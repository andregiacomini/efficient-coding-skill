"""Conservative observable-action analysis. Never reads reasoning/agent-message text."""
import posixpath
import re
import shlex
from collections import Counter

SKILL_PATH = '/root/.agents/skills/efficient-coding/SKILL.md'
ANALYSIS_VERSION = 2


def normalized(path, cwd='/workspace'):
    absolute = posixpath.normpath(path if path.startswith('/') else posixpath.join(cwd, path))
    return absolute[len('/workspace/'):] if absolute.startswith('/workspace/') else absolute


def literal(path):
    return bool(path) and not any(c in path for c in '$`*?[]{}<>') and path != '-'


def shell_operations(command):
    """Split supported shell syntax without evaluating it. Opaque programs stay opaque."""
    if not isinstance(command, str):
        return [], ['Missing structured command string']
    try:
        outer = shlex.split(command)
        if len(outer) == 3 and posixpath.basename(outer[0]) in ('sh', 'bash', 'zsh') and outer[1] in ('-c', '-lc'):
            command = outer[2]
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';|&<>')
        lexer.whitespace_split = True
        lexer.commenters = ''
        tokens = list(lexer)
    except ValueError:
        return [], ['Unparseable shell quoting']
    segments, segment, separator = [], [], None
    for token in tokens:
        if token in (';', '|', '&&', '||'):
            if segment:
                segments.append((segment, separator))
            segment, separator = [], token
        else:
            segment.append(token)
    if segment:
        segments.append((segment, separator))
    operations, unknown, cwd = [], [], '/workspace'
    for argv, separator in segments:
        if not argv:
            continue
        exe = posixpath.basename(argv[0])
        operation = {'argv': argv, 'category': 'other', 'repository_search': False,
                     'read_requests': [], 'coverage': 'supported', 'separator': separator}
        if any(x in argv for x in ('>', '>>', '<', '<<', '&', '(', ')')) or any('$(' in x or '`' in x for x in argv):
            operation['coverage'] = 'opaque-shell-syntax'
        elif exe == 'cd' and len(argv) == 2 and literal(argv[1]):
            cwd = posixpath.normpath(posixpath.join(cwd, argv[1]))
            operation['category'] = 'repository discovery'
        elif exe in ('pwd', 'ls', 'tree', 'stat'):
            operation['category'] = 'repository discovery'
        elif exe in ('rg', 'grep', 'egrep', 'fgrep', 'find'):
            operation['category'] = 'repository discovery' if exe == 'find' or '--files' in argv else 'search'
            operation['repository_search'] = True
            if exe == 'find' and any(x in argv for x in ('-exec', '-execdir', '-ok')):
                operation['coverage'] = 'opaque-find-execution'
            operation['search_scope'] = argv[1:]
        elif exe == 'git' and len(argv) > 1:
            operation['category'] = 'git/status/diff'
        elif exe in ('pytest', 'py.test') or (re.fullmatch(r'python(?:\d(?:\.\d+)?)?', exe)
                and '-m' in argv and argv[argv.index('-m') + 1:argv.index('-m') + 2] in (['unittest'], ['pytest'])):
            operation['category'] = 'test execution'
        elif exe == 'cat':
            operands = [x for x in argv[1:] if not x.startswith('-')]
            allowed = all(not x.startswith('-') or x in ('-n', '-b', '-s', '-A', '-v', '-E', '-T', '--') for x in argv[1:])
            if operands and allowed and all(literal(x) for x in operands):
                operation['category'] = 'file inspection'
                operation['read_requests'] = [{'path': normalized(x, cwd), 'range': None} for x in operands]
            elif not operands and separator == '|':
                operation['category'] = 'other'
            else:
                operation['coverage'] = 'unsupported-cat-operands'
        elif exe == 'sed' and len(argv) >= 4 and argv[1] == '-n':
            match = re.fullmatch(r'(\d+)(?:,(\d+))?p', argv[2])
            if match and all(literal(x) for x in argv[3:]):
                operation['category'] = 'file inspection'
                interval = [int(match[1]), int(match[2] or match[1])]
                operation['read_requests'] = [{'path': normalized(x, cwd), 'range': interval} for x in argv[3:]]
            else:
                operation['coverage'] = 'unsupported-sed-expression'
        elif exe in ('head', 'tail'):
            # Support -NUMBER / -n NUMBER; a pipeline filter with no files is not a file read.
            operands, remaining = [], argv[1:]
            if remaining and re.fullmatch(r'-\d+', remaining[0]):
                remaining = remaining[1:]
            elif len(remaining) >= 2 and remaining[0] == '-n' and remaining[1].isdigit():
                remaining = remaining[2:]
            if all(literal(x) and not x.startswith('-') for x in remaining):
                operands = remaining
                if operands:
                    operation['category'] = 'file inspection'
                    operation['read_requests'] = [{'path': normalized(x, cwd), 'range': None} for x in operands]
                elif separator != '|':
                    operation['coverage'] = 'stdin-source-unknown'
            else:
                operation['coverage'] = 'unsupported-head-tail-options'
        elif exe in ('apply_patch', 'patch') or (exe == 'sed' and any(x.startswith('-i') for x in argv[1:])):
            operation['category'] = 'editing'
        elif exe in ('make', 'cmake', 'pip', 'pip3', 'uv') or (exe in ('npm', 'yarn', 'pnpm') and len(argv) > 1 and argv[1] in ('install', 'ci', 'build')):
            operation['category'] = 'build/setup'
        elif exe in ('true', 'false', 'echo', 'printf'):
            pass
        else:
            operation['coverage'] = 'opaque-program'
        if separator in ('&&', '||'):
            operation['coverage'] = 'conditional-execution'
        if operation['coverage'] != 'supported':
            operation['read_requests'] = []
            operation['repository_search'] = False
            unknown.append({'argv': argv, 'reason': operation['coverage']})
        for request in operation['read_requests']:
            request['scope'] = 'skill' if request['path'] == SKILL_PATH else ('repository' if not request['path'].startswith('/') else 'external')
        operations.append(operation)
    return operations, unknown


def analyze_actions(items, timing_by_line=None):
    """items: chronological (event line, item) pairs, deduplicated by caller."""
    trajectory, reads, unknown, scopes = [], [], [], []
    category_counts = Counter()
    first_edit, first_test = None, None
    shell_count = search_count = test_count = edit_count = skill_loads = 0
    repo_tool_count = 0
    for ordinal, (line, item) in enumerate(items, 1):
        kind = item.get('type')
        action = {'ordinal': ordinal, 'line_number': line, 'item_id': item.get('id'),
                  'type': kind, 'operations': [], 'categories': [], 'received_seconds': None}
        if timing_by_line:
            action['received_seconds'] = timing_by_line.get(line)
        if kind == 'command_execution':
            shell_count += 1
            action['command'] = item.get('command')
            action['exit_code'] = item.get('exit_code')
            operations, unsupported = shell_operations(item.get('command', ''))
            action['operations'] = operations
            unknown += unsupported
            for operation in operations:
                category_counts[operation['category']] += 1
                search_count += operation['repository_search']
                if operation['repository_search']:
                    scopes.append(operation['argv'])
                if operation['category'] == 'test execution' and operation['coverage'] == 'supported':
                    test_count += 1
                    first_test = first_test or action
                if operation['category'] == 'editing':
                    edit_count += 1
                    first_edit = first_edit or action
                for request in operation['read_requests']:
                    request = dict(request, ordinal=ordinal, item_id=item.get('id'))
                    reads.append(request)
                    if request['scope'] == 'skill':
                        skill_loads += 1
            action['categories'] = sorted({o['category'] for o in operations})
            # Test counts are only taken from tool output, never from prose/filenames.
            output = item.get('aggregated_output', item.get('output', '')) or ''
            if any(o['category'] == 'test execution' for o in operations):
                action['unittest_reported_counts'] = [int(x) for x in re.findall(r'Ran (\d+) tests? in [0-9.]+s', output)]
            action['skill_content_observed'] = 'name: efficient-coding' in output and 'Optimize for correctness first' in output
            action['output_characters'] = len(output)
        elif kind == 'file_change':
            action['categories'] = ['editing']
            category_counts['editing'] += 1
            edit_count += 1
            first_edit = first_edit or action
            action['changed_paths'] = [normalized(c['path']) for c in item.get('changes', []) if isinstance(c.get('path'), str)]
        elif kind in ('file_read', 'read_file') and isinstance(item.get('path'), str):
            path = normalized(item['path'])
            scope = 'skill' if path == SKILL_PATH else ('repository' if not path.startswith('/') else 'external')
            reads.append({'path': path, 'range': None, 'scope': scope, 'ordinal': ordinal, 'item_id': item.get('id')})
            skill_loads += scope == 'skill'
            action['categories'] = ['file inspection']
            category_counts['file inspection'] += 1
        else:
            action['categories'] = ['other']
            category_counts['other'] += 1
            unknown.append({'item_type': kind, 'reason': 'unsupported-structured-tool'})
        action['skill_only'] = bool(action['operations']) and all(
            o['read_requests'] and all(r['scope'] == 'skill' for r in o['read_requests']) for o in action['operations'])
        if kind in ('file_read', 'read_file') and isinstance(item.get('path'), str):
            action['skill_only'] = normalized(item['path']) == SKILL_PATH
        repo_tool_count += not action['skill_only']
        trajectory.append(action)
    repository_reads = [r for r in reads if r['scope'] == 'repository']
    counts = Counter(r['path'] for r in repository_reads)
    def before(action):
        return None if action is None else sum(a['ordinal'] < action['ordinal'] for a in trajectory)
    metrics = {
        'repository_search_commands': search_count if not unknown else None,
        'observed_repository_search_commands': search_count,
        'test_commands': test_count if not unknown else None,
        'test_runs': test_count if not unknown else None,
        'observed_test_executions': test_count,
        'file_read_operations': sum(bool(o['read_requests']) for a in trajectory for o in a['operations']) + sum(a['type'] in ('file_read', 'read_file') and bool(a.get('categories') == ['file inspection']) for a in trajectory),
        'total_file_reads': len(reads),
        'repository_file_reads': len(repository_reads),
        'unique_files_inspected': len(counts),
        'repeated_file_reads': sum(n - 1 for n in counts.values()),
        'skill_loading_events': skill_loads,
        'tool_items_excluding_skill_loading': repo_tool_count,
        'edit_operations': edit_count,
        'shell_operations': sum(len(a['operations']) for a in trajectory),
        'time_until_first_edit_seconds': first_edit['received_seconds'] if first_edit else None,
        'time_until_first_test_seconds': first_test['received_seconds'] if first_test else None,
        'tool_items_before_first_edit': before(first_edit),
        'tokens_before_first_edit': None,
        'file_read_metric_scope': 'explicit named content-inspection requests; includes Skill in total, repository only in unique/repeated',
        'command_classification_complete': not unknown,
    }
    return metrics, {'schema_version': ANALYSIS_VERSION, 'actions': trajectory,
                     'file_reads': reads, 'repository_read_counts': dict(counts),
                     'search_commands': scopes, 'category_counts': dict(category_counts),
                     'unclassified_operations': unknown}
