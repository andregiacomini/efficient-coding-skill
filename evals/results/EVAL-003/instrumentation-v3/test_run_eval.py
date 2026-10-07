"""Synthetic harness tests: no benchmark source or real Codex inference is used."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import unittest
from unittest.mock import patch
from contextlib import contextmanager

spec = importlib.util.spec_from_file_location('run_eval', Path(__file__).with_name('run-eval.py'))
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class TraceTests(unittest.TestCase):
    def parse(self, events):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'trace.jsonl'
            path.write_text('\n'.join(json.dumps(e) for e in events))
            return harness.parse_trace(path)

    def test_deduplicates_items_and_preserves_missing_metrics(self):
        item = {'id': 'cmd1', 'type': 'command_execution', 'command': 'a compound command'}
        metrics, detail = self.parse([
            {'type': 'item.started', 'item': item},
            {'type': 'item.completed', 'item': item},
            {'type': 'turn.completed', 'usage': {'input_tokens': 10, 'cached_input_tokens': 7, 'output_tokens': 4}},
        ])
        self.assertEqual(metrics['tool_calls'], 1)
        self.assertEqual(metrics['shell_commands'], 1)
        self.assertEqual(metrics['total_tokens'], 14)
        self.assertIsNone(metrics['files_inspected'])
        self.assertIsNone(metrics['test_runs'])
        self.assertTrue(detail['trace_completed'])

    def test_unknown_tool_schema_does_not_invent_count(self):
        metrics, _ = self.parse([
            {'type': 'item.completed', 'item': {'id': 'new1', 'type': 'new_unknown_tool'}},
            {'type': 'turn.completed', 'usage': {'input_tokens': 10}},
        ])
        self.assertIsNone(metrics['tool_calls'])
        self.assertIsNone(metrics['total_tokens'])
        self.assertEqual(metrics['input_tokens'], 10)

    def test_null_usage_remains_unknown(self):
        metrics, detail = self.parse([{'type': 'turn.completed', 'usage': None}])
        self.assertTrue(detail['trace_completed'])
        self.assertIsNone(metrics['input_tokens'])
        self.assertIsNone(metrics['total_tokens'])

    def test_incomplete_trace_does_not_claim_zero_usage(self):
        metrics, detail = self.parse([{'type': 'error', 'message': 'unsupported model'}])
        self.assertFalse(detail['trace_completed'])
        self.assertTrue(all(metrics[k] is None for k in ('input_tokens', 'output_tokens', 'total_tokens', 'tool_calls', 'shell_commands', 'test_runs')))


class LifecycleTests(unittest.TestCase):
    def exercise(self, rejected=False, capture_failed=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / 'experiments/EVAL-001-baseline'
            source = root / 'seed-source'
            source.mkdir()
            subprocess.run(['git', 'init', source], check=True, capture_output=True)
            (source / 'sample.txt').write_text('original\n')
            subprocess.run(['git', '-C', source, 'add', '.'], check=True)
            subprocess.run(['git', '-C', source, '-c', 'user.name=test', '-c', 'user.email=test@example.invalid',
                            'commit', '-m', 'synthetic fixture'], check=True, capture_output=True)
            commit = subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD']).decode().strip()
            seed = root / 'seed.git'
            subprocess.run(['git', 'clone', '--bare', '--no-local', source, seed], check=True, capture_output=True)
            workspace.parent.mkdir()
            prompt = root / 'task.md'
            prompt.write_text('synthetic task only\n')
            original_run = subprocess.run
            observed_input = []
            original_capture = harness.capture

            def capture_artifacts(*args):
                if capture_failed:
                    raise OSError('simulated artifact storage failure')
                return original_capture(*args)

            def fake_run(args, **kwargs):
                if args[0] != 'docker':
                    return original_run(args, **kwargs)
                self.assertIn('exec', args)
                self.assertIn('--json', args)
                self.assertNotIn('resume', args)
                observed_input.append(kwargs['input'])
                (workspace / 'sample.txt').write_text('changed\n')
                (workspace / 'new.txt').write_text('new artifact\n')
                events = ([{'type': 'error', 'message': 'unsupported model'}] if rejected else
                          [{'type': 'turn.completed', 'usage': {'input_tokens': 8, 'output_tokens': 2}}])
                kwargs['stdout'].write(('\n'.join(json.dumps(e) for e in events) + '\n').encode())
                return subprocess.CompletedProcess(args, 1 if rejected else 0)

            with patch.multiple(harness, REPO=root, RESULTS=root/'results', SEED=seed, COMMIT=commit, PROMPT=prompt), \
                 patch.object(harness, 'preflight'), patch.object(harness, 'remove_container'), \
                 patch.object(harness, 'make_container'), \
                 patch.object(harness, 'capture', side_effect=capture_artifacts), \
                 patch.object(harness, 'benchmark', side_effect=[
                     (False, 'Expect a list of length 7, but got a list of length 6', 1),
                     (True, 'Ran 1 test\nOK\n', 0)]), \
                 patch.object(harness, 'run_agent', side_effect=fake_run):
                harness.prepare_workspaces()
                root_inode = workspace.stat().st_ino
                outcome = harness.run_one('B1')
                self.assertEqual(workspace.stat().st_ino, root_inode)
                directory = harness.RESULTS/'B1'
                summary = json.loads((directory/'summary.json').read_text())
                self.assertEqual(outcome, not (rejected or capture_failed))
                if capture_failed:
                    self.assertIn('Artifact capture failed', summary['infrastructure_failure'])
                    self.assertEqual((workspace/'sample.txt').read_text(), 'changed\n')
                    self.assertTrue((workspace/'new.txt').exists())
                    return
                self.assertEqual(summary['files_modified'], 2)
                self.assertEqual(observed_input, [prompt.read_bytes()])
                self.assertIn('+changed', (directory/'patch.diff').read_text())
                self.assertTrue((directory/'untracked.tar').is_file())
                self.assertEqual((workspace/'sample.txt').read_text(), 'original\n')
                self.assertFalse((workspace/'new.txt').exists())
                self.assertEqual(harness.git(workspace, 'status', '--short'), b'')
                self.assertEqual(summary['success'], None if rejected else True)
                report = (harness.RESULTS/'report.md').read_text()
                self.assertIn('| Runs | 0 | 0 |' if rejected else '| Runs | 1 | 0 |', report)
                # Completed artifacts are never silently overwritten.
                with self.assertRaises(harness.InfrastructureError):
                    harness.run_one('B1')

    def test_artifacts_saved_before_full_reset(self):
        self.exercise()

    def test_failed_capture_preserves_workspace(self):
        self.exercise(capture_failed=True)

    def test_infrastructure_rejection_saved_and_excluded_from_report(self):
        self.exercise(rejected=True)


class ClassificationTests(unittest.TestCase):
    def actions(self, command):
        from trace_analysis import analyze_actions
        return analyze_actions([(1, {'id': 'cmd', 'type': 'command_execution', 'command': command, 'exit_code': 0})])

    def test_search_and_test_file_inspection_are_not_tests(self):
        metrics, detail = self.actions("/bin/bash -lc \"cat test/test_a.py; rg -n 'pytest|unittest' src | head -65; rg --files -g '*test*'\"")
        self.assertEqual(metrics['repository_search_commands'], 2)
        self.assertEqual(metrics['test_runs'], 0)
        self.assertEqual(metrics['total_file_reads'], 1)
        self.assertEqual(metrics['unique_files_inspected'], 1)

    def test_distinct_read_operations_normalize_paths(self):
        metrics, detail = self.actions("cat a.py ./a.py; sed -n '10,20p' /workspace/a.py")
        self.assertEqual(metrics['total_file_reads'], 3)
        self.assertEqual(metrics['unique_files_inspected'], 1)
        self.assertEqual(metrics['repeated_file_reads'], 2)
        self.assertEqual(detail['file_reads'][-1]['range'], [10,20])

    def test_skill_read_is_separate_from_repository(self):
        metrics, detail = self.actions('cat /root/.agents/skills/efficient-coding/SKILL.md; cat AGENTS.md')
        self.assertEqual(metrics['skill_loading_events'], 1)
        self.assertEqual(metrics['repository_file_reads'], 1)
        self.assertEqual(metrics['total_file_reads'], 2)
        self.assertEqual(metrics['tool_items_excluding_skill_loading'], 1)

    def test_dynamic_or_conditional_execution_is_unknown(self):
        metrics, detail = self.actions('false && pytest; cat "$FILE"')
        self.assertIsNone(metrics['test_runs'])
        self.assertEqual(metrics['total_file_reads'], 0)
        self.assertFalse(metrics['command_classification_complete'])

    def test_filename_mentions_in_agent_text_are_not_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'codex.jsonl'
            path.write_text(json.dumps({'type':'item.completed','item':{'id':'msg','type':'agent_message','text':'cat other.py; pytest'}})+'\n'+json.dumps({'type':'turn.completed','usage':None})+'\n')
            metrics, details=harness.parse_trace(path)
            self.assertEqual(metrics['total_file_reads'],0)
            self.assertEqual(metrics['test_commands'],0)

    def test_convergence_metrics_use_observable_order_and_source_roots(self):
        from trace_analysis import analyze_actions
        commands = ['cat /root/.agents/skills/efficient-coding/SKILL.md',
                    'rg -n symbol src', 'cat src/a.py test/test_a.py',
                    'cat src/a.py src/b.py']
        items = [(i, {'id': str(i), 'type': 'command_execution', 'command': c})
                 for i, c in enumerate(commands, 1)]
        items.append((5, {'id': 'edit', 'type': 'file_change', 'changes': [{'path': 'src/a.py'}]}))
        metrics, detail = analyze_actions(items, {i: i / 10 for i in range(1, 6)}, source_roots=['src'])
        self.assertEqual(metrics['time_until_first_repository_search_seconds'], 0.2)
        self.assertEqual(metrics['time_until_first_file_read_seconds'], 0.1)
        self.assertEqual(metrics['time_until_first_repository_file_read_seconds'], 0.3)
        self.assertEqual(metrics['time_until_first_edit_seconds'], 0.5)
        self.assertEqual(metrics['unique_source_files_before_first_edit'], 2)
        self.assertEqual(metrics['searches_before_first_edit'], 1)
        self.assertEqual(metrics['tool_items_before_first_edit'], 4)
        self.assertIsNone(metrics['time_until_first_test_seconds'])


class WorkspaceIntegrityTests(unittest.TestCase):
    def test_fingerprints_match_and_unexpected_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed_source = root / 'source'
            seed_source.mkdir()
            subprocess.run(['git', 'init', '-q', seed_source], check=True)
            (seed_source/'sample.py').write_text('original\n')
            (seed_source/'.gitignore').write_text('*.ignored\n')
            (seed_source/'AGENTS.md').write_text('runtime information only\n')
            subprocess.run(['git', '-C', seed_source, 'add', '.'], check=True)
            subprocess.run(['git', '-C', seed_source, '-c', 'user.name=test',
                            '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'buggy fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', seed_source, 'rev-parse', 'HEAD']).decode().strip()
            seed = root/'seed.git'
            subprocess.run(['git', 'clone', '--bare', '--no-local', seed_source, seed], check=True, capture_output=True)
            (root/'experiments').mkdir()
            with patch.multiple(harness, REPO=root, EVAL_ID='EVAL-002', RESULTS=root/'results', SEED=seed, COMMIT=commit,
                                SUPPORT_FILES={'AGENTS.md':harness.digest(seed_source/'AGENTS.md')}):
                baseline, skill = harness.workspace_for('baseline'), harness.workspace_for('skill')
                harness.prepare_workspaces()
                self.assertEqual(harness.workspace_fingerprint(baseline), harness.workspace_fingerprint(skill))
                for name in ['duplicate 2.py', 'artifact.ignored']:
                    (baseline/name).write_text('preserve evidence\n')
                    with self.assertRaises(harness.InfrastructureError):
                        harness.reset_workspace(baseline)
                    self.assertTrue((baseline/name).exists())
                    with self.assertRaises(harness.InfrastructureError):
                        harness.verify_clean(baseline)
                    (baseline/name).unlink()
                (baseline/'AGENTS.md').write_text('contaminated\n')
                with self.assertRaises(harness.InfrastructureError):
                    harness.workspace_fingerprint(baseline)
                harness.reset_workspace(baseline)
                self.assertEqual(harness.workspace_fingerprint(baseline), harness.workspace_fingerprint(skill))
                with patch.object(harness, 'OBJECT_INVENTORY_HASH', harness.object_inventory_hash(baseline)):
                    harness.verify_clean(baseline)
                    subprocess.run(['git', '-C', baseline, 'hash-object', '-w', '--stdin'],
                                   input=b'synthetic unexpected Git object', capture_output=True, check=True)
                    self.assertEqual(harness.git(baseline, 'status', '--short'), b'')
                    with self.assertRaises(harness.InfrastructureError):
                        harness.verify_clean(baseline)

    def test_frozen_eval_rejects_agent_runs_and_reanalysis(self):
        for arguments in [['B1'], ['--all'], ['--reanalyze'], ['--check'], ['--prepare']]:
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('run-eval.py')),
                                     '--eval', 'EVAL-001', *arguments], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b'EVAL-001 is frozen', result.stderr)


class PytestGradingTests(unittest.TestCase):
    def grade(self, output, code):
        with patch.multiple(harness, RESULT_MODE='pytest', EXPECTED_TEST_COUNT=1), \
             patch.object(harness, 'make_container'), patch.object(harness, 'remove_container'), \
             patch.object(harness, 'command', return_value=subprocess.CompletedProcess([], code, output.encode(), b'')):
            return harness.benchmark(Path('/synthetic'), 'synthetic-only')

    def test_application_error_log_is_a_real_test_failure(self):
        self.assertFalse(self.grade('ERROR    app: expected negative path\n1 failed, 23 warnings in 0.20s\n', 1)[0])

    def test_setup_errors_are_not_bug_reproduction(self):
        with self.assertRaises(harness.InfrastructureError):
            self.grade('1 failed, 1 error in 0.20s\n', 1)

    def test_success_requires_frozen_test_count(self):
        self.assertTrue(self.grade('1 passed in 0.20s\n', 0)[0])
        with self.assertRaises(harness.InfrastructureError):
            self.grade('11 passed in 0.20s\n', 0)

    def test_timing_capture_preserves_raw_stream(self):
        import sys, time
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            raw=b'{"type":"turn.started"}\n{"type":"turn.completed","usage":null}\n'
            with (root/'codex.jsonl').open('wb') as stdout, (root/'stderr.txt').open('wb') as stderr:
                result=harness.run_agent([sys.executable,'-c','import sys; sys.stdout.buffer.write('+repr(raw)+')'],input=b'',stdout=stdout,stderr=stderr,timeout=5,timing_path=root/'event-timing.jsonl',started=time.monotonic())
            self.assertEqual(result.returncode,0)
            self.assertEqual((root/'codex.jsonl').read_bytes(),raw)
            records=[json.loads(line) for line in (root/'event-timing.jsonl').read_text().splitlines()]
            self.assertEqual([r['line_number'] for r in records],[1,2])
            self.assertGreaterEqual(records[1]['elapsed_seconds'],records[0]['elapsed_seconds'])

    def test_django_verbose_parser_retains_multiline_test_ids(self):
        output = ('test_a (app.tests.Case) ... ok\n'
                  'test_b (app.tests.Case)\nDescription of the externally observed behavior. ... ERROR\n')
        self.assertEqual(harness.django_test_results(output),
                         {'app.tests.Case.test_a': 'ok', 'app.tests.Case.test_b': 'ERROR'})

    def test_django_success_rejects_skipped_or_missing_required_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp)/'config.json'
            config.write_text(json.dumps({'required_test_ids': ['app.tests.Case.test_a']}))
            with patch.multiple(harness, RESULT_MODE='django_unittest', EXPECTED_TEST_COUNT=1,
                                BENCHMARK_CONFIG=config), \
                 patch.object(harness, 'make_container'), patch.object(harness, 'remove_container'):
                for output, code in [('test_a (app.tests.Case) ... skipped reason\nRan 1 test in 0.1s\nOK\n', 0),
                                     ('test_other (app.tests.Case) ... ok\nRan 1 test in 0.1s\nOK\n', 0)]:
                    with patch.object(harness, 'command', return_value=subprocess.CompletedProcess([], code, output.encode(), b'')):
                        with self.assertRaises(harness.InfrastructureError):
                            harness.benchmark(Path('/synthetic'), 'synthetic-only')

    def test_initial_django_failure_rejects_additional_environment_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp)/'config.json'
            config.write_text(json.dumps({'official_FAIL_TO_PASS': ['test_a (app.tests.Case)']}))
            with patch.multiple(harness, RESULT_MODE='django_unittest', BENCHMARK_CONFIG=config):
                expected = 'test_a (app.tests.Case) ... ERROR\ntest_b (app.tests.Case) ... ok\n'
                harness.verify_initial_failure(expected)
                with self.assertRaises(harness.InfrastructureError):
                    harness.verify_initial_failure(expected.replace(' ... ok', ' ... ERROR'))


class PersistentWorkspaceTests(unittest.TestCase):
    @contextmanager
    def prepared(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source'
            source.mkdir()
            subprocess.run(['git', 'init', '-q', source], check=True)
            (source / 'sample.py').write_text('original\n')
            subprocess.run(['git', '-C', source, 'add', '.'], check=True)
            subprocess.run(['git', '-C', source, '-c', 'user.name=test',
                            '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD']).decode().strip()
            seed = root / 'seed.git'
            subprocess.run(['git', 'clone', '--bare', '--no-local', source, seed], check=True, capture_output=True)
            (root / 'experiments').mkdir()
            with patch.multiple(harness, REPO=root, EVAL_ID='EVAL-003', RESULTS=root/'results',
                                SEED=seed, COMMIT=commit, SUPPORT_FILES={}, TEST_HASHES={},
                                OBJECT_INVENTORY_HASH=None, BENCHMARK_CONFIG=None):
                harness.prepare_workspaces()
                yield root, harness.workspace_for('baseline'), harness.workspace_for('skill')

    def test_reset_keeps_root_inode_and_removes_captured_history(self):
        with self.prepared() as (root, baseline, skill):
            before = harness.identity(baseline)
            (baseline/'sample.py').write_text('edited\n')
            (baseline/'untracked').mkdir()
            (baseline/'untracked/artifact').write_text('captured evidence\n')
            subprocess.run(['git', '-C', baseline, 'hash-object', '-w', '--stdin'],
                           input=b'unexpected future object', check=True, capture_output=True)
            harness.reset_workspace(baseline, captured=True)
            self.assertEqual(before, harness.identity(baseline))
            self.assertEqual((baseline/'sample.py').read_text(), 'original\n')
            self.assertEqual(harness.object_inventory_hash(baseline), harness.object_inventory_hash(harness.SEED, bare=True))
            self.assertFalse((baseline/'untracked').exists())
            logs = [json.loads(x) for x in (root/'results/lifecycle.jsonl').read_text().splitlines()]
            removals = [x for x in logs if x['operation'].startswith('remove-')]
            self.assertTrue(removals)
            self.assertTrue(all(x['timestamp'] and x['target_path'] and x['reason'] for x in removals))
            self.assertTrue(all(x['target_path'] != str(baseline) for x in removals))

    def test_missing_root_is_not_silently_recreated(self):
        with self.prepared() as (root, baseline, skill):
            baseline.rename(root/'missing-evidence')
            with self.assertRaisesRegex(harness.InfrastructureError, 'disappeared'):
                harness.reset_workspace(baseline)
            with self.assertRaisesRegex(harness.InfrastructureError, 'integrity failure'):
                harness.report()
            self.assertFalse(baseline.exists())

    def test_replaced_root_identity_is_rejected_even_with_identical_contents(self):
        import shutil
        with self.prepared() as (root, baseline, skill):
            moved = root/'original-root'
            baseline.rename(moved)
            shutil.copytree(moved, baseline)
            with self.assertRaisesRegex(harness.InfrastructureError, 'identity changed'):
                harness.workspace_checkpoint('synthetic replacement')

    def test_report_is_read_only_for_both_workspaces(self):
        with self.prepared() as (root, baseline, skill):
            def snapshot():
                return {str(p): (p.stat().st_ino, p.stat().st_mtime_ns, harness.digest(p))
                        for w in (baseline, skill) for p in w.rglob('*') if p.is_file()}
            import os
            os.utime(baseline/'sample.py', ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))
            before = snapshot()
            with patch.object(harness, 'reset_workspace', side_effect=AssertionError('report reset')):
                harness.report()
            self.assertEqual(before, snapshot())

    def test_report_detects_disappearance_after_output_write(self):
        with self.prepared() as (root, baseline, skill):
            original_save = harness.save
            def interrupted_save(path, data):
                original_save(path, data)
                if path.name == 'report.md':
                    baseline.rename(root/'external-removal-evidence')
            with patch.object(harness, 'save', side_effect=interrupted_save):
                with self.assertRaisesRegex(harness.InfrastructureError, 'integrity failure'):
                    harness.report()
            self.assertFalse(baseline.exists())

    def test_report_detects_external_content_change_without_repair(self):
        with self.prepared() as (root, baseline, skill):
            original_save = harness.save
            def interrupted_save(path, data):
                original_save(path, data)
                if path.name == 'report.md':
                    (skill/'sample.py').write_text('unexpected external change\n')
            with patch.object(harness, 'save', side_effect=interrupted_save):
                with self.assertRaisesRegex(harness.InfrastructureError, 'integrity failure'):
                    harness.report()
            self.assertEqual((skill/'sample.py').read_text(), 'unexpected external change\n')

    def test_reset_staging_failure_leaves_prepared_root_intact(self):
        with self.prepared() as (root, baseline, skill):
            before = harness.identity(baseline)
            with patch.object(harness, 'command', side_effect=harness.InfrastructureError('clone failed')):
                with self.assertRaisesRegex(harness.InfrastructureError, 'clone failed'):
                    harness.reset_workspace(baseline, captured=True)
            self.assertEqual(harness.identity(baseline), before)
            self.assertEqual((baseline/'sample.py').read_text(), 'original\n')

    def test_frozen_eval_002_cli_cannot_rewrite_or_reset(self):
        for action in ['B1', '--all', '--reanalyze', '--check', '--prepare']:
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('run-eval.py')),
                                     '--eval', 'EVAL-002', action], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b'EVAL-002 is frozen', result.stderr)


if __name__ == '__main__':
    unittest.main()
