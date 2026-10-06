#!/usr/bin/env python3
"""Reconstruct the sanitized EVAL-002 seed; never invokes a solving agent."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

REPO = Path(__file__).resolve().parent.parent


def run(*args, **kwargs):
    result = subprocess.run([str(a) for a in args], capture_output=True, timeout=180, **kwargs)
    if result.returncode:
        # Checkout stdout may contain fix-bearing commit messages. Keep it private.
        raise RuntimeError(f'Preparation command failed: {args[0]} (exit {result.returncode})')
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bugsinpy', type=Path, required=True, help='Local pinned BugsInPy dataset')
    args = parser.parse_args()
    config = json.loads((REPO/'evals/EVAL-002-config.json').read_text())
    dataset = args.bugsinpy.resolve()
    if run('git', '-C', dataset, 'rev-parse', 'HEAD').decode().strip() != config['benchmark_revision']:
        raise RuntimeError('BugsInPy revision differs from frozen configuration')
    spec = importlib.util.spec_from_file_location('harness', REPO/'evals/run-eval.py')
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    harness.configure('EVAL-002')
    # Existing verified seed is sufficient for resets; unexpected seeds are never removed.
    if harness.SEED.exists():
        harness.preflight()
        harness.check_only()
        return
    metadata = dataset/'projects/luigi/bugs/9'
    info = dict(line.split('=', 1) for line in (metadata/'bug.info').read_text().splitlines() if '=' in line)
    buggy = info['buggy_commit_id'].strip('"')
    fixed = info['fixed_commit_id'].strip('"')
    tests = info['test_file'].strip('"').split(';')
    if buggy != config['buggy_commit'] or set(tests) != set(config['transplanted_test_sha256']):
        raise RuntimeError('Dataset benchmark metadata changed')
    for name, expected in config['official_helper_sha256'].items():
        if hashlib.sha256((dataset/'framework/bin'/name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'Official helper changed: {name}')
    with tempfile.TemporaryDirectory(prefix='EVAL-002-preparation-') as temp:
        private = Path(temp)
        transport = private/'transport'
        run('git', 'init', '-q', transport)
        url = 'https://github.com/spotify/luigi.git'
        run('git', '-C', transport, 'fetch', '--no-tags', '--depth=1', url, buggy)
        run('git', '-C', transport, 'checkout', '-q', '--detach', 'FETCH_HEAD')
        run('git', '-C', transport, 'fetch', '--no-tags', '--depth=1', url, fixed)
        run('git', '-C', transport, 'update-ref', 'refs/heads/benchmark-tests', fixed)
        framework = private/'BugsInPy'
        (framework/'framework/bin').mkdir(parents=True)
        for name in config['official_helper_sha256']:
            shutil.copyfile(dataset/'framework/bin'/name, framework/'framework/bin'/name)
        project = framework/'projects/luigi'
        bug = project/'bugs/9'
        bug.mkdir(parents=True)
        (project/'project.info').write_text(f'github_url="{transport.as_uri()}"\nstatus="OK"\n')
        for name in ['bug.info', 'requirements.txt', 'run_test.sh', 'setup.sh']:
            if (metadata/name).exists():
                shutil.copyfile(metadata/name, bug/name)
        checkout = private/'checkout'
        checkout.mkdir()
        run('bash', framework/'framework/bin/bugsinpy-checkout', '-p', 'luigi', '-i', '9', '-v', '0', '-w', checkout)
        benchmark = checkout/'luigi'
        if run('git', '-C', benchmark, 'rev-parse', 'HEAD').decode().strip() != buggy:
            raise RuntimeError('Official checkout did not return the buggy revision')
        changed = set(run('git', '-C', benchmark, 'diff', '--name-only').decode().splitlines())
        if not changed <= set(tests):
            raise RuntimeError('Official checkout changed application source')
        snapshot = private/'snapshot'
        snapshot.mkdir()
        data = run('git', '-C', transport, 'archive', buggy)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive.getmembers():
                path = Path(member.name)
                if path.is_absolute() or '..' in path.parts:
                    raise RuntimeError('Unsafe snapshot archive')
                if member.issym():
                    target = (snapshot/path).parent / member.linkname
                    if not str(target.resolve()).startswith(str(snapshot.resolve()) + os.sep):
                        raise RuntimeError('Unsafe snapshot symlink')
            archive.extractall(snapshot)
        for name in tests:
            source = benchmark/name
            expected = run('git', '-C', transport, 'show', f'{fixed}:{name}')
            if source.read_bytes() != expected or hashlib.sha256(expected).hexdigest() != config['transplanted_test_sha256'][name]:
                raise RuntimeError('Transplanted test differs from frozen provenance')
            shutil.copyfile(source, snapshot/name)
        # Shared instructions contain only runtime/test commands, never selection notes.
        instructions = (REPO/'evals/EVAL-002-runtime/AGENTS.md').read_bytes()
        if hashlib.sha256(instructions).hexdigest() != config['support_files']['AGENTS.md']:
            raise RuntimeError('Runtime instructions changed')
        (snapshot/'AGENTS.md').write_bytes(instructions)
        run('git', 'init', '-q', '-b', 'main', snapshot)
        run('git', '-C', snapshot, '-c', 'core.autocrlf=false', 'add', '-f', '.')
        env = dict(os.environ, GIT_AUTHOR_DATE='2026-10-06T00:00:00Z', GIT_COMMITTER_DATE='2026-10-06T00:00:00Z')
        run('git', '-C', snapshot, '-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@example.invalid',
            'commit', '-qm', 'Frozen benchmark starting state', env=env)
        if run('git', '-C', snapshot, 'rev-parse', 'HEAD').decode().strip() != config['workspace_commit']:
            raise RuntimeError('Reconstructed snapshot commit differs from frozen state')
        if harness.object_inventory_hash(snapshot) != config['git_object_inventory_sha256']:
            raise RuntimeError('Unexpected snapshot Git objects')
        if subprocess.run(['git', '-C', str(snapshot), 'cat-file', '-e', fixed+'^{commit}'], capture_output=True).returncode == 0:
            raise RuntimeError('Fixed commit leaked into sanitized snapshot')
        harness.SEED.parent.mkdir(parents=True, exist_ok=True)
        run('git', 'clone', '--bare', '--no-local', snapshot, harness.SEED)
    # Temporary fixed-source access ends before any solving container is created.
    harness.check_only()


if __name__ == '__main__':
    main()
