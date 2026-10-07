#!/usr/bin/env python3
"""Shared evaluation harness. --check never starts a coding agent. Standard library only."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tarfile
import time
import threading
import tempfile
from trace_analysis import analyze_actions
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / 'evals/results/EVAL-001'
SEED = REPO / 'experiments/.EVAL-001-seed.git'
FIXTURES = REPO / 'experiments/.EVAL-001-fixtures'
COMMIT = '735bffc07ddef89128de379913b6d5dfc67f9789'
IMAGE = 'sha256:9c4211b7d47308c04df8a441127ef77894efc3ff71a1e2bf692d1796864ac1a9'
PROMPT = REPO / 'evals/EVAL-001-task.md'
SKILL = REPO / 'SKILL.md'
ORDER = ['B1', 'S1', 'B2', 'S2', 'B3', 'S3']
TEST = 'test.test_InfoExtractor.TestInfoExtractor.test_parse_mpd_formats'
TEST_COMMAND = ['/opt/eval-venv/bin/python', '-m', 'unittest', '-q', TEST]
CONFIG = {
    'codex_version': 'codex-cli 0.160.0', 'model': 'gpt-6.1-sol',
    'reasoning_effort': 'medium', 'sandbox': 'danger-full-access',
    'approval_policy': 'never', 'web_search': 'disabled', 'skill_version': '0.1',
    'prompt_sha256': 'de96b2e6a7b5fe6ad572c966276f49d26711f05b44527e9de8547e45bbe8c2d1',
    'skill_sha256': 'f149e53c49360da6eebcd78c35b6450032d4ea9beba450a2955a5ea91925d8c2',
    'agent_timeout_seconds': 1800,
}
EVAL_ID = 'EVAL-001'
BENCHMARK_CONFIG = None
TEST_ROOTS = ['test']
EXPECTED_HISTORY = 2
EXPECTED_FAILURE = 'Expect a list of length 7, but got a list of length 6'
RESULT_MODE = 'unittest'
EXPECTED_TEST_COUNT = 1
SUPPORT_FILES = {}
TEST_HASHES = {}
OBJECT_INVENTORY_HASH = None


def frozen(eval_id):
    path = REPO / f'evals/results/{eval_id}/manifest.json'
    return eval_id == 'EVAL-001' or (path.is_file() and json.loads(path.read_text()).get('status') == 'FROZEN')


def configure(eval_id):
    """Load only evaluator-owned configuration; never mount this in the agent."""
    global EVAL_ID, RESULTS, SEED, FIXTURES, COMMIT, IMAGE, PROMPT, TEST_COMMAND
    global CONFIG, BENCHMARK_CONFIG, TEST_ROOTS, EXPECTED_HISTORY, EXPECTED_FAILURE
    global RESULT_MODE, EXPECTED_TEST_COUNT, SUPPORT_FILES, TEST_HASHES, OBJECT_INVENTORY_HASH
    if eval_id == 'EVAL-001':
        return
    if frozen(eval_id):
        raise InfrastructureError(f'{eval_id} is frozen; use its tag for historical reproduction')
    path = REPO / f'evals/{eval_id}-config.json'
    data = json.loads(path.read_text())
    if data['status'] != 'PREPARED':
        raise InfrastructureError(f'{eval_id} is not prepared for agent runs')
    EVAL_ID = eval_id
    BENCHMARK_CONFIG = path
    RESULTS = REPO / f'evals/results/{eval_id}'
    SEED = REPO / f'experiments/.{eval_id}-seed.git'
    FIXTURES = REPO / f'experiments/.{eval_id}-fixtures'
    COMMIT, IMAGE = data['workspace_commit'], data['runner_image']
    PROMPT = REPO / f'evals/{eval_id}-task.md'
    CONFIG = data['agent_configuration']
    TEST_COMMAND, TEST_ROOTS = data['test_command'], data['test_roots']
    EXPECTED_HISTORY = data['seed_commit_count']
    EXPECTED_FAILURE = data['expected_failure']
    RESULT_MODE = data['result_mode']
    EXPECTED_TEST_COUNT = data['expected_test_count']
    SUPPORT_FILES = data['support_files']
    TEST_HASHES = data['transplanted_test_sha256']
    OBJECT_INVENTORY_HASH = data['git_object_inventory_sha256']


class InfrastructureError(RuntimeError):
    pass


def command(args, check=True, timeout=120, **kwargs):
    if str(args[0]) == 'git':
        args = ['git', '--no-optional-locks', '-c', 'gc.auto=0',
                '-c', 'maintenance.auto=false', '-c', 'gc.autoDetach=false', *args[1:]]
    result = subprocess.run([str(x) for x in args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, **kwargs)
    if check and result.returncode:
        raise InfrastructureError(f'{args[0]} failed ({result.returncode}): '
                                  + result.stderr.decode(errors='replace')[-2000:])
    return result


def git(workspace, *args):
    return command(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
                    '-C', workspace, *args]).stdout


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('wb') as file:
        file.write(data.encode() if isinstance(data, str) else data)
        file.flush()
        os.fsync(file.fileno())
    temp.replace(path)


def save_json(path, data):
    save(path, json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def workspace_for(condition):
    return REPO / f'experiments/{EVAL_ID}-{condition}'


def object_inventory_hash(repository, bare=False):
    prefix = ['git', '--git-dir', repository] if bare else ['git', '-C', repository]
    output = command(prefix + ['cat-file', '--batch-all-objects',
                               '--batch-check=%(objectname) %(objecttype)']).stdout
    return hashlib.sha256(b'\n'.join(sorted(output.splitlines())) + b'\n').hexdigest()


def verify_clean(workspace):
    if git(workspace, 'rev-parse', 'HEAD').decode().strip() != COMMIT:
        raise InfrastructureError('Unexpected workspace commit')
    if git(workspace, 'status', '--short'):
        raise InfrastructureError('Workspace is not clean')
    if git(workspace, 'remote') or (workspace / '.git/objects/info/alternates').exists():
        raise InfrastructureError('Workspace must have independent storage and no remotes')
    if EVAL_ID != 'EVAL-001':
        if git(workspace, 'ls-files', '--others', '--ignored', '--exclude-standard'):
            raise InfrastructureError('Unexpected ignored files in workspace')
        for name, expected in SUPPORT_FILES.items():
            if digest(workspace / name) != expected:
                raise InfrastructureError(f'Unexpected benchmark support file: {name}')
        for name, expected in TEST_HASHES.items():
            if digest(workspace / name) != expected:
                raise InfrastructureError(f'Transplanted benchmark test changed: {name}')
        if OBJECT_INVENTORY_HASH:
            if git(workspace, 'rev-list', '--all').decode().splitlines() != [COMMIT]:
                raise InfrastructureError('Workspace contains unexpected Git history')
            if object_inventory_hash(workspace) != OBJECT_INVENTORY_HASH:
                raise InfrastructureError('Workspace contains unexpected Git objects')


def workspace_fingerprint(workspace):
    verify_clean(workspace)
    files = []
    for entry in git(workspace, 'ls-files', '--stage', '-z').split(b'\0'):
        if not entry:
            continue
        mode_blob, name = entry.split(b'\t', 1)
        path = workspace / name.decode()
        mode = mode_blob.decode().split()[0]
        data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        files.append([name.decode(), mode, hashlib.sha256(data).hexdigest()])
    payload = {'head': COMMIT, 'tracked_files': files, 'support_files': SUPPORT_FILES,
               'configuration': CONFIG, 'runner_image': IMAGE,
               'test_command': TEST_COMMAND,
               'benchmark_config_sha256': digest(BENCHMARK_CONFIG) if BENCHMARK_CONFIG else None}
    return {'sha256': hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'head': COMMIT, 'tracked_file_count': len(files), 'support_files': SUPPORT_FILES,
            'git_status_porcelain': '', 'unexpected_ignored_files': []}


def lifecycle_log(operation, target, reason, **details):
    """Write and fsync BEFORE destructive operations; evaluator-only log."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    entry = {'timestamp': datetime.now(timezone.utc).isoformat(),
             'operation': operation, 'target_path': str(target), 'reason': reason, **details}
    with (RESULTS / 'lifecycle.jsonl').open('a') as file:
        file.write(json.dumps(entry, sort_keys=True) + '\n')
        file.flush()
        os.fsync(file.fileno())


def registration_path():
    return REPO / f'evals/preparation/{EVAL_ID}/workspace-registration.json'


def safe_workspace(workspace):
    if workspace not in [workspace_for('baseline'), workspace_for('skill')]:
        raise InfrastructureError('Unsafe workspace target')
    if workspace.is_symlink() or workspace.parent.is_symlink():
        raise InfrastructureError('Workspace paths must not be symlinks')


def identity(workspace):
    safe_workspace(workspace)
    if not workspace.is_dir():
        raise InfrastructureError(f'Prepared workspace disappeared: {workspace}')
    info = workspace.stat()
    return {'path': str(workspace), 'device': info.st_dev, 'inode': info.st_ino}


def verify_identity(workspace):
    actual = identity(workspace)
    path = registration_path()
    if not path.is_file():
        raise InfrastructureError('Workspaces must be explicitly created during preparation')
    expected = json.loads(path.read_text()).get(str(workspace))
    if not expected or any(actual[k] != expected[k] for k in actual):
        raise InfrastructureError(f'Workspace root identity changed: {workspace}')
    return expected


def workspace_checkpoint(stage):
    """Read workspace state only; write observations outside solver mounts."""
    states, failures = {}, []
    for condition in ('baseline', 'skill'):
        workspace = workspace_for(condition)
        state = {'path': str(workspace), 'exists': workspace.is_dir(),
                 'head': None, 'git_status_short': None, 'clean': None, 'fingerprint': None}
        try:
            expected = verify_identity(workspace)
            state['head'] = git(workspace, 'rev-parse', 'HEAD').decode().strip()
            state['git_status_short'] = git(workspace, 'status', '--short').decode()
            state['clean'] = not state['git_status_short']
            state['fingerprint'] = workspace_fingerprint(workspace)
            if state['fingerprint']['sha256'] != expected['fingerprint']:
                raise InfrastructureError('Frozen starting fingerprint changed')
        except Exception as error:
            state['error'] = str(error)
            failures.append(str(error))
        states[condition] = state
    lifecycle_log('workspace-checkpoint', REPO / 'experiments', stage, states=states)
    if failures:
        raise InfrastructureError('Workspace integrity failure: ' + '; '.join(failures))
    return states


def prepare_workspaces():
    """Explicit preparation only. Existing roots are never replaced or adopted."""
    if registration_path().exists():
        workspace_checkpoint('preparation-existing')
        return
    for condition in ('baseline', 'skill'):
        workspace = workspace_for(condition)
        safe_workspace(workspace)
        if workspace.exists():
            raise InfrastructureError(f'Unregistered workspace retained for review: {workspace}')
    records = {}
    for condition in ('baseline', 'skill'):
        workspace = workspace_for(condition)
        lifecycle_log('create-workspace', workspace, 'explicit experiment preparation')
        command(['git', 'clone', '--no-local', SEED, workspace])
        git(workspace, 'remote', 'remove', 'origin')
        git(workspace, 'checkout', '--detach', COMMIT)
        git(workspace, 'config', 'gc.auto', '0')
        git(workspace, 'config', 'maintenance.auto', 'false')
        verify_clean(workspace)
        records[str(workspace)] = dict(identity(workspace), fingerprint=workspace_fingerprint(workspace)['sha256'])
    save_json(registration_path(), records)
    workspace_checkpoint('preparation-created')


def reset_workspace(workspace, captured=False):
    """Restore pristine independent Git storage/content without deleting the root."""
    expected = verify_identity(workspace)
    if not captured:
        unexpected = git(workspace, 'ls-files', '--others', '--exclude-standard', '-z')
        unexpected += git(workspace, 'ls-files', '--others', '--ignored', '--exclude-standard', '-z')
        if unexpected:
            raise InfrastructureError('Unexpected contamination; workspace retained: ' +
                                      unexpected.decode(errors='replace').replace('\0', ', '))
    # Build a pristine clone outside the experiment tree, including fresh objects,
    # refs and hooks. A failed clone leaves the prepared root untouched.
    temporary = tempfile.mkdtemp(prefix=f'{EVAL_ID}-reset-')
    staging = Path(temporary) / 'snapshot'
    try:
        command(['git', 'clone', '--no-local', SEED, staging])
        git(staging, 'remote', 'remove', 'origin')
        git(staging, 'checkout', '--detach', COMMIT)
        git(staging, 'config', 'gc.auto', '0')
        git(staging, 'config', 'maintenance.auto', 'false')
        verify_clean(staging)
        if workspace_fingerprint(staging)['sha256'] != expected['fingerprint']:
            raise InfrastructureError('Reset source differs from registered frozen state')
        verify_identity(workspace)
        for child in sorted(workspace.iterdir()):
            verify_identity(workspace)
            lifecycle_log('remove-workspace-child', child, 'restore captured run state' if captured else 'explicit reset')
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        for child in sorted(staging.iterdir()):
            verify_identity(workspace)
            target = workspace / child.name
            if child.is_dir() and not child.is_symlink():
                shutil.copytree(child, target, symlinks=True)
            elif child.is_symlink():
                target.symlink_to(os.readlink(child))
            else:
                shutil.copy2(child, target)
        verify_identity(workspace)
        verify_clean(workspace)
        if workspace_fingerprint(workspace)['sha256'] != expected['fingerprint']:
            raise InfrastructureError('Post-reset fingerprint mismatch')
    finally:
        lifecycle_log('remove-temporary-reset-directory', temporary, 'discard verified reset staging clone')
        shutil.rmtree(temporary)


def remove_container(name):
    if command(['docker', 'container', 'inspect', name], check=False).returncode == 0:
        command(['docker', 'rm', '-f', name])


def preflight(prepare=False):
    for path, key in [(PROMPT, 'prompt_sha256'), (SKILL, 'skill_sha256')]:
        if digest(path) != CONFIG[key]:
            raise InfrastructureError(f'Frozen input changed: {path}')
    if BENCHMARK_CONFIG:
        data = json.loads(BENCHMARK_CONFIG.read_text())
        for name, expected in data.get('harness_input_sha256', {}).items():
            if digest(REPO / name) != expected:
                raise InfrastructureError(f'Frozen harness input changed: {name}')
    command(['docker', 'image', 'inspect', IMAGE])
    head = command(['git', '--git-dir', SEED, 'rev-parse', 'HEAD']).stdout.decode().strip()
    count = command(['git', '--git-dir', SEED, 'rev-list', '--count', 'HEAD']).stdout.decode().strip()
    if head != COMMIT or count != str(EXPECTED_HISTORY):
        raise InfrastructureError('Frozen seed is missing or has unexpected history')
    if OBJECT_INVENTORY_HASH and object_inventory_hash(SEED, bare=True) != OBJECT_INVENTORY_HASH:
        raise InfrastructureError('Seed contains unexpected Git objects')
    for name, expected in TEST_HASHES.items():
        data = command(['git', '--git-dir', SEED, 'show', f'{COMMIT}:{name}']).stdout
        if hashlib.sha256(data).hexdigest() != expected:
            raise InfrastructureError(f'Seed benchmark test changed: {name}')
    # Restore benchmark-provided tests from the sanitized frozen snapshot. Their
    # preparation-time transplantation never grants the solver fixed-source access.
    data = command(['git', '--git-dir', SEED, 'archive', '--format=tar', COMMIT, *TEST_ROOTS]).stdout
    expected = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        for member in members:
            path = Path(member.name)
            allowed = any(path == Path(root) or Path(root) in path.parents or path in Path(root).parents for root in TEST_ROOTS)
            if path.is_absolute() or '..' in path.parts or not allowed or not (member.isfile() or member.isdir()):
                raise InfrastructureError('Unexpected benchmark fixture archive entry')
            if member.isfile():
                expected[member.name] = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
        if not FIXTURES.exists():
            if not prepare:
                raise InfrastructureError('Frozen fixtures missing; run explicit preparation')
            lifecycle_log('create-fixtures', FIXTURES, 'explicit experiment preparation')
            FIXTURES.mkdir()
            archive.extractall(FIXTURES, members=members)
    if FIXTURES.is_symlink() or any(p.is_symlink() for p in FIXTURES.rglob('*')):
        raise InfrastructureError('Unsafe frozen fixture symlink')
    actual = {str(p.relative_to(FIXTURES)): digest(p) for p in FIXTURES.rglob('*') if p.is_file()}
    if actual != expected:
        raise InfrastructureError('Frozen fixtures changed; retained for review')


def make_container(name, workspace, condition, grader=False):
    remove_container(name)
    args = ['docker', 'run', '-dt', '--name', name, '-v', f'{workspace}:/workspace',
            '-w', '/workspace']
    if EVAL_ID != 'EVAL-001':
        data = json.loads(BENCHMARK_CONFIG.read_text())
        for key, value in data['environment'].items():
            args += ['-e', f'{key}={value}']
    if grader:
        for root in TEST_ROOTS:
            args += ['-v', f'{FIXTURES / root}:/workspace/{root}:ro']
    command(args + [IMAGE])
    command(['docker', 'exec', name, 'git', 'config', '--global', '--add',
             'safe.directory', '/workspace'])
    if grader:
        return
    command(['docker', 'exec', name, 'mkdir', '-p', '/root/.codex'])
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        raise InfrastructureError('Codex auth.json missing; authenticate on the host first')
    command(['docker', 'cp', auth, f'{name}:/root/.codex/auth.json'])
    command(['docker', 'exec', name, 'codex', 'login', 'status'])
    version = command(['docker', 'exec', name, 'codex', '--version']).stdout.decode().strip()
    if version != CONFIG['codex_version']:
        raise InfrastructureError(f'Unexpected Codex version: {version}')
    if condition == 'skill':
        command(['docker', 'exec', name, 'mkdir', '-p', '/root/.agents/skills/efficient-coding'])
        command(['docker', 'cp', SKILL, f'{name}:/root/.agents/skills/efficient-coding/SKILL.md'])
    else:
        command(['docker', 'exec', name, 'bash', '-c',
                 'test ! -e /root/.agents/skills/efficient-coding'])
    command(['docker', 'exec', name, 'bash', '-c', 'test ! -d /root/.codex/sessions'])
    mounts = json.loads(command(['docker', 'inspect', name]).stdout)[0]['Mounts']
    if len(mounts) != 1 or mounts[0]['Source'] != str(workspace):
        raise InfrastructureError('Agent container has unexpected mounts')


def django_test_results(output):
    """Parse verbose Django unittest IDs, including multiline docstring output."""
    import re
    results, current = {}, None
    for line in output.splitlines():
        match = re.match(r'^(test\w+) \(([^)]+)\)(.*)', line)
        if match:
            current = match[2] + '.' + match[1]
            tail = match[3]
            if ' ... ' in tail:
                results[current] = tail.rsplit(' ... ', 1)[1].strip()
                current = None
        elif current and ' ... ' in line:
            results[current] = line.rsplit(' ... ', 1)[1].strip()
            current = None
    return results


def verify_initial_failure(output):
    if RESULT_MODE != 'django_unittest':
        return
    import re
    settings = json.loads(BENCHMARK_CONFIG.read_text())
    expected = set()
    for label in settings['official_FAIL_TO_PASS']:
        match = re.fullmatch(r'(\w+) \(([^)]+)\)', label)
        if not match:
            raise InfrastructureError('Unmapped official initial failure ID')
        expected.add(match[2] + '.' + match[1])
    results = django_test_results(output)
    actual = {key for key, value in results.items() if value in ('ERROR', 'FAIL')}
    if actual != expected or any(value != 'ok' for key, value in results.items() if key not in expected):
        raise InfrastructureError('Initial failures differ from frozen benchmark regression cases')


def benchmark(workspace, name):
    """Evaluate against immutable benchmark-provided tests in a fresh grader."""
    try:
        make_container(name, workspace, 'baseline', grader=True)
        result = command(['docker', 'exec', name, *TEST_COMMAND], check=False, timeout=120)
        output = (result.stdout + result.stderr).decode(errors='replace')
        passed = result.returncode == 0 and 'Ran 1 test' in output and '\nOK' in output
        failed = result.returncode == 1 and 'Ran 1 test' in output and 'FAILED (' in output
        if RESULT_MODE == 'pytest':
            import re
            # Application ERROR logs are normal in negative-path tests. Only
            # pytest's final counts distinguish failures from collection/setup errors.
            final_summary = next((line for line in reversed(output.splitlines())
                                  if re.search(r'\b\d+ (?:passed|failed|errors?)\b', line)), '')
            errors = re.search(r'\b[1-9]\d* errors?\b', final_summary) is not None
            failures = re.search(r'\b[1-9]\d* failed\b', final_summary) is not None
            passed = result.returncode == 0 and not errors and not failures and re.search(rf'\b{EXPECTED_TEST_COUNT} passed\b', final_summary) is not None
            failed = result.returncode == 1 and failures and not errors
        if RESULT_MODE == 'django_unittest':
            import re
            settings = json.loads(BENCHMARK_CONFIG.read_text())
            results = django_test_results(output)
            required = set(settings['required_test_ids'])
            counts = re.findall(r'Ran (\d+) tests? in ', output)
            if set(results) != required or counts != [str(EXPECTED_TEST_COUNT)]:
                raise InfrastructureError('Django test inventory/count differs from frozen benchmark')
            passed = result.returncode == 0 and all(v == 'ok' for v in results.values()) and '\nOK' in output
            failed = result.returncode == 1 and any(v in ('ERROR', 'FAIL') for v in results.values()) and 'FAILED (' in output
            if any(v not in ('ok', 'ERROR', 'FAIL') for v in results.values()):
                raise InfrastructureError('Django benchmark test skipped or unrecognized')
        if not (passed or failed):
            raise InfrastructureError('Benchmark did not produce a recognized test result: ' + output)
        return passed, output, result.returncode
    finally:
        remove_container(name)


def parse_trace(path):
    """Only derive metrics supported by structured events; never infer shell reads."""
    events, event_lines, errors, items, ended = [], [], [], {}, False
    for number, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError('event is not an object')
            events.append(event)
            event_lines.append(number)
        except (ValueError, TypeError):
            errors.append(f'Invalid JSONL line {number}')
    turns = [e for e in events if e.get('type') == 'turn.completed']
    ended = bool(turns) and not any(e.get('type') in ('error', 'turn.failed') for e in events)
    first_lines = {}
    for line_number, e in zip(event_lines, events):
        if e.get('type') in ('item.started', 'item.updated', 'item.completed'):
            item = e.get('item', {})
            if not isinstance(item, dict) or not item.get('id'):
                errors.append('Unidentified item')
            else:
                first_lines.setdefault(item['id'], line_number)
                items[item['id']] = item
    commands = [i for i in items.values() if i.get('type') == 'command_execution']
    known_tools = {'command_execution', 'file_change', 'mcp_tool_call', 'web_search',
                   'collab_tool_call', 'image_view', 'todo_list', 'file_read', 'read_file'}
    known_non_tools = {'agent_message', 'reasoning'}
    unknown = sorted({str(i.get('type')) for i in items.values()
                      if i.get('type') not in known_tools | known_non_tools})
    complete = ended and not errors
    metrics = {'input_tokens': None, 'output_tokens': None, 'cached_input_tokens': None, 'total_tokens': None,
               'tool_calls': None, 'shell_commands': None, 'files_inspected': None,
               'test_runs': None}
    for field in ('input_tokens', 'output_tokens', 'cached_input_tokens'):
        values = [(e.get('usage') or {}).get(field)
                  if isinstance(e.get('usage'), dict) else None for e in turns]
        if complete and values and all(type(v) is int and v >= 0 for v in values):
            metrics[field] = sum(values)
    if metrics['input_tokens'] is not None and metrics['output_tokens'] is not None:
        metrics['total_tokens'] = metrics['input_tokens'] + metrics['output_tokens']
    if complete:
        metrics['shell_commands'] = len(commands)
        if not unknown:
            metrics['tool_calls'] = sum(i.get('type') in known_tools for i in items.values())
    timing_by_line = {}
    timing_path = path.with_name('event-timing.jsonl')
    if timing_path.exists():
        for record in timing_path.read_text().splitlines():
            try:
                entry = json.loads(record)
                timing_by_line[entry['line_number']] = entry['elapsed_seconds']
            except (ValueError, KeyError, TypeError):
                pass  # Missing/invalid sidecar timestamps never invalidate historical raw traces.
    observable_items = [(first_lines[key], item) for key, item in items.items()
                        if item.get('type') in known_tools or item.get('type') in unknown]
    analysis_config = json.loads(BENCHMARK_CONFIG.read_text()) if BENCHMARK_CONFIG else {}
    action_metrics, trajectory = analyze_actions(observable_items, timing_by_line,
        source_roots=analysis_config.get('source_roots'), test_entrypoints=analysis_config.get('test_entrypoints'))
    metrics.update({key: value if complete else None for key, value in action_metrics.items()})
    metrics['total_tool_calls'] = metrics['tool_calls']
    # Comprehensive filesystem reads remain unknown; explicit requests are separately scoped.
    metrics['files_inspected'] = None
    return metrics, {
        'trajectory': trajectory,
        'trace_completed': complete, 'trace_errors': errors, 'unknown_item_types': unknown,
        'reported_turn_usage': [e.get('usage') for e in turns],
        'commands': [i.get('command') for i in commands],
        'metric_limitations': [
            'Explicit read/search/test command counts describe observable supported operations; physical reads and opaque programs remain unknown.',
            'tool_calls counts unique structured tool items, not hidden calls or shell subcommands; unknown item types produce null.',
            'shell_commands counts command_execution items, including compound command strings as one execution.',
            'total_tokens = reported input_tokens + output_tokens; cached input is already included, not added twice.',
        ],
    }


def run_agent(args, input, stdout, stderr, timeout, timing_path, started):
    """Preserve raw stdout bytes and separately timestamp line receipt on the host."""
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
    pump_errors = []
    def pump():
        try:
            with timing_path.open('w') as timings:
                for line_number, line in enumerate(iter(process.stdout.readline, b''), 1):
                    received = time.monotonic() - started
                    stdout.write(line)
                    stdout.flush()
                    timings.write(json.dumps({'line_number': line_number,
                                              'elapsed_seconds': round(received, 6)}) + '\n')
                    timings.flush()
                os.fsync(timings.fileno())
        except Exception as error:
            pump_errors.append(error)
    worker = threading.Thread(target=pump, daemon=True)
    worker.start()
    try:
        process.stdin.write(input)
        process.stdin.close()
        code = process.wait(timeout=timeout)
    except BaseException:
        process.kill()
        process.wait()
        raise
    finally:
        worker.join(timeout=5)
        if not worker.is_alive():
            process.stdout.close()
        if not process.stdin.closed:
            process.stdin.close()
    if worker.is_alive() or pump_errors:
        raise InfrastructureError('Structured-output capture did not finish reliably')
    return subprocess.CompletedProcess(args, code)


def reanalyze():
    """Update derived summaries/trajectories only; leave every raw input unchanged."""
    for run in ORDER:
        directory = RESULTS / run
        path = directory / 'summary.json'
        if not path.exists() or not (directory / 'codex.jsonl').exists():
            continue
        summary = json.loads(path.read_text())
        metrics, details = parse_trace(directory / 'codex.jsonl')
        summary.update(metrics)
        summary['analysis_schema_version'] = details['trajectory']['schema_version']
        metadata_path = directory / 'metadata.json'
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
            summary['skill_invocation_requested'] = metadata.get('skill_invocation')
        else:
            summary['skill_invocation_requested'] = None
        save_json(path, summary)
        save_json(directory / 'trajectory.json', details['trajectory'])
    report()


def capture(workspace, directory):
    save(directory / 'patch.diff', git(workspace, 'diff', '--binary', '--no-ext-diff', '--no-textconv', COMMIT))
    save(directory / 'diff-stat.txt', git(workspace, 'diff', '--stat', '--no-ext-diff', '--no-textconv', COMMIT))
    save(directory / 'git-status.txt', git(workspace, 'status', '--short'))
    tracked = git(workspace, 'diff', '--name-only', '--no-renames', COMMIT, '-z').decode().split('\0')
    untracked = git(workspace, 'ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')
    paths = sorted(set(filter(None, tracked + untracked)))
    save_json(directory / 'modified-paths.json', paths)
    # Preserve additions omitted by git diff. Do not dereference links outside the checkout.
    with tarfile.open(directory / 'untracked.tar', 'w', dereference=False) as archive:
        for name in filter(None, untracked):
            archive.add(workspace / name, arcname=name, recursive=False)
    return paths


def report():
    workspace_checkpoint('report-before')
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for run in ORDER:
        path = RESULTS / run / 'summary.json'
        if path.exists():
            rows.append(json.loads(path.read_text()))
    valid = {condition: [r for r in rows if r['condition'] == condition
                        and r.get('infrastructure_failure') is None]
             for condition in ('baseline', 'skill')}
    signatures = {json.dumps(r.get('configuration'), sort_keys=True) for r in rows}
    if len(signatures) > 1:
        raise InfrastructureError('Refusing to aggregate different configurations')
    lines = [f'# {EVAL_ID} report', '', 'Explicit Skill invocation experiment; no statistical significance is claimed.', '',
             '| Run | Condition | Success | Tokens | Seconds | Tool items | Infrastructure failure |',
             '| --- | --- | --- | ---: | ---: | ---: | --- |']
    def shown(value):
        return '—' if value is None else str(value).replace('|', '\\|').replace('\n', ' ')
    for r in rows:
        lines.append('| ' + ' | '.join(shown(r.get(k)) for k in
                     ('run_id', 'condition', 'success', 'total_tokens', 'duration_seconds',
                      'tool_calls', 'infrastructure_failure')) + ' |')
    lines += ['', '| Metric | Baseline | Efficient Coding v0.1 |', '| --- | ---: | ---: |']
    def value(condition, metric):
        group = valid[condition]
        if metric == 'Runs':
            return len(group)
        if metric == 'Successful runs':
            return sum(r.get('success') is True for r in group)
        if metric == 'Success rate':
            return f'{sum(r.get("success") is True for r in group) / len(group):.1%}' if group else None
        key = {'Median total tokens': 'total_tokens', 'Median duration': 'duration_seconds',
               'Median tool calls': 'tool_calls', 'Median files inspected': 'files_inspected',
               'Median test runs': 'test_runs',
               'Median cached input tokens': 'cached_input_tokens',
               'Median repository searches': 'repository_search_commands',
               'Median unique files inspected (explicit repository reads)': 'unique_files_inspected',
               'Median total file reads (explicit; includes Skill)': 'total_file_reads',
               'Median repository file reads (explicit)': 'repository_file_reads',
               'Median repeated reads (repository)': 'repeated_file_reads',
               'Median Skill loading events': 'skill_loading_events',
               'Median tool items excluding Skill loading': 'tool_items_excluding_skill_loading'}[metric]
        values = [r.get(key) for r in group if r.get(key) is not None]
        return statistics.median(values) if values else None
    for metric in ['Runs', 'Successful runs', 'Success rate', 'Median total tokens',
                   'Median duration', 'Median tool calls', 'Median cached input tokens',
                   'Median repository searches', 'Median unique files inspected (explicit repository reads)',
                   'Median total file reads (explicit; includes Skill)',
                   'Median repository file reads (explicit)', 'Median repeated reads (repository)',
                   'Median test runs', 'Median Skill loading events',
                   'Median tool items excluding Skill loading']:
        lines.append(f'| {metric} | {shown(value("baseline", metric))} | {shown(value("skill", metric))} |')
    lines += ['', 'Infrastructure failures are listed individually and excluded from aggregates.',
              'Medians use available values only; missing metrics are not zero.',
              'Success is a benchmark-test proxy, not proof of complete correctness.',
              'Read metrics count explicit named inspection requests, not all physical reads; search scanning is excluded.',
              'Test counts describe recognized observable shell invocations, not hidden interpreter/subprocess activity.',
              'First-action timing and pre-edit tokens are unavailable for historical runs without per-event timing/usage.', '']
    save(RESULTS / 'report.md', '\n'.join(lines))
    workspace_checkpoint('report-after')


def run_one(run_id):
    condition = 'baseline' if run_id.startswith('B') else 'skill'
    workspace = workspace_for(condition)
    directory = RESULTS / run_id
    directory.mkdir(parents=True, exist_ok=True)
    if any(p.name != '.gitkeep' for p in directory.iterdir()):
        raise InfrastructureError(f'{run_id} already has artifacts; explicitly clear them before rerunning')
    name = f'efficient-coding-{EVAL_ID.lower()}-{run_id.lower()}'
    metadata = {'run_id': run_id, 'condition': condition, 'configuration': CONFIG,
                'commit': COMMIT, 'runner_image': IMAGE, 'workspace': str(workspace),
                'prompt_path': str(PROMPT), 'skill_invocation': condition == 'skill',
                'started_at': datetime.now(timezone.utc).isoformat()}
    summary = {'run_id': run_id, 'condition': condition, 'model': CONFIG['model'],
               'commit': COMMIT, 'success': None, 'benchmark_test_passed': None,
               'input_tokens': None, 'output_tokens': None, 'total_tokens': None,
               'duration_seconds': None, 'tool_calls': None, 'shell_commands': None,
               'files_inspected': None, 'files_modified': None, 'test_runs': None,
               'infrastructure_failure': None, 'configuration': CONFIG,
               'skill_invocation_requested': condition == 'skill'}
    prepared, saved = False, False
    save_json(directory / 'metadata.json', metadata)
    try:
        metadata['workspace_state_before'] = workspace_checkpoint('run-before:' + run_id)
        preflight()
        # Remove legacy manual containers before touching their bind mounts.
        remove_container(f'{EVAL_ID}-{condition}')
        verify_identity(workspace)
        prepared = True
        make_container(name, workspace, condition)
        passed, output, code = benchmark(workspace, name + '-before')
        save(directory / 'initial-test-output.txt', output)
        if passed or EXPECTED_FAILURE not in output:
            raise InfrastructureError('Frozen benchmark failure is not reproduced')
        verify_initial_failure(output)
        verify_clean(workspace)
        workspace_checkpoint('agent-before:' + run_id)
        metadata['workspace_fingerprint'] = workspace_fingerprint(workspace)
        instructions = ('Use the $efficient-coding Skill v0.1 for this task.'
                        if condition == 'skill' else '')
        args = ['docker', 'exec', '-i', name, 'codex', '--no-daemon', '-a', CONFIG['approval_policy'],
                'exec', '--ignore-user-config', '--json', '--color', 'never',
                '-C', '/workspace', '-m', CONFIG['model'], '-s', CONFIG['sandbox'],
                '-c', 'model_reasoning_effort=' + json.dumps(CONFIG['reasoning_effort']),
                '-c', 'web_search=' + json.dumps(CONFIG['web_search']),
                '-c', 'features.multi_agent=false',
                '-c', 'developer_instructions=' + json.dumps(instructions), '-']
        metadata['codex_command'] = args
        metadata['task_prompt_sha256'] = digest(PROMPT)
        save_json(directory / 'metadata.json', metadata)
        started = time.monotonic()
        agent_failure = None
        with (directory / 'codex.jsonl').open('wb') as stdout, (directory / 'codex-stderr.txt').open('wb') as stderr:
            try:
                result = run_agent(args, input=PROMPT.read_bytes(), stdout=stdout,
                                   stderr=stderr, timeout=CONFIG['agent_timeout_seconds'],
                                   timing_path=directory / 'event-timing.jsonl', started=started)
                metadata['codex_exit_code'] = result.returncode
                if result.returncode:
                    agent_failure = f'Codex exited {result.returncode}; inspect codex.jsonl and codex-stderr.txt'
            except subprocess.TimeoutExpired:
                command(['docker', 'stop', '-t', '1', name])
                agent_failure = 'Codex timed out; no continuation was attempted'
            finally:
                summary['duration_seconds'] = round(time.monotonic() - started, 3)
                stdout.flush()
                stderr.flush()
                os.fsync(stdout.fileno())
                os.fsync(stderr.fileno())
        remove_container(name)
        metrics, details = parse_trace(directory / 'codex.jsonl')
        summary.update(metrics)
        metadata.update({key: value for key, value in details.items() if key != 'trajectory'})
        save_json(directory / 'trajectory.json', details['trajectory'])
        passed, output, code = benchmark(workspace, name + '-after')
        save(directory / 'test-output.txt', output)
        summary['benchmark_test_passed'] = passed
        metadata['benchmark_exit_code'] = code
        metadata['post_agent_harness_test_runs'] = 1
        if agent_failure or not details['trace_completed']:
            raise InfrastructureError(agent_failure or 'Codex trace is incomplete or invalid')
        summary['success'] = passed
    except (Exception, KeyboardInterrupt) as error:
        summary['infrastructure_failure'] = f'{type(error).__name__}: {error}'
        summary['success'] = None
    finally:
        # Quiesce the agent before capturing; never reset while it can still write.
        quiesced, captured = True, False
        try:
            remove_container(name)
        except Exception as error:
            quiesced = False
            summary['infrastructure_failure'] = f'Cannot stop agent container: {error}'
        if prepared and quiesced:
            try:
                paths = capture(workspace, directory)
                summary['files_modified'] = len(paths)
                captured = True
            except Exception as error:
                summary['infrastructure_failure'] = f'Artifact capture failed; workspace retained: {error}'
        metadata['finished_at'] = datetime.now(timezone.utc).isoformat()
        save_json(directory / 'metadata.json', metadata)
        save_json(directory / 'summary.json', summary)
        saved = True
        if prepared and saved and captured and quiesced:
            try:
                reset_workspace(workspace, captured=True)
            except Exception as error:
                summary['infrastructure_failure'] = f'Post-save reset failed: {error}'
                save_json(directory / 'summary.json', summary)
        try:
            metadata['workspace_state_after'] = workspace_checkpoint('run-after:' + run_id)
            save_json(directory / 'metadata.json', metadata)
            report()
        except Exception as error:
            message = f'Lifecycle verification failed: {error}'
            metadata['lifecycle_failure'] = message
            save_json(directory / 'metadata.json', metadata)
            summary['infrastructure_failure'] = (summary['infrastructure_failure'] + '; ' + message
                                                 if summary['infrastructure_failure'] else message)
            save_json(directory / 'summary.json', summary)
            print(summary['infrastructure_failure'], file=sys.stderr)
    print(f'{run_id}: ' + (summary['infrastructure_failure'] or f'benchmark passed={summary["benchmark_test_passed"]}'), flush=True)
    return summary['infrastructure_failure'] is None


def check_only():
    workspace_checkpoint('check-before')
    preflight()
    fingerprints = {}
    for condition in ('baseline', 'skill'):
        workspace = workspace_for(condition)
        name = f'efficient-coding-{EVAL_ID.lower()}-check-{condition}'
        remove_container(f'{EVAL_ID}-{condition}')
        verify_identity(workspace)
        try:
            make_container(name, workspace, condition)
            command(['docker', 'exec', name, 'codex', '--no-daemon', '-a', 'never',
                     'exec', '--ignore-user-config', '--json', '--help'])
            passed, output, code = benchmark(workspace, name + '-test')
            if passed or EXPECTED_FAILURE not in output:
                raise InfrastructureError('Expected assertion failure not reproduced')
            verify_initial_failure(output)
            verify_clean(workspace)
            fingerprints[condition] = workspace_fingerprint(workspace)
            if EVAL_ID != 'EVAL-001':
                directory = REPO / f'evals/preparation/{EVAL_ID}'
                failure_path = directory / f'{condition}-failure.txt'
                if not failure_path.exists():
                    save(failure_path, output)
                lifecycle_log('benchmark-failure-verified', workspace, 'preparation/check only; no model request',
                              exit_code=code, output_sha256=hashlib.sha256(output.encode()).hexdigest())
            print(f'{condition}: HEAD={COMMIT}; git status --short empty; benchmark-provided test fails; isolation verified')
        finally:
            remove_container(name)
            workspace_checkpoint('check-condition-after:' + condition)
    if fingerprints['baseline']['sha256'] != fingerprints['skill']['sha256']:
        raise InfrastructureError('Baseline/treatment starting fingerprints differ')
    if EVAL_ID != 'EVAL-001':
        save_json(REPO / f'evals/preparation/{EVAL_ID}/workspace-fingerprints.json', fingerprints)
    print('Equivalent starting fingerprint: ' + fingerprints['baseline']['sha256'])
    workspace_checkpoint('check-after')
    print('Infrastructure check complete. No Codex task or model request was made.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--eval', default='EVAL-001', choices=['EVAL-001', 'EVAL-002', 'EVAL-003'])
    parser.add_argument('run_id', nargs='?', choices=ORDER)
    parser.add_argument('--prepare', action='store_true', help='Explicitly create/register workspaces without an agent request')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--check', action='store_true', help='Reset/verify both arms without starting an agent')
    parser.add_argument('--reanalyze', action='store_true', help='Reparse existing raw traces; no agent execution')
    parser.add_argument('--report', action='store_true', help='Regenerate report from saved summaries only')
    args = parser.parse_args()
    if sum([bool(args.run_id), args.all, args.check, args.report, args.reanalyze, args.prepare]) != 1:
        parser.error('Choose one run ID, --all, --check, --report, --prepare, or --reanalyze')
    if frozen(args.eval):
        if args.report:
            print((REPO / f'evals/results/{args.eval}/report.md').read_text(), end='')
            return 0
        parser.error(f'{args.eval} is frozen. Historical workspaces/artifacts cannot be changed. Use its tag in a separate checkout.')
    try:
        configure(args.eval)
    except (OSError, KeyError, ValueError, InfrastructureError) as error:
        parser.error(str(error))
    RESULTS.mkdir(parents=True, exist_ok=True)
    lock = RESULTS / '.runner.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        parser.error('Another runner is active, or a stale .runner.lock needs manual review')
    try:
        os.write(descriptor, str(os.getpid()).encode())
        if args.prepare:
            preflight(prepare=True)
            prepare_workspaces()
            check_only()
        elif args.reanalyze:
            reanalyze()
        elif args.report:
            report()
        elif args.check:
            check_only()
        else:
            order = ORDER if args.all else [args.run_id]
            print(json.dumps({'codex_version': CONFIG['codex_version'], 'model': CONFIG['model'],
                              'reasoning_effort': CONFIG['reasoning_effort'], 'commit': COMMIT,
                              'prompt_path': str(PROMPT), 'skill_version': CONFIG['skill_version'],
                              'run_order': order}, indent=2), flush=True)
            for run_id in order:
                if not run_one(run_id):
                    return 1
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(f'Infrastructure failure: {error}', file=sys.stderr)
        return 1
    finally:
        os.close(descriptor)
        lock.unlink()


if __name__ == '__main__':
    sys.exit(main())
