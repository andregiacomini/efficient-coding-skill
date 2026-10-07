#!/usr/bin/env python3
"""Reuse the sanitized EVAL-003 seed; prepare/check three arms, never run an agent."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
spec = importlib.util.spec_from_file_location('run_eval', Path(__file__).with_name('run-eval.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed-path', type=Path, help='Existing exact sanitized bare seed; defaults to EVAL-003 seed')
    args = parser.parse_args()
    h.configure('EVAL-004')
    config = json.loads(h.BENCHMARK_CONFIG.read_text())
    source = (args.seed_path or h.REPO/'experiments/.EVAL-003-seed.git').resolve()
    h.RESULTS.mkdir(parents=True, exist_ok=True)
    lock = h.RESULTS/'.runner.lock'
    import os
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode())
        if not h.SEED.exists():
            h.verify_harness_inputs()
            if source == h.SEED or source.is_symlink() or not source.is_dir():
                raise h.InfrastructureError('Supply the existing sanitized bare seed')
            if h.command(['git','--git-dir',source,'rev-list','--all']).stdout.decode().splitlines() != [h.COMMIT]:
                raise h.InfrastructureError('Source seed is not the one-commit sanitized snapshot')
            if h.object_inventory_hash(source, bare=True) != h.OBJECT_INVENTORY_HASH:
                raise h.InfrastructureError('Source seed contains unexpected objects')
            h.lifecycle_log('create-seed', h.SEED, 'independent clone of existing sanitized EVAL-003 seed')
            h.command(['git','clone','--bare','--no-local',source,h.SEED])
            h.command(['git','--git-dir',h.SEED,'remote','remove','origin'])
            h.command(['git','--git-dir',h.SEED,'config','gc.auto','0'])
            h.command(['git','--git-dir',h.SEED,'config','maintenance.auto','false'])
        archive = h.command(['git','--git-dir',h.SEED,'archive','--format=tar',h.COMMIT]).stdout
        if hashlib.sha256(archive).hexdigest() != config['sanitized_archive_sha256']:
            raise h.InfrastructureError('EVAL-004 does not match the frozen EVAL-003 repository archive')
        h.preflight(prepare=True)
        h.prepare_workspaces()
        h.check_only()
        h.report()
        fingerprints = json.loads((h.REPO/'evals/preparation/EVAL-004/workspace-fingerprints.json').read_text())
        manifest_path = h.RESULTS/'manifest.json'
        if not manifest_path.exists():
            inputs = [h.BENCHMARK_CONFIG, h.PROMPT, h.REPO/'versions/manifest.json']
            inputs += [h.REPO/name for name in config['harness_input_sha256']]
            inputs += [h.REPO/s['skill_path'] for s in h.CONDITIONS.values() if s['skill_path']]
            outputs = list((h.REPO/'evals/preparation/EVAL-004').glob('*'))
            manifest = {
                'eval_id':'EVAL-004', 'status':'PREPARED',
                'prepared_at':datetime.now(timezone.utc).isoformat(),
                'task_id':config['task_id'], 'reuses_frozen_eval':'eval-003',
                'eval_003_freeze_commit':config['eval_003_freeze_commit'],
                'workspace_commit':h.COMMIT, 'sanitized_archive_sha256':config['sanitized_archive_sha256'],
                'workspace_fingerprint':next(iter(fingerprints.values()))['sha256'],
                'workspace_fingerprints':fingerprints,
                'workspace_registration':json.loads(h.registration_path().read_text()),
                'configuration':h.CONFIG, 'conditions':h.CONDITIONS,
                'runner_image':h.IMAGE, 'python_version':config['python_version'],
                'test_command':h.TEST_COMMAND, 'expected_test_count':113,
                'initial_result':{'passing_tests':109,'expected_errors':4,'skipped_tests':0,'failure':h.EXPECTED_FAILURE},
                'instrumentation_schema_version':4, 'instrumentation_revision':'4.1',
                'trace_parser_unchanged_from_eval_003':h.digest(h.REPO/'evals/trace_analysis.py')==config['harness_input_sha256']['evals/trace_analysis.py'],
                'primary_comparison':'V1 -> V2', 'run_order':h.ORDER,
                'primary_metrics':config['primary_metrics'],
                'first_success_definition':config['first_success_definition'],
                'solver_mounts':'One own workspace; one condition Skill copied outside the repository, or none; no evaluator files, sibling repositories, traces or patches.',
                'agent_runs':[], 'model_requests_during_preparation':0, 'result':None,
                'input_sha256':{str(p.relative_to(h.REPO)):h.digest(p) for p in inputs},
                'preparation_output_sha256':{str(p.relative_to(h.REPO)):h.digest(p) for p in outputs if p.is_file()},
                'limitations':[
                    'Local strict 113-test adapter, not full official SWE-bench Docker harness.',
                    'No statistical significance claim from three repetitions per condition.',
                    'Network is not air-gapped; known-solution access is prohibited; web search is disabled.',
                    'Lifecycle checkpoints detect state changes, not every transient external interference.',
                    'Post-success work is measured, not automatically classified as unnecessary.',
                    'Cross-evaluation full fingerprints differ because they also hash evaluator configuration; repository archives are identical.',
                ]}
            h.save_json(manifest_path, manifest)
        if any((h.RESULTS/run).exists() for run in h.ORDER):
            raise h.InfrastructureError('Preparation must not contain any solving-agent run directories')
        h.workspace_checkpoint('preparation-complete-no-agent-runs')
        print('EVAL-004 PREPARED. No solving-agent session or model request executed.')
        return 0
    finally:
        os.close(descriptor)
        lock.unlink()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt) as error:
        print(f'Preparation failed; preserve state for review: {error}', file=sys.stderr)
        sys.exit(1)
