# EVAL-002 candidate selection — official transplanted tests

Selected: **Luigi, bug 9**. All ten candidates below genuinely reproduced in two
independent regression invocations after the official BugsInPy test transplant.
Earlier pass/missing-node results were preliminary, non-benchmark-faithful checks
that omitted transplantation; they are preserved in separate earlier files and
are superseded for selection. No solving agent has run.

## Heuristic and eligibility

The same nine-point structural score is retained: source files (2 for >=100,
1 for >=30); physical LOC (2 for >=20,000, 1 for >=5,000); source directories
(2 for >=5, 1 for >=2); distinct direct project-module imports in the transplanted
test (2 for >=3, 1 for >=2); tests outside source (1). Counts are Python files under
`luigi/` or `lib/ansible/`, including in-tree vendored code and physical comments/
blank lines. Directory breadth and imports are proxies, not proven necessary reads.

Subtract 2 for an explicit application error/trace location, or 1 when the test/
failure strongly indicates a module or reporting API. Incidental logs of a
deliberate fixture exception do not identify the cause of a different assertion.
No gold-patch size, fixed application source or future diff is used.

A real, stable bug failure, practical runtime and no immediately obvious single
implementation location are hard selection gates. Scores rank structural signals;
they do not override these gates. A large rejected repository may score higher
than the selected candidate. Navigation difficulty remains a prediction to test.

| Candidate | Buggy commit | Python files / LOC / directories | Final score (penalty) | Official regression outcome | Decision |
| --- | --- | --- | --- | --- | --- |
| luigi-24 | `572fce617a3b8133983cdee2b2cc336a65af5abe` | 69 / 16,504 / 4 | 5/9 (-1) | 2 failed, 8 warnings; stable 2/2 | Rejected: test directly patches Spark subprocess arguments; one contribution module is obvious. |
| luigi-30 | `97fa4afea3748f0d714482d2c97990bb467bc9d1` | 56 / 15,157 / 3 | 3/9 (-2) | 2 failed, 4 warnings; stable 2/2 | Rejected: worker execution logs/trace explicitly expose the execution area. |
| luigi-5 | `45b5711d1900184ccd66c65216d28c0d69d10d4a` | 84 / 24,893 / 4 | 5/9 (-1) | 2 failed, 31 warnings; stable 2/2 | Rejected: utility decorator/MRO assertions strongly identify one utility module. |
| ansible-3 | `70219df9056ffb1e2766f572fbe71f7a1800c9f5` | 450 / 102,658 / 71 | 7/9 (-1) | 1 failed, 53 passed; stable 2/2 | Rejected: distribution mock targets identify one facts implementation; size does not add navigation. |
| ansible-9 | `9276dd2007a73172ed99ab5a56cded4298d3cd2b` | 5484 / 1,688,098 / 557 | 7/9 (-1) | 2 failed, 11 passed; stable 2/2 | Rejected: command assertions identify one subscription module despite the huge tree. |
| luigi-7 | `dd1f2ce0061e7787166522a3c75339ba4755dd2c` | 85 / 24,420 / 4 | 5/9 (-1) | 1 failed, 31 warnings; stable 2/2 | Rejected: direct scheduler API calls strongly identify the scheduler module. |
| luigi-21 | `b7768da963570bd2223d97c1035f811c2eaf30b4` | 70 / 16,848 / 4 | 4/9 (-2) | 1 failed, 2 warnings; stable 2/2 | Rejected: traceback gives the exact application line in interface.py. |
| ansible-4 | `d91658ec0c8434c82c3ef98bfe9eb4e1027a43a3` | 450 / 102,526 / 71 | 6/9 (-1) | 1 failed, 1 warning; stable 2/2 | Rejected: one CollectionSearch import and one method identify the implementation. |
| luigi-9 | `f7e0b7710fd8b12f27625b1efb62a8fde6e206c4` | 86 / 23,651 / 4 | 5/9 (-1) | 1 failed, 23 warnings; stable 2/2 | SELECTED: retry execution and historical reporting cross a behavior boundary; the failing key is reported at a test line. |
| luigi-14 | `f7219c38121098d464011a094156d99b5b320362` | 82 / 21,739 / 4 | 4/9 (-2) | 1 failed, 3 warnings; stable 2/2 | Rejected: traceback gives the exact scheduler.py implementation line. |

## Why Luigi 9

The failure is `KeyError: 'ever_failed'` at the test assertion after two executions
of a task whose first run deliberately raises an exception. The test covers
completed status and failure history in an execution summary. Reporting, worker
state and task lifecycle are plausible inspection areas; that inference comes
from the test behavior/imports, not a reference solution. The first-run worker
trace is expected fixture behavior and does not pinpoint the cause of the summary
failure. We apply a one-point penalty because the reporting API is recognizable.

This differs from EVAL-001's focused XML-parser assertion: understanding the
observable result involves a retry/history sequence and a result consumed across
execution/reporting boundaries. It may still admit a short agent trajectory; no
claim of measured exploration difficulty or Skill advantage is made. The selected
candidate was reproduced twice in fresh containers, in 0.71 and 0.668 seconds
including container startup. The benchmark test itself reported 0.17 seconds.

Failing test:
`test/execution_summary_test.py::ExecutionSummaryTest::test_status_with_task_retry`.

## Benchmark-faithful preparation and isolation

Pinned BugsInPy revision: `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
The unmodified official `bugsinpy-checkout -p PROJECT -i BUG -v 0` helper performed
its normal fixed-test-to-buggy transplant. The only transport adaptation was a
local shallow mirror with the two required revisions instead of fetching full
upstream history; helper bytes and benchmark metadata were unchanged. Fixed
application files and fix-bearing commit messages remained confined to private
preparation storage and were never inspected or copied into solving snapshots.
Reference/gold patches were never read. Checkout stdout stayed private.

Official `bugsinpy-compile` and `bugsinpy-test` helpers ran in preparation-only
containers. Platform-specific dependency dumps were replaced by an explanatory
comment because pinned minimal dependencies were already installed in the runtime;
helper-created venv imports used those site-packages. Direct pytest runs verified
the actual exit code and repeated each regression twice. Wrapper exit zero is
not treated as proof of passing tests. This setup adaptation is explicit; the
application source/test transplantation remains faithful to the benchmark.

Python 3.8.20 is used instead of the dataset's 3.8.3; this patch-level deviation
is frozen for both conditions. Dependencies are pinned in
`EVAL-002-runtime/requirements.txt`. No benchmark package is installed separately,
so a future installed Luigi version cannot leak into the solver.

Each `preparation/EVAL-002-candidates/<candidate>/transplanted-candidate.json`
contains buggy-state metrics, exact relevant test commands, transplanted-file
hashes and repetition timings. `official-test-output.txt` and `reproduction-*.txt`
contain only buggy benchmark behavior. The earlier no-transplant outputs remain
separate. Candidate notes/logs/configuration are never mounted in solving containers.
The final selected snapshot is a new single-commit Git repository; it carries no
upstream or fixed commit objects, messages, references, remotes or alternates.
See [EVAL-002.md](EVAL-002.md) for the verified solving configuration and commands.
