#!/usr/bin/env python3
"""EVAL-001 harness. --check never starts a coding agent. Standard library only."""
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


class InfrastructureError(RuntimeError):
    pass


def command(args, check=True, timeout=120, **kwargs):
    result = subprocess.run([str(x) for x in args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, **kwargs)
    if check and result.returncode:
        raise InfrastructureError(f'{args[0]} failed ({result.returncode}): '
                                  + result.stderr.decode(errors='replace')[-2000:])
    return result


def git(workspace, *args):
    return command(['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
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
    return REPO / f'experiments/EVAL-001-{condition}'


def verify_clean(workspace):
    if git(workspace, 'rev-parse', 'HEAD').decode().strip() != COMMIT:
        raise InfrastructureError('Unexpected workspace commit')
    if git(workspace, 'status', '--short'):
        raise InfrastructureError('Workspace is not clean')
    if git(workspace, 'remote') or (workspace / '.git/objects/info/alternates').exists():
        raise InfrastructureError('Workspace must have independent storage and no remotes')


def reset_workspace(workspace):
    """Reclone to remove previous objects, refs, reflogs, hooks and ignored files."""
    if workspace not in [workspace_for('baseline'), workspace_for('skill')] or workspace.is_symlink():
        raise InfrastructureError('Unsafe reset target')
    staging = workspace.with_name(workspace.name + '.reset')
    if staging.exists():
        raise InfrastructureError(f'Remove interrupted reset directory first: {staging}')
    command(['git', 'clone', '--no-local', SEED, staging])
    git(staging, 'remote', 'remove', 'origin')
    git(staging, 'checkout', '--detach', '--force', COMMIT)
    git(staging, 'reset', '--hard', COMMIT)
    git(staging, 'clean', '-fdx')
    verify_clean(staging)
    if workspace.exists():
        shutil.rmtree(workspace)
    staging.rename(workspace)
    verify_clean(workspace)


def remove_container(name):
    if command(['docker', 'container', 'inspect', name], check=False).returncode == 0:
        command(['docker', 'rm', '-f', name])


def preflight():
    for path, key in [(PROMPT, 'prompt_sha256'), (SKILL, 'skill_sha256')]:
        if digest(path) != CONFIG[key]:
            raise InfrastructureError(f'Frozen input changed: {path}')
    command(['docker', 'image', 'inspect', IMAGE])
    head = command(['git', '--git-dir', SEED, 'rev-parse', 'HEAD']).stdout.decode().strip()
    count = command(['git', '--git-dir', SEED, 'rev-list', '--count', 'HEAD']).stdout.decode().strip()
    if head != COMMIT or count != '2':
        raise InfrastructureError('Frozen seed is missing or has unexpected history')
    # Recreate original benchmark tests from the frozen buggy snapshot, never from a fix.
    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)
    FIXTURES.mkdir()
    data = command(['git', '--git-dir', SEED, 'archive', '--format=tar', COMMIT, 'test']).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        for member in members:
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or path.parts[0] != 'test' or not (member.isfile() or member.isdir()):
                raise InfrastructureError('Unexpected benchmark fixture archive entry')
        archive.extractall(FIXTURES, members=members)


def make_container(name, workspace, condition, grader=False):
    remove_container(name)
    args = ['docker', 'run', '-dt', '--name', name, '-v', f'{workspace}:/workspace',
            '-w', '/workspace']
    if grader:
        args += ['-v', f'{FIXTURES / "test"}:/workspace/test:ro']
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


def benchmark(workspace, name):
    """Evaluate against immutable original tests in a fresh grader runtime."""
    try:
        make_container(name, workspace, 'baseline', grader=True)
        result = command(['docker', 'exec', name, *TEST_COMMAND], check=False, timeout=120)
        output = (result.stdout + result.stderr).decode(errors='replace')
        passed = result.returncode == 0 and 'Ran 1 test' in output and '\nOK' in output
        failed = result.returncode == 1 and 'Ran 1 test' in output and 'FAILED (' in output
        if not (passed or failed):
            raise InfrastructureError('Benchmark did not produce a recognized unittest result: ' + output)
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
    action_metrics, trajectory = analyze_actions(observable_items, timing_by_line)
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
    lines = ['# EVAL-001 report', '', 'Explicit Skill invocation experiment; no statistical significance is claimed.', '',
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


def run_one(run_id):
    condition = 'baseline' if run_id.startswith('B') else 'skill'
    workspace = workspace_for(condition)
    directory = RESULTS / run_id
    directory.mkdir(parents=True, exist_ok=True)
    if any(p.name != '.gitkeep' for p in directory.iterdir()):
        raise InfrastructureError(f'{run_id} already has artifacts; explicitly clear them before rerunning')
    name = f'efficient-coding-eval-001-{run_id.lower()}'
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
        preflight()
        # Remove legacy manual containers before touching their bind mounts.
        remove_container(f'EVAL-001-{condition}')
        reset_workspace(workspace)
        prepared = True
        make_container(name, workspace, condition)
        passed, output, code = benchmark(workspace, name + '-before')
        save(directory / 'initial-test-output.txt', output)
        if passed or 'Expect a list of length 7, but got a list of length 6' not in output:
            raise InfrastructureError('Original failure is not reproduced')
        verify_clean(workspace)
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
                reset_workspace(workspace)
            except Exception as error:
                summary['infrastructure_failure'] = f'Post-save reset failed: {error}'
                save_json(directory / 'summary.json', summary)
        report()
    print(f'{run_id}: ' + (summary['infrastructure_failure'] or f'benchmark passed={summary["benchmark_test_passed"]}'), flush=True)
    return summary['infrastructure_failure'] is None


def check_only():
    preflight()
    for condition in ('baseline', 'skill'):
        workspace = workspace_for(condition)
        name = f'efficient-coding-eval-001-check-{condition}'
        remove_container(f'EVAL-001-{condition}')
        reset_workspace(workspace)
        try:
            make_container(name, workspace, condition)
            command(['docker', 'exec', name, 'codex', '--no-daemon', '-a', 'never',
                     'exec', '--ignore-user-config', '--json', '--help'])
            passed, output, code = benchmark(workspace, name + '-test')
            if passed or 'Expect a list of length 7, but got a list of length 6' not in output:
                raise InfrastructureError('Expected assertion failure not reproduced')
            verify_clean(workspace)
            print(f'{condition}: HEAD={COMMIT}; git status --short empty; original test fails; isolation verified')
        finally:
            remove_container(name)
            reset_workspace(workspace)
    print('Infrastructure check complete. No Codex task or model request was made.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id', nargs='?', choices=ORDER)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--check', action='store_true', help='Reset/verify both arms without starting an agent')
    parser.add_argument('--reanalyze', action='store_true', help='Reparse existing raw traces; no agent execution')
    parser.add_argument('--report', action='store_true', help='Regenerate report from saved summaries only')
    args = parser.parse_args()
    if sum([bool(args.run_id), args.all, args.check, args.report, args.reanalyze]) != 1:
        parser.error('Choose one run ID, --all, --check, --report, or --reanalyze')
    RESULTS.mkdir(parents=True, exist_ok=True)
    lock = RESULTS / '.runner.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        parser.error('Another runner is active, or a stale .runner.lock needs manual review')
    try:
        os.write(descriptor, str(os.getpid()).encode())
        if args.reanalyze:
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
