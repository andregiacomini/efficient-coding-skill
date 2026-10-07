#!/usr/bin/env python3
"""Reconstruct EVAL-003 from its base revision and test-only patch; no agent call."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

REPO = Path(__file__).resolve().parent.parent
PREPARATION = REPO/'evals/preparation/EVAL-003'


def run(*args, **kwargs):
    if str(args[0]) == 'git':
        args = ('git', '--no-optional-locks', '-c', 'gc.auto=0',
                '-c', 'maintenance.auto=false', '-c', 'gc.autoDetach=false', *args[1:])
    result = subprocess.run([str(a) for a in args], capture_output=True, timeout=180, **kwargs)
    if result.returncode:
        raise RuntimeError(f'Preparation command failed: {args[0]} (exit {result.returncode})')
    return result.stdout


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_snapshot(private, metadata, source_repository=None):
    """Only the base revision is fetched. Gold/fixed source is never obtained."""
    if source_repository is None:
        source_repository = private/'base-only-transport'
        run('git', 'init', '-q', source_repository)
        run('git', '-C', source_repository, 'fetch', '--no-tags', '--depth=1',
            'https://github.com/django/django.git', metadata['base_commit'])
        run('git', '-C', source_repository, 'checkout', '-q', '--detach', 'FETCH_HEAD')
    if run('git', '-C', source_repository, 'rev-parse', 'HEAD').decode().strip() != metadata['base_commit']:
        raise RuntimeError('Transport is not the declared base revision')
    snapshot = private/'snapshot'
    snapshot.mkdir()
    data = run('git', '-C', source_repository, 'archive', metadata['base_commit'])
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or member.islnk():
                raise RuntimeError('Unsafe source archive member')
            if member.issym():
                target = (snapshot/path).parent/member.linkname
                if not str(target.resolve()).startswith(str(snapshot.resolve()) + os.sep):
                    raise RuntimeError('Unsafe source symlink')
        archive.extractall(snapshot)
    production = {str(p.relative_to(snapshot)): sha(p) for p in snapshot.rglob('*')
                  if p.is_file() and not p.is_symlink() and not str(p.relative_to(snapshot)).startswith('tests/')}
    patch = PREPARATION/'test.patch'
    import re
    paths = re.findall(r'^diff --git a/(.*?) b/([^\n]+)', patch.read_text(), re.M)
    if not paths or any(not x.startswith('tests/') or '..' in Path(x).parts for pair in paths for x in pair):
        raise RuntimeError('Benchmark patch is not restricted to tests')
    run('git', 'apply', patch, cwd=snapshot)
    current_production = {str(p.relative_to(snapshot)): sha(p) for p in snapshot.rglob('*')
                          if p.is_file() and not p.is_symlink() and not str(p.relative_to(snapshot)).startswith('tests/')}
    if current_production != production:
        raise RuntimeError('Benchmark test transplantation changed application source')
    (snapshot/'AGENTS.md').write_bytes((REPO/'evals/EVAL-003-runtime/AGENTS.md').read_bytes())
    run('git', 'init', '-q', '-b', 'main', snapshot)
    run('git', '-C', snapshot, '-c', 'core.autocrlf=false', 'add', '-f', '.')
    env = dict(os.environ, GIT_AUTHOR_DATE='2026-10-06T00:00:00Z', GIT_COMMITTER_DATE='2026-10-06T00:00:00Z')
    run('git', '-C', snapshot, '-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@example.invalid',
        'commit', '-qm', 'Frozen benchmark starting state', env=env)
    return snapshot


def main():
    metadata = json.loads((PREPARATION/'task-metadata.json').read_text())
    config = json.loads((REPO/'evals/EVAL-003-config.json').read_text())
    for name, expected in config['harness_input_sha256'].items():
        if sha(REPO/name) != expected:
            raise RuntimeError(f'Frozen input changed: {name}')
    sys.path.insert(0, str(REPO/'evals'))
    spec = importlib.util.spec_from_file_location('harness', REPO/'evals/run-eval.py')
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    harness.configure('EVAL-003')
    if not harness.SEED.exists():
        private = Path(tempfile.mkdtemp(prefix='EVAL-003-preparation-'))
        try:
            snapshot = build_snapshot(private, metadata)
            if run('git', '-C', snapshot, 'rev-parse', 'HEAD').decode().strip() != config['workspace_commit']:
                raise RuntimeError('Reconstructed sanitized commit differs from frozen state')
            if harness.object_inventory_hash(snapshot) != config['git_object_inventory_sha256']:
                raise RuntimeError('Reconstructed Git objects differ from frozen inventory')
            if run('git', '-C', snapshot, 'rev-list', '--count', '--all').decode().strip() != '1':
                raise RuntimeError('Unexpected history in sanitized snapshot')
            harness.SEED.parent.mkdir(parents=True, exist_ok=True)
            harness.lifecycle_log('create-seed', harness.SEED, 'explicit experiment preparation')
            run('git', 'clone', '--bare', '--no-local', snapshot, harness.SEED)
        finally:
            harness.lifecycle_log('remove-private-preparation-directory', private,
                                  'discard base-only transport/snapshot; never an experiment workspace')
            shutil.rmtree(private)
    harness.preflight(prepare=True)
    harness.prepare_workspaces()
    harness.check_only()
    print('EVAL-003 prepared. No coding-agent run or model request was made.')


if __name__ == '__main__':
    main()
