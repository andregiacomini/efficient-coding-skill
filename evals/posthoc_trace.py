"""Conservative observable-action analysis. Never reads reasoning/agent-message text."""
import ast
import posixpath
import re
import shlex
from collections import Counter

SKILL_PATH = '/root/.agents/skills/efficient-coding/SKILL.md'
ANALYSIS_VERSION = 5
ANALYSIS_REVISION = "5.0"


def normalized(path, cwd='/workspace'):
    absolute = posixpath.normpath(path if path.startswith('/') else posixpath.join(cwd, path))
    return absolute[len('/workspace/'):] if absolute.startswith('/workspace/') else absolute


def literal(path):
    return bool(path) and not any(c in path for c in '$`*?[]{}<>') and path != '-'


def python_operations(source, argv, cwd, test_entrypoints):
    """Statically recognize a deliberately small Python subset; never execute code.

    Imports/runtime calls are not source reads. Literal file inspection, regex
    searches, test entrypoints and literal subprocess commands are observable.
    Unknown control flow/calls stay opaque, including unevaluated function bodies.
    """
    base = {'argv': argv, 'category': 'behavior inspection', 'repository_search': False,
            'read_requests': [], 'coverage': 'supported', 'separator': None}
    operations, aliases, values, uncertain, bound_lines = [], {}, {}, [], {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [dict(base, coverage='unparseable-python')]
    if any(isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.AsyncFor,
                          ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
                          ast.IfExp, ast.Lambda, ast.BoolOp, ast.Raise)) for n in ast.walk(tree)):
        return [dict(base, coverage='python-control-flow')]
    def name(node):
        if isinstance(node, ast.Name): return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            parent = name(node.value)
            return parent + '.' + node.attr if parent else None
        return None
    def value(node):
        if isinstance(node, ast.Name): return values.get(node.id) if getattr(node,'lineno',0)>=bound_lines.get(node.id,0) else None
        try: return ast.literal_eval(node)
        except (ValueError, TypeError): pass
        if isinstance(node, ast.Call):
            callee = name(node.func)
            if callee in ('pathlib.Path', 'Path') and len(node.args) == 1:
                return value(node.args[0])
            if isinstance(node.func, ast.Attribute):
                owner = node.func.value
                if node.func.attr in ('read_text', 'read_bytes', 'read', 'readlines'):
                    path = read_path(node)
                    if path: return {'content_path': path}
                if node.func.attr in ('splitlines', 'split'):
                    return value(owner)
        return None
    def read_path(node):
        if not isinstance(node.func, ast.Attribute): return None
        owner = node.func.value; method = node.func.attr
        if method in ('read_text', 'read_bytes'):
            path = value(owner)
            return path if isinstance(path, str) and literal(path) else None
        if method in ('read', 'readlines'):
            if isinstance(owner, ast.Call) and name(owner.func) in ('open','builtins.open'):
                args = [value(a) for a in owner.args]
                mode=next((value(k.value) for k in owner.keywords if k.arg=='mode'),args[1] if len(args)>1 else 'r')
                if mode not in ('r','rb','rt'): return None
                if args and isinstance(args[0], str) and literal(args[0]) and (len(args)==1 or args[1] in ('r','rb','rt')):
                    return args[0]
            handle = value(owner)
            if isinstance(handle, dict): return handle.get('file_handle')
        return None
    def add(category, **kw): operations.append(dict(base, category=category, **kw))
    # Bind only straight-line literals/import aliases. No filesystem consulted.
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names: aliases[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names: aliases[a.asname or a.name] = node.module + '.' + a.name
        elif isinstance(node, ast.Assign):
            v=value(node.value); target=node.targets[0] if len(node.targets)==1 else None
            if isinstance(target, ast.Name):
                if target.id in bound_lines: return [dict(base,coverage='python-rebinding')]
                bound_lines[target.id]=node.lineno
                if v is not None: values[target.id]=v
                resolved=name(node.value)
                if resolved: aliases[target.id]=resolved
            elif isinstance(target, ast.Attribute) and name(target)=='sys.argv': values['sys.argv']=v
        elif isinstance(node, ast.With):
            for context in node.items:
                call=context.context_expr
                if isinstance(call,ast.Call) and name(call.func)=='open' and call.args and isinstance(context.optional_vars,ast.Name):
                    path=value(call.args[0]); mode=next((value(k.value) for k in call.keywords if k.arg=='mode'),value(call.args[1]) if len(call.args)>1 else 'r')
                    if isinstance(path,str) and literal(path) and mode in ('r','rb','rt'):
                        values[context.optional_vars.id]={'file_handle':path}
    def observable_nodes(node):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            for child in ast.walk(node):
                if isinstance(child,ast.Call) and not (name(child.func) in ('print','str','repr','len') or (name(child.func) or '').startswith('django.')):
                    uncertain.append('unexecuted-or-dynamic-python-body')
            return
        yield node
        for child in ast.iter_child_nodes(node): yield from observable_nodes(child)
    for node in observable_nodes(tree):
        if not isinstance(node, ast.Call): continue
        callee=name(node.func)
        method=node.func.attr if isinstance(node.func,ast.Attribute) else None
        path=read_path(node)
        if path:
            add('file inspection', read_requests=[{'path':normalized(path,cwd),'range':None}]); continue
        if callee in ('open','builtins.open'):
            # Opening alone is not content inspection; the supported read above counts it.
            args=[value(a) for a in node.args]
            mode=next((value(k.value) for k in node.keywords if k.arg=='mode'),args[1] if len(args)>1 else 'r')
            if mode not in ('r','rb','rt'): uncertain.append('writing-python-open')
            if not args or not isinstance(args[0],str) or not literal(args[0]) or (len(args)>1 and args[1] not in ('r','rb','rt')):
                uncertain.append('dynamic-or-writing-python-open')
            continue
        if callee in ('pathlib.Path','Path','print','str','repr','len','sys.path.insert','sys.path.append'):
            continue
        if callee in ('re.search','re.findall','re.finditer','re.match','re.fullmatch'):
            data=value(node.args[1]) if len(node.args)>1 else None
            if isinstance(data,dict) and data.get('content_path'):
                add('search',repository_search=True,search_scope=[data['content_path']]); continue
            uncertain.append('python-regex-source-unknown'); continue
        if callee in ('os.listdir',) or method in ('glob','rglob'):
            directory=value(node.args[0]) if callee=='os.listdir' and node.args else value(node.func.value)
            if isinstance(directory,str) and literal(directory):
                add('repository discovery',repository_search=True,search_scope=[directory]);continue
            uncertain.append('dynamic-python-search');continue
        if callee in ('subprocess.run','subprocess.check_output','subprocess.check_call'):
            args=value(node.args[0]) if node.args else None
            if isinstance(args,list) and all(isinstance(x,str) for x in args) and not any(k.arg in ('shell','cwd') for k in node.keywords):
                ops,unknown=shell_operations(shlex.join(args),test_entrypoints=test_entrypoints)
                operations.extend(ops);uncertain.extend(unknown);continue
            uncertain.append('dynamic-python-subprocess');continue
        if callee in ('pytest.main','unittest.main','runtests.django_tests'):
            add('test execution',python_test_entrypoint=callee);continue
        if callee in ('runpy.run_path','runpy.run_module'):
            target=value(node.args[0]) if node.args else None
            if isinstance(target,str) and ((callee=='runpy.run_path' and normalized(target,cwd) in (test_entrypoints or [])) or (callee=='runpy.run_module' and target in ('unittest','pytest'))):
                add('test execution',python_test_entrypoint=target,python_test_argv=values.get('sys.argv'));continue
            uncertain.append('unknown-python-entrypoint');continue
        if callee and callee.startswith('django.'):
            continue  # Runtime behavior probe; implicit imports/SQL are not source inspection.
        if method in ('splitlines','split','strip') and isinstance(value(node.func.value),dict): continue
        uncertain.append('unsupported-python-call:'+str(callee))
    if not operations: operations=[base]
    if uncertain: operations.append(dict(base,coverage='opaque-python',python_unknown=uncertain))
    return operations


def scoped_operations(operations):
    unknown=[]
    for op in operations:
        if op['coverage']!='supported': unknown.append({'argv':op['argv'],'reason':op['coverage']})
        for request in op['read_requests']:
            request['scope']='skill' if request['path']==SKILL_PATH else ('repository' if not request['path'].startswith('/') else 'external')
    return operations,unknown


def shell_segments(command):
    """Separate only unquoted shell operators; retain quoted regex/operator arguments."""
    parts, start, separator, quote, escaped, unsafe = [], 0, None, None, False, False
    i = 0
    while i < len(command):
        c = command[i]
        if escaped:
            escaped = False; i += 1; continue
        if c == '\\' and quote != "'":
            escaped = True; i += 1; continue
        if quote:
            if c == quote: quote = None
            i += 1; continue
        if c in "'\"": quote = c; i += 1; continue
        if c in '<>()`' or (c == '&' and command[i:i+2] != '&&'):
            unsafe = True
        operator = next((op for op in ('&&','||',';','|','\n') if command.startswith(op, i)), None)
        if operator:
            raw = command[start:i].strip()
            if raw: parts.append((shlex.split(raw), separator, unsafe))
            separator = ';' if operator == '\n' else operator
            i += len(operator); start = i; unsafe = False; continue
        i += 1
    raw = command[start:].strip()
    if raw: parts.append((shlex.split(raw), separator, unsafe))
    return parts


def conditional_execution(segments, exit_code):
    """Prove invocation, never infer it from output volume or assistant prose."""
    pure_and_success = (type(exit_code) is int and exit_code == 0 and len(segments) > 1
                        and all(sep == '&&' and not unsafe for _,sep,unsafe in segments[1:])
                        and not segments[0][2])
    executed, previous = [], None
    for index, (argv, separator, unsafe) in enumerate(segments):
        if separator in (None, ';', '|'):
            invocation = True
        elif pure_and_success:
            invocation = True
        elif separator == '&&':
            invocation = previous == 0 if previous is not None else None
        elif separator == '||':
            invocation = previous != 0 if previous is not None else None
        else:
            invocation = None
        executed.append(invocation)
        if invocation is True:
            previous = (0 if argv == ['true'] else 1 if argv == ['false'] else None)
        elif invocation is None:
            previous = None
        # A skipped command preserves the AND/OR list's previous status.
    return executed


def black_operation(argv, operation, output, exit_code, cwd, isolated=False):
    exe = posixpath.basename(argv[0])
    args = argv[3:] if re.fullmatch(r'python(?:\d(?:\.\d+)?)?',exe) and argv[1:3] == ['-m','black'] else argv[1:]
    if '--version' in args:
        operation['category'] = 'formatter availability'
    elif '--check' in args or '--diff' in args:
        operation['category'] = 'format validation'
        targets = []; skip = False
        for arg in args:
            if skip: skip = False; continue
            if arg in ('--line-length','-l','--target-version','-t','--config','--include','--exclude','--extend-exclude','--force-exclude'):
                skip = True; continue
            if arg.startswith('-'): continue
            if literal(arg): targets.append(normalized(arg,cwd))
            else: operation['coverage'] = 'dynamic-format-target'
        operation['validation_targets'] = targets
    elif isolated and type(exit_code) is int and exit_code != 0 and re.search(r'(?:No module named [\'\"]?black|black: command not found)',output or ''):
        operation['category'] = 'failed formatting attempt'
        operation['no_edit_evidence'] = 'formatter failed to load'
    else:
        operation['category'] = 'formatting'
        operation['coverage'] = 'format-edit-outcome-unknown'
    return operation


def shell_operations(command, test_entrypoints=None, exit_code=None, output=None):
    """Split supported shell syntax without evaluating it. Opaque programs stay opaque."""
    if not isinstance(command, str):
        return [], ['Missing structured command string']
    try:
        outer = shlex.split(command)
        if len(outer) == 3 and posixpath.basename(outer[0]) in ('sh', 'bash', 'zsh') and outer[1] in ('-c', '-lc'):
            command = outer[2]
        heredoc = re.fullmatch(r"([^\n]+?)\s*<<\s*(['\"]?)([A-Za-z_][A-Za-z_0-9]*)\2\s*\n(.*)\n\3\s*", command, re.S)
        if heredoc:
            if not heredoc.group(2) and any(c in heredoc.group(4) for c in ('$','`')):
                return [], [{'reason':'expanding-heredoc'}]
            prefix=shlex.split(heredoc.group(1))
            if len(prefix)==2 and re.fullmatch(r'python(?:\d(?:\.\d+)?)?',posixpath.basename(prefix[0])) and prefix[1]=='-':
                return scoped_operations(python_operations(heredoc.group(4),prefix,'/workspace',test_entrypoints))
        segments = shell_segments(command)
    except ValueError:
        return [], ['Unparseable shell quoting']
    operations, unknown, cwd = [], [], '/workspace'
    invocations = conditional_execution(segments, exit_code)
    for segment_index, (argv, separator, unsafe) in enumerate(segments):
        if not argv:
            continue
        exe = posixpath.basename(argv[0])
        invocation = invocations[segment_index]
        operation = {'argv': argv, 'category': 'other', 'repository_search': False,
                     'read_requests': [], 'coverage': 'supported', 'separator': separator}
        if invocation is False:
            operations.append(dict(operation, category='skipped command', execution='proven-skipped'))
            continue
        operation['execution'] = 'proven-executed' if invocation is True else 'unknown'
        if re.fullmatch(r'python(?:\d(?:\.\d+)?)?',exe) and len(argv)==3 and argv[1]=='-c' and invocation is True:
            ops=python_operations(argv[2],argv,cwd,test_entrypoints)
            operations.extend(ops); unknown.extend(scoped_operations(ops)[1]); continue
        if unsafe or any(x in argv for x in ('>', '>>', '<', '<<', '&', '(', ')')) or any('$(' in x or '`' in x for x in argv):
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
        elif re.fullmatch(r'python(?:\d(?:\.\d+)?)?', exe) and len(argv) > 1 and literal(argv[1]) and normalized(argv[1], cwd) in (test_entrypoints or []):
            operation['category'] = 'test execution'
        elif exe == 'black' or (re.fullmatch(r'python(?:\d(?:\.\d+)?)?',exe) and argv[1:3] == ['-m','black']):
            operation = black_operation(argv, operation, output, exit_code, cwd, isolated=len(segments)==1)
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
            rest = argv[2:]; expressions = []
            while rest and rest[0] == '-e' and len(rest) >= 2:
                expressions.append(rest[1]); rest = rest[2:]
            if not expressions and rest:
                expressions.append(rest[0]); rest = rest[1:]
            matches = [re.fullmatch(r'(\d+)\s*(?:,\s*(\d+))?\s*p', part.strip())
                       for expr in expressions for part in expr.split(';') if part.strip()]
            if matches and all(matches) and rest and all(literal(x) and not x.startswith('-') for x in rest):
                operation['category'] = 'file inspection'
                intervals = [[int(m[1]), int(m[2] or m[1])] for m in matches]
                operation['read_requests'] = [{'path': normalized(x, cwd), 'range': intervals[0] if len(intervals)==1 else None, 'ranges': intervals} for x in rest]
            elif (expressions and len(expressions) == 1 and re.fullmatch(r'\d+\s*,\s*[A-Za-z]+\s+p',expressions[0].strip())
                  and 'sed: -e expression #1' in (output or '') and 'unexpected' in (output or '')
                  and type(exit_code) is int and exit_code != 0 and segment_index == len(segments)-1):
                operation['category'] = 'failed inspection'
                operation['failure_evidence'] = 'literal malformed range; sed expression parse error before file inspection'
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
        if invocation is None:
            operation['coverage'] = 'conditional-execution'
        if operation['coverage'] != 'supported':
            operation['read_requests'] = []
            operation['repository_search'] = False
            unknown.append({'argv': argv, 'reason': operation['coverage']})
        for request in operation['read_requests']:
            request['scope'] = 'skill' if request['path'] == SKILL_PATH else ('repository' if not request['path'].startswith('/') else 'external')
        operations.append(operation)
    return operations, unknown


def completion_metrics(actions, first_success, source_roots, test_entrypoints, regression_test_ids=None):
    """Count observable completed edit items; revalidation requires fresh passing tests.

    Hygiene checks are not semantic revalidation. Formatting checks are validation
    attempts, but do not establish production/test behavioral correctness.
    """
    def code_kind(path):
        if any(path.startswith(r.rstrip('/')+'/') for r in (source_roots or [])): return 'production'
        if path.startswith('tests/') or path.startswith('test/'): return 'test'
        return 'other'
    edits, tests, validations = [], [], []
    ambiguous_edit = False
    ambiguous_validation = False
    for action in actions:
        if any(op['coverage']!='supported' for op in action['operations']):
            ambiguous_edit = True
            ambiguous_validation = True
        if action['type'] == 'file_change':
            if action.get('status') == 'failed': continue
            if not action.get('completed_line_number'):
                ambiguous_edit = True; continue
            paths = [p for p in action.get('changed_paths',[]) if not p.startswith('/')]
            if paths:
                edits.append(dict(action, edit_paths=paths))
        elif 'editing' in action['categories'] or 'formatting' in action['categories']:
            # A shell writer without structured changed-path evidence can affect the
            # final edit boundary. Do not silently assume it changed no files.
            ambiguous_edit = True
        test_ops = [o for o in action['operations'] if o['category']=='test execution' and o['coverage']=='supported']
        format_ops = [o for o in action['operations'] if o['category']=='format validation' and o['coverage']=='supported']
        if (test_ops or format_ops) and action.get('completed_line_number'):
            output = action.get('validation_output','')
            passed = action.get('exit_code') == 0 and 'FAILED (' not in output
            if test_ops:
                passed = passed and bool(action.get('unittest_reported_counts')) and '\nOK' in output
                tests.append(dict(action, test_ops=test_ops, passed=passed))
            validations.append(dict(action, passed=passed, validation_kind='test' if test_ops else 'format'))
    edits.sort(key=lambda a:a['completed_line_number'])
    tests.sort(key=lambda a:a['completed_line_number'])
    validations.sort(key=lambda a:a['completed_line_number'])
    last_edit = edits[-1] if edits else None
    last_test = tests[-1] if tests else None
    last_validation = validations[-1] if validations else None
    def stamp(event): return event.get('completed_seconds') if event else None
    def after(boundary):
        if not boundary or ambiguous_edit: return None
        overlap = [e for e in edits if e['line_number'] <= boundary['completed_line_number'] < e['completed_line_number']]
        if overlap: return None
        return [e for e in edits if e['line_number'] > boundary['completed_line_number']]
    after_test, after_validation = after(last_test), after(last_validation)
    after_success = after(first_success)
    def last_kind(kind): return next((e for e in reversed(edits) if any(code_kind(p)==kind for p in e['edit_paths'])),None)
    def relevant(test, paths):
        # Full-module discovery covers changed prefetch test files. A targeted
        # class cannot prove coverage of arbitrary edits elsewhere in that file.
        targets = [arg for op in test['test_ops'] for arg in op['argv'][2:] if not arg.startswith('-')]
        full_prefetch = 'prefetch_related' in targets
        observed = test.get('targeted_regression_results') or []
        regression_present = (bool(regression_test_ids) and len(observed)==len(regression_test_ids)
                         and {name for name,status in observed}==set(regression_test_ids))
        for path in paths:
            kind = code_kind(path)
            if kind == 'test':
                if not path.startswith('tests/prefetch_related/') or not full_prefetch: return None
            elif kind == 'production':
                if not full_prefetch and not regression_present: return None
            else:
                return None
        return True
    def subsequent(edit, passed_only=False):
        if not edit or ambiguous_edit or ambiguous_validation: return None
        paths = [p for p in edit['edit_paths'] if code_kind(p)!='other']
        if not paths: return None
        later = [t for t in tests if t['line_number'] > edit['completed_line_number']]
        for test in later:
            if relevant(test, paths) is True and (not passed_only or test['passed']): return True
        if any(t['line_number'] <= edit['completed_line_number'] < t['completed_line_number'] for t in tests): return None
        if later and any(relevant(t,paths) is None for t in later): return None
        return False
    production, test_edit = last_kind('production'), last_kind('test')
    flags = {}
    for label,kind in [('repository',None),('production','production'),('test','test')]:
        flags[label+'_edited_after_last_test'] = (None if after_test is None else
             any(kind is None or any(code_kind(p)==kind for p in e['edit_paths']) for e in after_test))
    return {
        'last_edit_time_seconds': None if ambiguous_edit else stamp(last_edit),
        'last_edit_started_seconds': None if ambiguous_edit or not last_edit else last_edit['received_seconds'],
        'last_edit_item_id': None if ambiguous_edit or not last_edit else last_edit['item_id'],
        'last_edit_paths': None if ambiguous_edit else last_edit['edit_paths'] if last_edit else [],
        'last_test_time_seconds': None if ambiguous_validation else stamp(last_test),
        'last_validation_time_seconds': None if ambiguous_validation else stamp(last_validation),
        'last_validation_kind': last_validation['validation_kind'] if last_validation else None,
        'last_validation_passed': last_validation['passed'] if last_validation else None,
        'edits_after_first_targeted_success': len(after_success) if after_success is not None else None,
        'edits_after_last_test_execution': len(after_test) if after_test is not None else None,
        'edits_after_last_validation': len(after_validation) if after_validation is not None else None,
        **flags,
        'validation_after_final_production_edit': subsequent(production),
        'validation_after_final_test_file_edit': subsequent(test_edit),
        'final_production_edit_revalidated': subsequent(production,True),
        'final_test_file_edit_revalidated': subsequent(test_edit,True),
        'final_edit_revalidated': subsequent(last_edit,True),
        'tool_calls_between_first_success_and_final_edit': (sum(a['line_number']>first_success['completed_line_number'] and a['line_number']<last_edit['line_number'] for a in actions) if first_success and last_edit and not ambiguous_edit else None),
        'tool_calls_after_final_edit': (sum(a['line_number']>last_edit['completed_line_number'] for a in actions) if last_edit and not ambiguous_edit else None),
        'completion_edit_coverage_complete': not ambiguous_edit,
    }


def analyze_actions(items, timing_by_line=None, source_roots=None, test_entrypoints=None,
                    regression_test_ids=None, completion_by_id=None):
    """items: chronological (event line, item) pairs, deduplicated by caller."""
    trajectory, reads, unknown, scopes = [], [], [], []
    category_counts = Counter()
    first_edit, first_test, first_success = None, None, None
    shell_count = search_count = test_count = edit_count = skill_loads = 0
    repo_tool_count = 0
    for ordinal, (line, item) in enumerate(items, 1):
        kind = item.get('type')
        action = {'ordinal': ordinal, 'line_number': line, 'item_id': item.get('id'),
                  'type': kind, 'status': item.get('status'), 'operations': [], 'categories': [], 'received_seconds': None}
        if timing_by_line:
            action['received_seconds'] = timing_by_line.get(line)
        completed_line=(completion_by_id or {}).get(item.get('id'))
        action['completed_line_number']=completed_line
        action['completed_seconds']=(timing_by_line or {}).get(completed_line)
        if kind == 'command_execution':
            shell_count += 1
            action['command'] = item.get('command')
            action['exit_code'] = item.get('exit_code')
            operations, unsupported = shell_operations(item.get('command', ''), test_entrypoints=test_entrypoints,
                exit_code=item.get('exit_code') if completed_line else None,
                output=item.get('aggregated_output', item.get('output', '')))
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
                target_results=[]
                current=None
                for result_line in output.splitlines():
                    match=re.match(r'^(test\w+) \(([\w.]+)\)(.*)',result_line)
                    if match: current=match[2]+'.'+match[1]
                    if current and ' ... ' in result_line:
                        status=result_line.rsplit(' ... ',1)[1].strip()
                        if current in (regression_test_ids or []): target_results.append((current,status))
                        current=None
                action['targeted_regression_results']=target_results
                if (regression_test_ids and completed_line and action['unittest_reported_counts']
                        and len(target_results)==len(regression_test_ids)
                        and {t for t,status in target_results}==set(regression_test_ids)
                        and all(status=='ok' for t,status in target_results)):
                    if first_success is None or completed_line<first_success['completed_line_number']: first_success=action
            action['skill_content_observed'] = 'name: efficient-coding' in output and 'Optimize for correctness first' in output
            action['output_characters'] = len(output)
            action['validation_output'] = output if any(o['category']=='test execution' for o in operations) else ''
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
    first_search = next((a for a in trajectory if any(o.get('repository_search') for o in a['operations'])), None)
    first_read = next((a for a in trajectory if any(r['ordinal'] == a['ordinal'] for r in reads)), None)
    first_repository_read = next((a for a in trajectory if any(r['ordinal'] == a['ordinal'] for r in repository_reads)), None)
    pre_edit_reads = [r for r in repository_reads if first_edit and r['ordinal'] < first_edit['ordinal']]
    source_files = ({r['path'] for r in pre_edit_reads
                     if any(r['path'].startswith(root.rstrip('/') + '/') for root in source_roots)}
                    if source_roots is not None else None)
    pre_edit_searches = (sum(o.get('repository_search', False) for a in trajectory
                            if a['ordinal'] < first_edit['ordinal'] for o in a['operations'])
                         if first_edit else None)
    pre_edit_actions=[a for a in trajectory if first_edit and a['ordinal']<first_edit['ordinal']]
    pre_unknown=any(o['coverage']!='supported' for a in pre_edit_actions for o in a['operations']) or any(a['type'] not in ('command_execution','file_change','file_read','read_file') for a in pre_edit_actions)
    post_actions=([a for a in trajectory if a['line_number']>first_success['completed_line_number']] if first_success else [])
    post_unknown=any(o['coverage']!='supported' for a in post_actions for o in a['operations']) or any(a['type'] not in ('command_execution','file_change','file_read','read_file') for a in post_actions)
    post_ordinals={a['ordinal'] for a in post_actions}
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
        'time_until_first_repository_search_seconds': first_search['received_seconds'] if first_search else None,
        'time_until_first_file_read_seconds': first_read['received_seconds'] if first_read else None,
        'time_until_first_repository_file_read_seconds': first_repository_read['received_seconds'] if first_repository_read else None,
        'unique_source_files_before_first_edit': len(source_files) if source_files is not None and first_edit and not pre_unknown else None,
        'searches_before_first_edit': pre_edit_searches if first_edit and not pre_unknown else None,
        'unique_repository_files_before_first_edit': len({r['path'] for r in pre_edit_reads}) if first_edit and not pre_unknown else None,
        'time_until_first_targeted_success_seconds': first_success['completed_seconds'] if first_success else None,
        'first_targeted_success_item_id': first_success['item_id'] if first_success else None,
        'post_first_success_tool_calls': len(post_actions) if first_success else None,
        'post_first_success_searches': sum(o.get('repository_search',False) for a in post_actions for o in a['operations']) if first_success and not post_unknown else None,
        'post_first_success_file_reads': sum(r['ordinal'] in post_ordinals for r in repository_reads) if first_success and not post_unknown else None,
        'post_first_success_test_executions': sum(o['category']=='test execution' and o['coverage']=='supported' for a in post_actions for o in a['operations']) if first_success and not post_unknown else None,
        'observed_post_first_success_searches': sum(o.get('repository_search',False) for a in post_actions for o in a['operations']) if first_success else None,
        'observed_post_first_success_file_reads': sum(r['ordinal'] in post_ordinals for r in repository_reads) if first_success else None,
        'observed_post_first_success_test_executions': sum(o['category']=='test execution' and o['coverage']=='supported' for a in post_actions for o in a['operations']) if first_success else None,
        'tokens_before_first_edit': None,
        'file_read_metric_scope': 'explicit named content-inspection requests; includes Skill in total, repository only in unique/repeated',
        'command_classification_complete': not unknown,
        'analysis_revision': ANALYSIS_REVISION,
    }
    metrics.update(completion_metrics(trajectory,first_success,source_roots,test_entrypoints,regression_test_ids))
    for action in trajectory: action.pop('validation_output',None)
    return metrics, {'schema_version': ANALYSIS_VERSION, 'actions': trajectory,
                     'file_reads': reads, 'repository_read_counts': dict(counts),
                     'search_commands': scopes, 'category_counts': dict(category_counts),
                     'unclassified_operations': unknown}
