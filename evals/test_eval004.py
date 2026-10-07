"""Three-condition orchestration tests. No Docker or model requests are made."""
import importlib.util
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
spec = importlib.util.spec_from_file_location('run_eval004', Path(__file__).with_name('run-eval.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def specs():
    result = {}
    for arm, version in [('B', None), ('V1','0.1'), ('V2','0.2')]:
        result[arm] = {'skill_version':version,
                       'skill_path':f'versions/v{version}/efficient-coding/SKILL.md' if version else None,
                       'skill_sha256':hashlib.sha256(version.encode()).hexdigest() if version else None,
                       'run_ids':[f'B{i}' if arm == 'B' else f'{arm}-{i}' for i in range(1,4)]}
    return result


ORDER = [r for i in range(1,4) for r in (f'B{i}',f'V1-{i}',f'V2-{i}')]


class ThreeConditionTests(unittest.TestCase):
    def test_mapping_and_condition_orders(self):
        with patch.multiple(h, EVAL_ID='EVAL-004', CONDITIONS=specs(), ORDER=ORDER):
            h.validate_conditions(h.CONDITIONS, ORDER)
            for i in range(1,4):
                for arm, run in [('B',f'B{i}'),('V1',f'V1-{i}'),('V2',f'V2-{i}')]:
                    self.assertEqual(h.condition_for_run(run), arm)
            self.assertEqual(h.planned_runs(all_runs=True), ORDER)
            self.assertEqual(h.planned_runs(condition='V1'), ['V1-1','V1-2','V1-3'])
            self.assertEqual(h.skill_instructions('B'), '')
            self.assertEqual(h.skill_instructions('V1'), 'Use the $efficient-coding Skill v0.1 for this task.')
            self.assertEqual(h.skill_instructions('V2'), h.skill_instructions('V1').replace('0.1','0.2'))
            with self.assertRaises(h.InfrastructureError): h.condition_for_run('S1')
            with self.assertRaises(h.InfrastructureError): h.safe_workspace(h.REPO/'experiments/EVAL-003-baseline')

    def test_invalid_design_is_rejected(self):
        bad = specs(); bad['B']['skill_path'] = 'SKILL.md'
        with self.assertRaises(h.InfrastructureError): h.validate_conditions(bad, ORDER)
        bad = specs(); bad['V1']['skill_path'] = 'versions/v0.2/efficient-coding/SKILL.md'
        with self.assertRaises(h.InfrastructureError): h.validate_conditions(bad, ORDER)
        with self.assertRaises(h.InfrastructureError): h.validate_conditions(specs(), list(reversed(ORDER)))

    def test_only_selected_skill_is_copied_and_only_own_workspace_is_mounted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); auth = root/'auth.json'; auth.write_text('{}')
            config = root/'config.json'; config.write_text(json.dumps({'environment':{}}))
            for arm, entry in specs().items():
                if entry['skill_path']:
                    path = root/entry['skill_path']; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(entry['skill_version'])
            for arm in specs():
                workspace = root/f'experiments/EVAL-004-{arm}'
                calls = []
                def command(args, **kwargs):
                    calls.append(args)
                    output = b''
                    if args[-2:] == ['codex','--version']: output = b'codex-cli 0.160.0\n'
                    if args[:2] == ['docker','inspect']:
                        output = json.dumps([{'Mounts':[{'Source':str(workspace)}]}]).encode()
                    if args[-2:] == ['cat','/root/.agents/skills/efficient-coding/SKILL.md']:
                        output = specs()[arm]['skill_version'].encode()
                    return subprocess.CompletedProcess(args,0,output,b'')
                with patch.multiple(h, REPO=root, EVAL_ID='EVAL-004', CONDITIONS=specs(), BENCHMARK_CONFIG=config), \
                     patch.object(h,'command',side_effect=command), patch.object(h,'remove_container'), \
                     patch.dict(os.environ,{'CODEX_HOME':str(root)}):
                    h.make_container('test-arm',workspace,arm)
                mounts = next(c for c in calls if c[:2] == ['docker','run'])
                self.assertEqual([mounts[i+1] for i,arg in enumerate(mounts) if arg == '-v'],[f'{workspace}:/workspace'])
                copies = [c for c in calls if c[:2] == ['docker','cp'] and str(c[2]) != str(auth)]
                self.assertEqual(len(copies),0 if arm == 'B' else 1)
                if copies: self.assertEqual(copies[0][2],root/specs()[arm]['skill_path'])
                self.assertTrue(any('test ! -e /root/.agents/skills && test ! -e /root/.codex/skills' in c for c in calls))

    def test_report_primary_comparison_missing_values_and_infrastructure_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); conditions=specs(); cfg={'model':'same'}
            for run, arm, tokens, infra in [('B1','B',100,None),('V1-1','V1',200,None),('V2-1','V2',150,None),('V2-2','V2',999,'synthetic failure')]:
                directory=root/run; directory.mkdir()
                row={'run_id':run,'condition':arm,'configuration':cfg,'skill_version':conditions[arm]['skill_version'],
                     'skill_sha256':conditions[arm]['skill_sha256'],'total_tokens':tokens,
                     'success':True if not infra else None,'infrastructure_failure':infra,'post_first_success_searches':None}
                (directory/'summary.json').write_text(json.dumps(row))
            with patch.multiple(h, EVAL_ID='EVAL-004', CONDITIONS=conditions, ORDER=ORDER, RESULTS=root, CONFIG=cfg), \
                 patch.object(h,'workspace_checkpoint') as checkpoint, patch.object(h,'verify_harness_inputs'):
                h.report()
            result=json.loads((root/'aggregate.json').read_text())
            self.assertEqual(result['primary_comparison'],'V1 -> V2')
            self.assertEqual(result['conditions']['V2']['runs'],1)
            self.assertEqual(result['conditions']['V2']['metrics']['total_tokens']['median'],150)
            self.assertEqual(result['comparisons'][0]['paired'][0]['percentage_changes']['total_tokens'],-25)
            self.assertIsNone(result['conditions']['V1']['metrics']['post_first_success_searches']['median'])
            self.assertEqual(checkpoint.call_args_list[0].args,('report-before',))
            self.assertEqual(checkpoint.call_args_list[-1].args,('report-after',))
            self.assertIn('N/D',(root/'report.md').read_text())

    def test_report_rejects_changed_condition_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'V1-1').mkdir()
            (root/'V1-1/summary.json').write_text(json.dumps({'run_id':'V1-1','condition':'V1','configuration':{},'skill_version':'0.2'}))
            with patch.multiple(h, EVAL_ID='EVAL-004', CONDITIONS=specs(), ORDER=ORDER, RESULTS=root, CONFIG={}), \
                 patch.object(h,'workspace_checkpoint'),patch.object(h,'verify_harness_inputs'):
                with self.assertRaises(h.InfrastructureError): h.report()

    def test_three_roots_reset_independently_and_keep_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; source.mkdir(); (root/'experiments').mkdir()
            subprocess.run(['git','init','-q',source],check=True)
            (source/'sample.py').write_text('original\n')
            subprocess.run(['git','-C',source,'add','.'],check=True)
            subprocess.run(['git','-C',source,'-c','user.name=test','-c','user.email=test@example.invalid','commit','-qm','neutral fixture'],check=True)
            commit=subprocess.check_output(['git','-C',source,'rev-parse','HEAD']).decode().strip()
            seed=root/'seed.git'; subprocess.run(['git','clone','--bare','--no-local',source,seed],check=True,capture_output=True)
            with patch.multiple(h, REPO=root, EVAL_ID='EVAL-004', CONDITIONS=specs(), ORDER=ORDER,
                                RESULTS=root/'results', SEED=seed, COMMIT=commit, BENCHMARK_CONFIG=None,
                                SUPPORT_FILES={}, TEST_HASHES={}, OBJECT_INVENTORY_HASH=None):
                h.prepare_workspaces()
                starts=h.workspace_checkpoint('synthetic-start')
                self.assertEqual(len({v['fingerprint']['sha256'] for v in starts.values()}),1)
                identities={arm:h.identity(h.workspace_for(arm)) for arm in h.conditions()}
                baseline=h.workspace_for('B'); (baseline/'sample.py').write_text('candidate\n')
                with self.assertRaises(h.InfrastructureError): h.workspace_checkpoint('contaminated')
                for arm in ('V1','V2'):
                    self.assertEqual((h.workspace_for(arm)/'sample.py').read_text(),'original\n')
                h.reset_workspace(baseline,captured=True)
                restored=h.workspace_checkpoint('synthetic-restored')
                for arm in h.conditions():
                    self.assertEqual(h.identity(h.workspace_for(arm)),identities[arm])
                    self.assertEqual(restored[arm]['fingerprint'],starts[arm]['fingerprint'])
                removed=h.workspace_for('V1'); removed.rename(root/'retained-missing-root')
                with self.assertRaises(h.InfrastructureError): h.workspace_checkpoint('missing')
                self.assertFalse(removed.exists())

    def test_frozen_eval003_cannot_reset_or_reprocess(self):
        for action in ['B1','--all','--reanalyze','--check','--prepare']:
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('run-eval.py')),'--eval','EVAL-003',action],capture_output=True)
            self.assertEqual(result.returncode,2)
            self.assertIn(b'EVAL-003 is frozen',result.stderr)


if __name__ == '__main__':
    unittest.main()
