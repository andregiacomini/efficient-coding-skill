# EVAL-003 B1/S1 smoke comparison

Only B1 and S1 were executed. Both pass the frozen 113-test verifier; neither has an infrastructure failure. This is a single-pair smoke check, not evidence establishing Skill effectiveness. Efficient Coding remains unchanged v0.1.

Configuration: Codex CLI 0.160.0; gpt-6.1-sol; reasoning medium; web disabled. Both fresh sessions start from neutral commit `7e9cb01fe632404d84e1da569ebd6fafa4e0aa9d` and fingerprint `7253a1d91093fdb8513f9982b04f9feeafdb45ed4578d2f9a5dc409d661090c1`. Skill availability and explicit invocation are S1-only.

## Metrics

| Metric | B1 | S1 |
| --- | ---: | ---: |
| Success | Yes | Yes |
| 113-test verifier passed | Yes | Yes |
| Total tokens | 211,361 | 445,148 |
| Input tokens | 208,098 | 439,456 |
| Cached input tokens | 183,040 | 406,144 |
| Output tokens | 3,263 | 5,692 |
| Duration | 93.620 s | 136.720 s |
| Tool calls | 12 | 21 |
| Repository searches | 7 | N/A (8 recognized; incomplete) |
| Explicit file reads | 11 | 15 |
| Unique files inspected | 6 | 9 |
| Repeated reads | 5 | 5 |
| Test executions | 2 | N/A (5 recognized; incomplete) |
| Files modified | 4 | 4 |
| Skill load events | 0 | 1 |

Total tokens in S1 are **110.61% higher** and agent process duration **46.04% longer** in this pair. Cached input is included in input, not added again. These are descriptive differences, not a causal or general efficiency conclusion.

## Convergence

| Convergence metric | B1 | S1 |
| --- | ---: | ---: |
| Time to first repository search | 6.722 s | 6.339 s |
| Time to first file read | 10.564 s | 6.183 s |
| Time to first edit | 44.614 s | 31.586 s |
| Time to first test | 44.774 s | 17.463 s |
| Searches before first edit | 5 | N/A (6 recognized; incomplete) |
| Unique source files inspected before first edit | 2 | N/A (3 explicit targets recognized; incomplete) |
| Tool calls before first edit | 4 | 7 |

Times are monotonic host event-receipt times relative to agent launch, not exact execution-start timestamps. First file read in S1 is the Skill; first repository-file read is 11.997 s, versus 10.564 s for B1. Tool counts before the first edit include Skill loading. No hidden reasoning or per-action token usage was used.

## Instrumentation coverage

Native usage, tool-item counts, durations, Skill load events, final changed-path inventories, complete raw traces and per-line timings were captured. Timing-sidecar line numbers/counts match raw JSONL in both runs. Read metrics count supported explicit named targets only; unique/repeated counts are repository-only. S1 has 15 recognized read requests: 14 repository requests and one Skill read; B1 has 11 repository requests.

S1 issued two compound `sed` expressions selecting multiple ranges and two inline Python/heredoc debug probes. Frozen schema v3 conservatively leaves their coverage opaque. Its comprehensive searches/test counts and pre-edit search/source counts are therefore null. Eight searches, five test commands, six pre-edit searches and three pre-edit source targets are recognized lower-bound observations, not replacements for unavailable complete metrics. Compound sed reads are omitted from recognized read counts even where their paths are visible in the recorded commands. Rules, traces and summaries were not changed or reanalyzed to fill gaps.

Both repeated-read counts are five under this explicit-read scope. B1 selected different ranges in related_descriptors.py and the test/doc files; S1 revisited query.py, expressions.py, sql/query.py and the prefetch tests. Repeated target requests do not establish redundant rereading; S1 additionally has unsupported multi-range reads.

## Observable B1 chronology

1. **6.722–10.564 s:** Filename searches target prefetch/descriptors, followed by AGENTS.md, Git status and symbol searches in relation descriptors and the benchmark tests.
2. **16.475–22.910 s:** Reads multiple descriptor ranges, the failing test class, queryset/prefetch coordination, test imports and relation-model fixtures. Searches also examine window/query behavior in SQL compiler/where/query, window-function code and window tests. Before editing, supported explicit production reads name related_descriptors.py and query.py; supported repository reads cover five unique targets.
3. **44.614–44.774 s:** First observable implementation commitment is a structured edit to related_descriptors.py, followed by the focused four-test class: all four pass. This describes editing activity, not an inferred internal hypothesis.
4. **66.104–66.278 s:** Edits descriptors, query.py and the test file, then runs the whole prefetch module: 116 tests pass, including added local cases.
5. **73.809–88.544 s:** Checks diffs, reads queryset documentation in two ranges, searches Window expressions, and makes another query.py/documentation edit. Final agent validation is diff/status, with no further agent test after this last edit. The separate grader then passes all 113 frozen tests.

## Observable S1 chronology

1. **6.183–12.036 s:** Loads the Skill once, then directly searches prefetch descriptors/tests and AGENTS.md. Reads runtime instructions and prefetch tests; a multi-range descriptor read falls outside supported metric parsing. Searches query-state/window expressions, expression-window tests and relation-model ordering.
2. **17.303–31.581 s:** Reads queryset coordination, a window test, descriptor imports, documentation and SQL compiler ordering. Reproduces the four initial errors itself at 17.463 s before any edit. Recognized pre-edit source reads include descriptors, query.py and compiler.py; seven explicit repository targets are recognized.
3. **31.586–34.514 s:** First structured implementation edit targets related_descriptors.py; the four focused tests then pass.
4. **62.956–100.223 s:** Edits query.py, documentation and tests. An eight-test focused run fails two added cases. It expands into sql/query.py, expressions.py and lookup-resolution searches, revisiting query ranges. A Python debug probe fails on a runtests API invocation; a second probe executes one added test and reproduces a failure.
5. **110.645–117.532 s:** Edits the test file again; eight focused tests pass, then the whole prefetch module passes 117 tests.
6. **117.535–132.860 s:** Reviews diffs, makes another descriptors/query.py/documentation edit, then checks diff/status. No further agent test follows the last edit; the separate final grader passes all 113 frozen tests.

Both final changed-path inventories contain the same four paths: `django/db/models/fields/related_descriptors.py`, `django/db/models/query.py`, `docs/ref/models/querysets.txt`, `tests/prefetch_related/tests.py`. Generated patches were captured and hashed without manually inspecting their contents.

## Navigation and interpretation

Both agents initially locate relation descriptors and prefetch tests directly. Observable exploration spans related managers/descriptors, queryset coordination, SQL/window behavior and tests/documentation. B1 has two recognized pre-edit production targets; S1 has three, and later broadens into query-state/expression handling after added-test failures. Exact counts of alternative implementation hypotheses cannot be recovered from tool activity; modules/search scopes are observable, internal hypotheses are not.

S1 edits earlier (31.586 versus 44.614 s), performs a pre-edit test, records more total tool items (21 versus 12), more supported explicit repository targets (9 versus 6), and more recognized validation commands. Its one dedicated Skill-loading item leaves 20 tool items excluding loading, versus B1’s 12. Those differences extend beyond the loading event, but attribution to the Skill cannot be established from this one pair.

Both solve the broader task according to the identical frozen verifier and each modifies two production files plus tests and documentation. Final correctness remains a benchmark proxy, not complete Django correctness.

## Integrity and readiness

All 13 expected artifacts exist in each run. Initial failures and final 113-test results are recorded separately. Capture completed before reset. Both root device/inode identities are preserved; both HEAD/status/fingerprints are restored. Each agent container was checked for the single permitted workspace mount; no sibling root, evaluator notes or gold/future history was exposed.

Report-before/report-after checkpoints and the final independent audit agree with the frozen states. All 196 protected input/preparation/historical artifact files match the pre-run SHA-256 snapshot. B1 artifacts retain their hashes through S1. EVAL-001/002 artifacts, Skill, prompt, configuration, instrumentation and EVAL-003 preparation metadata are unchanged. The preparation manifest remains its immutable pre-run snapshot; this document records the later smoke result.

No lifecycle/contamination failure occurred. **The harness is ready for B2/S2/B3/S3**, with conservative partial-command metric coverage in S1 explicitly noted. No remaining run was started. Do not conclude effectiveness/ineffectiveness or change the Skill from this smoke pair.

Sources: [B1 summary](B1/summary.json), [B1 observable trajectory](B1/trajectory.json), [S1 summary](S1/summary.json), [S1 observable trajectory](S1/trajectory.json), [partial report](report.md), [integrity verification](smoke-integrity-verification.json).
