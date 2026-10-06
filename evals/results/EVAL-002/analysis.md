# EVAL-002 observable analysis

All six runs passed the independent frozen benchmark. Treatments performed fewer
repository search commands in every pair, but the same number of explicit
repository read requests. Median total tokens were 2.96% lower and mean total
tokens 7.27% lower with the Skill; S1 increased tokens while S2/S3 decreased them.
This is descriptive evidence from three pairs on one bug, not an established
causal or general efficiency benefit.

The [report](report.md) contains aggregate values, all individual metrics and
paired token differences. Sources here are the six saved `trajectory.json`
files, structured tool events, native usage and pytest output. Reasoning and
agent-message text, generated patch contents, known fixes and future versions
were not inspected. No source commands from the traces were executed by this
analysis.

## Search behavior

Repository-search counts include filename discovery and content searches. Simple
`pwd`/`ls` and Git commands are separate operations.

| Pair | Baseline searches | Skill searches | Observable scope |
| --- | ---: | ---: | --- |
| B1/S1 | 4 | 3 | B1 searched the Luigi directory and selected tests, then discovered tests and searched return-code references. S1 searched named summary/test/interface files. |
| B2/S2 | 3 | 2 | B2 used targeted filenames/content followed by a Python-file search across `test` and `luigi`. S2 used targeted filenames and one content search in the named summary source and test. |
| B3/S3 | 5 | 2 | B3 searched the named summary, both source/test directories, then test filenames and return-code references. S3 used targeted filenames and the named summary source/test. |

S runs consistently used fewer queries and narrower content-search targets.
Filename discovery still traverses the repository, and the trace does not
inventory every file scanned. Some additional baseline searches supported the
additional return-code validation; fewer searches need not mean that those
baseline operations were unnecessary.

## File exploration and repeated work

Every run explicitly inspected `AGENTS.md`, `luigi/execution_summary.py` and
`test/execution_summary_test.py`. B3 also inspected `luigi/retcodes.py` lines
65–110 while preparing broader validation.

| Run | Summary-source ranges | Summary-test ranges | Explicit repository requests | Unique repository targets | Repeated targets |
| --- | --- | --- | ---: | ---: | ---: |
| B1 | 1–290; 290–520 | 1050–1155; 20–100 | 5 | 3 | 2 |
| S1 | 1–115; 330–425 | 1–48; 1050–1140 | 5 | 3 | 2 |
| B2 | 1–280; 290–430 | 1000–1140; 20–55 | 5 | 3 | 2 |
| S2 | 30–108; 330–405 | 1080–1130; 1–48 | 5 | 3 | 2 |
| B3 | 1–300; 300–435 | 1010–1160; 1–110 | 6 | 4 | 2 |
| S3 | 1–108; 255–292; 332–415 | 1090–1130; 25–98 | 6 | 3 | 3 |

Treatments requested shorter source/test ranges in aggregate within each pair.
They did not reduce repository read-request counts. Distinct explicit targets
were unchanged in pairs 1/2 and one lower in pair 3. Median unique targets stayed
at 3, and median repository reads stayed at 5. The extra treatment read in the
headline explicit-read metric is the Skill itself.

Repeated-path counts are equal in pairs 1/2 and higher in S3. These requests
cover separate ranges; only B1/B3 share a single source boundary line between
requests. This is not evidence of redundant whole-file rereading. Multiple
ranges can occur within one compound tool command. No reduction in redundant
work is established from these counts, nor can legitimate validation reruns be
classified as wasted work solely because the command repeats.

The task remained localized despite the preparation hypothesis about wider
navigation. Three common explicit targets include an instruction file and a
test file; this does not exercise broad architecture discovery.

## Editing and validation

All six recorded one edit operation and one final modified application file,
`luigi/execution_summary.py`. Modified-path inventories, patch numstat and valid
untracked archives confirm capture. The patches were not manually reviewed, so
this analysis makes no claim about patch equivalence or relative code quality.

All runs first reproduced the expected failing benchmark and passed final
independent grading against the frozen read-only test tree.

| Run | Agent validation after editing | Agent test invocations, including initial failure | Final independent grader |
| --- | --- | ---: | --- |
| B1 | Summary test file: 34 passed; return-code file: 11 passed | 3 | 1 passed |
| S1 | Focused benchmark: 1 passed; summary test file: 34 passed | 3 | 1 passed |
| B2 | Summary and return-code files together: 45 passed | 2 | 1 passed |
| S2 | Focused benchmark: 1 passed; summary test file: 34 passed | 3 | 1 passed |
| B3 | Focused benchmark: 1 passed; summary and return-code files: 45 passed | 3 | 1 passed |
| S3 | Focused benchmark: 1 passed; summary test file: 34 passed | 3 | 1 passed |

Baseline validation consistently included return-code tests; treatment validation
did not. Thus equal success rates do not imply equal validation breadth. All
passed the declared success criterion, but broader software correctness is not
proven. The initial and final harness graders are excluded from agent test counts.

## Skill loading and token accounting

Every S run began with one standalone Skill-file read and output containing the
frozen instructions. Each returned 1,776 characters. Baseline runs had no Skill
loading event. This adds one observed read/tool item; the exact token and time
overhead of loading, catalog availability and invocation instructions is not
itemized and is not estimated.

| Pair | Raw B/S tool calls | B/S excluding standalone Skill loading |
| --- | --- | --- |
| B1/S1 | 8 / 9 | 8 / 8 |
| B2/S2 | 8 / 9 | 8 / 8 |
| B3/S3 | 9 / 9 | 9 / 8 |

Total-token differences are +13.05%, −9.63% and −21.50%, respectively, using each
baseline as denominator. Treatment total usage is therefore not consistently
lower. Output tokens are higher in every treatment (897/803/833 versus
777/780/832), while input differences account for most of each total difference.
Cached input is already included in input and is not added again. Aggregate usage
cannot be partitioned into reads, edits, tests or Skill overhead, and narrower
read ranges cannot quantitatively explain the token differences.

Durations also have mixed directions: S1 is slower, S2 faster, S3 nearly equal
and slightly faster. Median process duration is 26.675 versus 27.380 seconds.
Event receipt timestamps are available for all runs, but they are not provider
execution timestamps; tokens before the first edit remain unavailable.

## Answers to the evaluation questions

1. **Did v0.1 reduce repository exploration?** In the measured scope, yes:
   fewer search commands in every pair, narrower content-search targets and
   shorter requested read ranges. It did not reduce repository read requests
   or median unique explicit targets. Total physical scanning/context cannot
   be measured here, and causality is not established.
2. **Did it reduce redundant work?** Not demonstrated. Repeated-path counts
   were unchanged in two pairs and higher in one, and the ranges do not show
   substantial redundant rereading. Repository tool activity excluding loading
   was equal in two pairs and one lower in the third.
3. **Did it preserve correctness?** It preserved the declared benchmark success
   criterion: 3/3 treatments and 3/3 baselines passed independent grading. Both
   conditions passed broader summary tests, but treatment validation was narrower
   and full correctness is not established.
4. **Did it reduce token usage?** Observed mean and median totals were lower
   by 7.27% and 2.96%, respectively; savings occurred in two of three pairs.
   This supports a descriptive aggregate reduction, not a reliable general
   saving or attribution to the Skill.
5. **Were differences consistent across pairs?** Fewer treatment searches,
   narrower search scopes, smaller aggregate requested ranges, one extra Skill
   read, higher output tokens and narrower validation breadth
   occurred throughout. Success/edit counts and repository read-request counts
   were equal throughout. Total-token, duration, unique-target and repeated-read
   differences were not consistently reductions.
6. **Is this stronger evidence than EVAL-001?** It adds a second bug and more
   direct measurement: frozen fingerprints/object inventories, independent
   sanitized workspaces and event timing. Within EVAL-002, the fewer-search
   pattern is consistent, unlike EVAL-001's higher treatment search median
   (4 versus 3). However, both tasks remained localized, each has only three
   pairs, and token directions are mixed. It improves measurement and coverage
   without establishing a stronger general efficacy claim. EVAL-001's saved
   results and historical limitations remain unchanged.
7. **Change the Skill or add another benchmark first?** Add another benchmark
   first. There is no clearly demonstrated failure tied to a particular
   instruction, no established reduction in redundant work and no repeatable
   token advantage across every pair. Preserve v0.1 and seek a task with
   genuinely broader observable navigation before considering an instruction
   change. No EVAL-003 was started.

## Integrity and limitations

The [verification evidence](six-run-verification.json) records before/after
checks for each newly authorized run and a final audit of all six. All have
13 expected artifacts, complete traces, matched native metrics and matching
monotonic timing entries. Both workspaces were clean at the identical frozen fingerprint at the first
final audit. A later post-report check found the baseline path missing, while
the Skill workspace still matched the frozen fingerprint. All 194 protected files, including B1/S1 and EVAL-001
artifacts, are unchanged. No run infrastructure failure occurred.

The earlier B1 post-reset duplicate-path anomaly remains documented and
quarantined outside solver workspaces. Every before/after checkpoint for the four new runs passed;
its origin remains unconfirmed. It cannot be erased from the experiment's
integrity history, although every recorded starting fingerprint matches.

Three pairs on one bug provide descriptive comparisons only. The fixed alternating
order does not counterbalance time effects; provider caching/service variability
is not controlled by the frozen harness. The read metric omits search scans and
runtime imports. Benchmark success is a limited correctness proxy, and validation
breadth differs by condition. No statistical significance, cost estimate,
per-phase token attribution or hidden-reasoning inference is made.

A later integrity exception is recorded in the verification evidence and report:
the baseline workspace disappeared after the successful final audit. Nearby
suffix-named workspace directories were left untouched and not inspected. All
six runs' captured artifacts and protected files remained unchanged. This is
not a recorded agent/grader failure, but it is a host-state failure and an
additional reproducibility limitation. No repair or further experiment was
attempted. It does not establish a different recorded starting state or prove
that no between-checkpoint interference occurred.
