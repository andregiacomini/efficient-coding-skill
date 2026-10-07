# EVAL-004 — first-triplet smoke comparison

Status: **PARTIAL: B1, V1-1, V2-1 only**. All three passed the immutable 113-test verifier; no infrastructure/lifecycle/contamination failure was recorded. Remaining six runs were not started. Neither Skill, task, model, verifier nor instrumentation was changed.

## Run metrics

| Metric | B1 | V1-1 | V2-1 |
| --- | ---: | ---: | ---: |
| Success | Yes | Yes | Yes |
| 113-test verifier passed | Yes | Yes | Yes |
| Total tokens | 245,138 | 237,103 | 257,194 |
| Input tokens | 241,202 | 232,525 | 252,723 |
| Cached input tokens | 215,040 | 181,504 | 225,792 |
| Output tokens | 3,936 | 4,578 | 4,471 |
| Duration (s) | 142.434 | 158.275 | 148.009 |
| Tool calls | 18 | 17 | 17 |
| Repository searches | N/D | 11 | N/D |
| Explicit file reads (including Skill) | 12 | 15 | 10 |
| Unique files inspected (repository) | 8 | 8 | 6 |
| Repeated reads (repository) | 4 | 6 | 3 |
| Test executions | N/D | 5 | N/D |
| Files modified | 4 | 4 | 4 |

## Convergence and completion

| Metric | B1 | V1-1 | V2-1 |
| --- | ---: | ---: | ---: |
| Time to first edit (s) | 49.503 | 60.660 | 54.346 |
| Time to first targeted-test success (s) | 51.088 | 61.672 | 55.618 |
| Searches before first edit | N/D | 9 | N/D |
| Unique repository files before first edit | N/D | 6 | N/D |
| Tool calls before first edit | 3 | 6 | 6 |
| Tool calls after first success | 13 | 9 | 9 |
| Searches after first success | N/D | 2 | 1 |
| Reads after first success (repository) | N/D | 5 | 0 |
| Test executions after first success | N/D | 3 | 3 |

Explicit file reads include one Skill read in each treatment: repository reads are B1 **12**, V1-1 **14**, V2-1 **9**. Unique/repeated reads concern repository paths only. Repeated means another explicit request for the same path, including different ranges or changed contents; it does not establish redundant work. Search scans and Git diff output are excluded from explicit-read metrics. Zero post-success explicit reads does not mean no code review occurred. Agent test counts exclude preparation/grader executions.

## Primary comparison: V1-1 → V2-1

V2 recorded **9 → 9** post-success tool calls (unchanged), **2 → 1** searches (−50%), **5 → 0** explicit repository reads (−100%) and **3 → 3** test executions (unchanged). Total tokens **237,103 → 257,194 (+8.47%)**; duration **158.275 → 148.009 s (−6.49%)**. Both passed 113/113. First edit/success were earlier in V2 (54.346/55.618 s versus 60.660/61.672 s). This is mixed observable behavior: less post-success search/read activity, with unchanged calls/tests and higher total tokens. It does not establish that the completion checkpoint caused the differences.

The original four targeted regressions passed before additional cases were introduced. In V2, the next eight-test run failed (two failures, two errors), then an edit to query.py/tests/docs was followed by a passing eight-test run and 117-test suite. In V1, the additional nine-test run passed, followed by 118-test suites before and after a later production edit. These later checks cannot all be labeled waste.

## Secondary comparisons

B1 → V1-1: tokens **−3.28%**, duration **+11.12%**, total calls **18 → 17**, post-success calls **13 → 9**. B1 → V2-1: tokens **+4.92%**, duration **+3.91%**, calls **18 → 17**, post-success calls **13 → 9**. Baseline reached its first edit and targeted success earlier than both treatments. Global/pre-edit exploration totals cannot be compared completely because baseline and V2 contain unavailable metrics. No efficacy conclusion follows from this single triplet.

## Observable chronological trajectories

- **B1:** searched relationship descriptors/regression tests and window-related symbols; explicitly read descriptors, query.py, compiler.py, lookups.py, AGENTS.md, test definitions/models before editing. First edit touched related_descriptors.py at **49.503 s**; four regressions passed at **51.088 s**. Subsequently edited query.py/tests, ran eight tests (two failures), inspected docs and reread tests, attempted unavailable Black twice, made more edits and passed **117 tests** at **131.070 s**. Final diff/status checks preceded the evaluator’s **113/113** success.
- **V1-1:** read frozen v0.1, discovered candidate files, searched descriptors/query/compiler/expressions/lookups and window-test examples; explicitly read six repository paths before editing. Initial four-test run failed. First edit touched descriptors and query.py at **60.660 s**; four regressions passed at **61.672 s**. Then read docs/expressions/two descriptor ranges and performed two searches, edited docs/tests, passed nine tests, edited again and passed **118 tests** at **131.603 s**. Reviewed diff, edited descriptors at **150.192 s**, reran **118 tests**, performed final diff/status checks; grader passed **113/113**.
- **V2-1:** read frozen v0.2, searched descriptors/query/regression tests/backend feature flags; inspected descriptors, tests/models, compiler.py, query.py and docs. One malformed sed failed and was followed by a valid read of that file. Initial four-test run failed. First edit touched descriptors at **54.346 s**; four regressions passed at **55.618 s**. Added tests, saw two failures/two errors in eight tests, edited query.py/docs/tests, then passed eight and **117 tests** (full-module completion **117.506 s**). Reviewed diff/config and attempted Black --check (module unavailable). Edited the test file at **141.944 s**, then ran only diff/status; fresh grader passed **113/113** using the original read-only test tree.

All three modified the same four final paths: django/db/models/fields/related_descriptors.py, django/db/models/query.py, tests/prefetch_related/tests.py and docs/ref/models/querysets.txt. Classification uses structured tool events, command arguments, exit codes, test summaries and changed paths. No agent prose, hidden reasoning or generated patch contents were used.

## Post-success activity classification

| Category | Observable evidence |
| --- | --- |
| Clearly necessary validation | V1 item_12: new nine-test group after test edits; item_14: full 118-test module after more test edits; item_18: full module after a later production edit. V2 item_11: added eight-test cases reveal failures; item_13: rerun after query.py/tests edits; item_16: broader 117-test module. These validate new/changed code and additional cases beyond the original four. |
| Potentially necessary validation | V1 item_10: docs/expressions/descriptor reads and searches for limits/backend-feature-related tests; V1 item_15/item_19 and V2 item_15/item_19: diff/check/status review. V2 item_15 searches formatter configuration; item_17 attempts Black --check but fails because the module is absent. Relevance is observable; necessity of every check is not established. |
| Redundant/repeated activity | No clearly unnecessary repetition is established for V1 versus V2. V1 repeats the full module with an intervening production edit, which justifies revalidation; repeated file names/ranges alone do not establish waste. B1 attempts the same unavailable Black module twice without an observable installation between attempts; both return No module named black. |
| Unable to classify | Post-success edits themselves (V1 item_11/item_13/item_17; V2 item_10/item_12/item_18): paths/timing are observable, but necessity/semantic scope cannot be established without reviewing patch content. The final V2 test edit was not followed by another agent test execution. |

The final V2 test-tree edit limits what the agent’s last 117-test success establishes about its final added tests. The frozen 113-test grader verifies final production code against original benchmark tests; it deliberately does not verify newly edited test cases. We do not infer the final edit was formatting-only or introduced a defect. Passing the benchmark remains a correctness proxy, not complete proof.

## Instrumentation coverage and integrity

Tokens, cached input, duration, unique structured tool calls, timing, targeted success, explicit reads, changed paths and all 13 artifacts per run were captured; deterministic reparse matches saved summaries. V1’s command classification is fully covered. B1 conditional shell commands and unrecognized Black invocations leave searches/test totals, pre-edit exploration and post-success search/read/test totals N/D. V2’s malformed `sed -n '1, seventy p'` leaves global searches/tests and pre-edit exploration N/D under the frozen conservative classifier. It failed with exit 1 and was corrected in a later call; its post-success region is fully supported. No parser changes or guessed replacements were made.

Supported observations retained by the parser (lower bounds, not substitutes for unavailable totals): B1 searches 4/tests 3, post-success searches 1/reads 2/tests 2; V2 searches 8/tests 5. V1/V2 post-success primary metrics are all available. CLI completed successfully despite some agent-side commands failing; failed initial tests, added cases and optional formatter attempts are not harness infrastructure failures.

All registered roots retain their device/inode, expected HEAD, empty status and frozen fingerprint. Before/after states and report checkpoints agree. Frozen Skill hashes/prompt/config/parser/verifier inputs and all historical EVAL-001/002/003 result hashes were verified unchanged. Solvers used only their own mounted workspace and appropriate Skill; observable commands showed no sibling/evaluator/external-solution access. Preparation metadata remains the historical preparation record; current run results are in their separate directories and partial aggregate.

## Experiment status only

1. **Correctness:** yes by the benchmark criterion, 113/113 for all three.
2. **Instrumentation:** capture worked; classification coverage is partial as documented, with complete primary post-success V1/V2 metrics.
3. **Integrity:** no infrastructure, lifecycle or contamination issue detected.
4. **V2 post-success reduction:** fewer searches and explicit reads, same calls/tests, higher tokens and shorter duration; a mixed single-triplet observation.
5. **Readiness:** operationally ready for the remaining six runs, with the existing instrumentation limitations documented. None were started. No Skill change or efficacy conclusion is proposed.
