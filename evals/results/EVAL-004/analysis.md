# EVAL-004 — complete analysis, post-hoc schema 5.0

All nine runs passed the immutable 113-test verifier. The six new runs executed in the frozen order B2, V1-2, V2-2, B3, V1-3, V2-3. B1/V1-1/V2-1 were reprocessed, never rerun. No infrastructure, lifecycle, fingerprint or contamination failure was detected. Raw artifacts, both Skills, task, model, verifier, execution environment and historical EVAL-001/002/003 artifacts are unchanged.

**Primary result:** relative to v0.1, v0.2 reduced aggregate post-success searches and explicit reads, but did not consistently reduce total post-success tool activity, tokens or duration. Mean total tokens increased **2.59%**, median **0.82%**. Mean duration increased **0.48%**, median **5.63%**. Final-edit revalidation was **2/3** in every condition. This supports a narrower exploration observation, not the intended complete stopping/revalidation effect. Three runs per condition on one task support no significance or generalization claim.

## Measurement and preservation

The frozen runner and original schema-4 execution parser were not edited. Separate `evals/posthoc_trace.py` / `evals/analyze-EVAL-004.py` analyze only saved structured events, commands, exit codes, changed paths and test output. Every added rule has tests; **70 tests passed** before the new runs. Native usage, tool-item counts and elapsed duration are unchanged by reprocessing. Schema-4 derived outputs are archived under `instrumentation-v4/`; original raw traces and all other raw run artifacts retain their hashes.

Completion definitions are in [EVAL-004-posthoc.md](../../EVAL-004-posthoc.md). First success is the first recognized test item reporting all four originally failing regressions as `ok`. Post-success activity starts after that item's completion; overlapping items are excluded. Times use saved monotonic receipt events relative to CLI start, not preparation time or hidden execution timing. A tool call is a structured item, while searches/reads/tests are recognized operations; several operations can share one tool item.

Explicit reads include the Skill load in treatment totals. Unique/repeated files and post-success reads concern repository paths only. Searches exclude filename discovery (`rg --files`), and explicit reads exclude search scanning, Git diff output and implicit imports. Repeated requests for the same path can involve different ranges or changed content and do not establish redundant work. Durations are CLI wall time, excluding harness setup, external grading and reset. Token totals are input plus output; cached input is a subset of input and must not be added again.

`final_edit_revalidated` requires a passing relevant **behavioral test after the final code edit**; Git hygiene and a failed Black check do not establish it. Full `prefetch_related` validation covers edited test files; targeted original IDs can establish production revalidation but cannot prove coverage of arbitrary added tests. Ambiguous coverage/order would be null. False means missing subsequent validation evidence, not an incorrect edit. The external grader uses original tests and therefore cannot revalidate solver-authored test edits.

## Recovered metrics

B1 recovered total searches/tests **6/3**, pre-edit searches/repository files **5/7** (source files **4**), and post-success searches/reads/tests **1/2/2**. V2-1 recovered total searches/tests **8/5** and pre-edit searches/repository files **7/6** (source files **3**). V1-1's existing common metrics did not change. V2-2 additionally recovered searches/tests **6/3** and post-success searches/reads/tests **0/1/2**. All nine trajectories now have **zero unclassified operations** and all requested metrics are available. No activity was inferred from model prose.

The first-triplet interpretation remains mixed: V2-1 has fewer post-success searches/reads, equal calls/tests, higher tokens and shorter duration. The new final-edit indicator adds a material completion caveat: V2-1 edited a test file after its last test, whereas B1 and V1-1 revalidated their final edits. All final production edits in that first triplet were revalidated. Detailed first-triplet reconstruction: [triplet-reanalysis.md](triplet-reanalysis.md).

## Individual runs

| Run | Success / 113 passed | Tokens | Seconds | Tools | Searches | Reads incl. Skill | Unique repo files | Repeated reads | Test executions | Files modified | Skill loads |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | yes | 245,138 | 142.434 | 18 | 6 | 12 | 8 | 4 | 3 | 4 | 0 |
| V1-1 | yes | 237,103 | 158.275 | 17 | 11 | 15 | 8 | 6 | 5 | 4 | 1 |
| V2-1 | yes | 257,194 | 148.009 | 17 | 8 | 10 | 6 | 3 | 5 | 4 | 1 |
| B2 | yes | 257,909 | 133.114 | 15 | 5 | 15 | 8 | 7 | 4 | 4 | 0 |
| V1-2 | yes | 201,240 | 115.420 | 14 | 7 | 10 | 6 | 3 | 3 | 4 | 1 |
| V2-2 | yes | 196,303 | 120.366 | 14 | 6 | 11 | 6 | 4 | 3 | 4 | 1 |
| B3 | yes | 201,920 | 129.540 | 10 | 10 | 14 | 9 | 5 | 2 | 4 | 0 |
| V1-3 | yes | 215,486 | 129.039 | 15 | 8 | 13 | 8 | 4 | 5 | 4 | 1 |
| V2-3 | yes | 217,248 | 136.303 | 13 | 6 | 13 | 6 | 6 | 4 | 4 | 1 |

Every run modified the same four final paths: `django/db/models/fields/related_descriptors.py`, `django/db/models/query.py`, `tests/prefetch_related/tests.py`, `docs/ref/models/querysets.txt`. The frozen verifier always ran 113 original tests; larger solver counts below include added test cases.

## Condition aggregates

Each numeric cell is **median / mean**, with n=3 available in every condition.

| Metric (median / mean) | Baseline | v0.1 | v0.2 |
| --- | --- | --- | --- |
| Runs | 3 | 3 | 3 |
| Successful runs / success rate | 3 / 100% | 3 / 100% | 3 / 100% |
| Total tokens | 245,138 / 234,989 | 215,486 / 217,943 | 217,248 / 223,581.667 |
| Input tokens | 241,202 / 231,273.667 | 211,851 / 214,076.333 | 213,734 / 219,748.333 |
| Cached input tokens | 215,040 / 196,010.667 | 181,504 / 181,418.667 | 187,648 / 188,245.333 |
| Output tokens | 3,617 / 3,715.333 | 3,635 / 3,866.667 | 3,515 / 3,833.333 |
| Duration (s) | 133.114 / 135.029 | 129.039 / 134.245 | 136.303 / 134.893 |
| Tool calls | 15 / 14.333 | 15 / 15.333 | 14 / 14.667 |
| Repository searches | 6 / 7 | 8 / 8.667 | 6 / 6.667 |
| Explicit reads incl. Skill | 14 / 13.667 | 13 / 12.667 | 11 / 11.333 |
| Explicit repository reads | 14 / 13.667 | 12 / 11.667 | 10 / 10.333 |
| Unique repository files | 8 / 8.333 | 8 / 7.333 | 6 / 6 |
| Repeated repository reads | 5 / 5.333 | 4 / 4.333 | 4 / 4.333 |
| Test executions | 3 / 3 | 5 / 4.333 | 4 / 4 |
| Files modified | 4 / 4 | 4 / 4 | 4 / 4 |
| Skill load events | 0 / 0 | 1 / 1 | 1 / 1 |
| Time to first edit (s) | 54.288 / 53.357 | 60.660 / 57.711 | 54.346 / 53.820 |
| Time to first targeted success (s) | 55.332 / 54.614 | 61.672 / 58.721 | 55.618 / 55.015 |
| Searches before first edit | 5 / 6 | 8 / 7.667 | 6 / 6.333 |
| Unique repository files before first edit | 7 / 7 | 6 / 6.333 | 6 / 6 |
| Tool calls before first edit | 4 / 4.333 | 6 / 6 | 6 / 5.333 |
| Post-success tool calls | 7 / 8 | 7 / 7.333 | 8 / 7.333 |
| Post-success searches | 1 / 1 | 1 / 1 | 0 / 0.333 |
| Post-success repository reads | 3 / 3 | 1 / 2 | 0 / 0.333 |
| Post-success tests | 2 / 1.667 | 3 / 2.667 | 2 / 2.333 |
| Edits after first success | 2 / 3.333 | 2 / 2.333 | 2 / 2.333 |
| Edits after last test | 0 / 0.333 | 0 / 0.333 | 0 / 0.333 |
| Edits after last validation | 0 / 0.333 | 0 / 0.333 | 0 / 0.333 |
| Last edit (s) | 124.567 / 116.160 | 112.743 / 124.432 | 115.432 / 121.091 |
| Last test (s) | 109.255 / 112.093 | 124.186 / 123.204 | 116.726 / 113.815 |
| Last validation (s) | 109.255 / 112.093 | 124.186 / 125.265 | 116.726 / 116.487 |
| Calls between first success and final edit | 5 / 5 | 5 / 4.333 | 4 / 4.333 |
| Calls after final edit | 2 / 2 | 2 / 2 | 2 / 2 |

Boolean indicators use **true / false / unavailable; true proportion**. They are not averaged with missing values as zero.

| Indicator | Baseline | v0.1 | v0.2 |
| --- | --- | --- | --- |
| final_edit_revalidated | 2 / 1 / 0; 66.7% | 2 / 1 / 0; 66.7% | 2 / 1 / 0; 66.7% |
| repository_edited_after_last_test | 1 / 2 / 0; 33.3% | 1 / 2 / 0; 33.3% | 1 / 2 / 0; 33.3% |
| production_edited_after_last_test | 1 / 2 / 0; 33.3% | 1 / 2 / 0; 33.3% | 0 / 3 / 0; 0.0% |
| test_edited_after_last_test | 0 / 3 / 0; 0.0% | 1 / 2 / 0; 33.3% | 1 / 2 / 0; 33.3% |
| validation_after_final_production_edit | 2 / 1 / 0; 66.7% | 2 / 1 / 0; 66.7% | 3 / 0 / 0; 100.0% |
| validation_after_final_test_file_edit | 3 / 0 / 0; 100.0% | 2 / 1 / 0; 66.7% | 2 / 1 / 0; 66.7% |
| final_production_edit_revalidated | 2 / 1 / 0; 66.7% | 2 / 1 / 0; 66.7% | 3 / 0 / 0; 100.0% |
| final_test_file_edit_revalidated | 3 / 0 / 0; 100.0% | 2 / 1 / 0; 66.7% | 2 / 1 / 0; 66.7% |

## Primary paired comparisons: v0.1 → v0.2

Negative percentages mean v0.2 is lower. Formula: `(V2 − V1) / V1 × 100`. A zero V1 denominator yields N/D; absolute counts remain visible below. All runs succeeded.

| Pair | Tokens Δ% | Duration Δ% | Post calls Δ% | Post searches Δ% | Post reads Δ% | Post tests Δ% |
| --- | --- | --- | --- | --- | --- | --- |
| V1-1 → V2-1 | 8.474 | -6.486 | 0.000 | -50.000 | -100.000 | 0.000 |
| V1-2 → V2-2 | -2.453 | 4.285 | 14.286 | -100.000 | N/D | 0.000 |
| V1-3 → V2-3 | 0.818 | 5.629 | -16.667 | N/D | -100.000 | -33.333 |

### Pair 1

| Metric | V1-1 | V2-1 |
| --- | --- | --- |
| Total tokens | 237,103 | 257,194 |
| Duration (s) | 158.275 | 148.009 |
| Tool calls | 17 | 17 |
| Repository searches | 11 | 8 |
| Explicit reads incl. Skill | 15 | 10 |
| Unique repository files | 8 | 6 |
| Test executions | 5 | 5 |
| Time to first edit (s) | 60.660 | 54.346 |
| Time to first targeted success (s) | 61.672 | 55.618 |
| Searches before first edit | 9 | 7 |
| Unique repository files before first edit | 6 | 6 |
| Tool calls before first edit | 6 | 6 |
| Post-success tool calls | 9 | 9 |
| Post-success searches | 2 | 1 |
| Post-success repository reads | 5 | 0 |
| Post-success tests | 3 | 3 |
| Edits after first success | 3 | 3 |
| Edits after last validation | 0 | 1 |
| Last edit (s) | 150.196 | 141.947 |
| Last test (s) | 151.463 | 117.506 |
| Last validation (s) | 151.463 | 125.523 |
| Calls between first success and final edit | 6 | 7 |
| Calls after final edit | 2 | 1 |
| Final edit revalidated | yes | no |

### Pair 2

| Metric | V1-2 | V2-2 |
| --- | --- | --- |
| Total tokens | 201,240 | 196,303 |
| Duration (s) | 115.420 | 120.366 |
| Tool calls | 14 | 14 |
| Repository searches | 7 | 6 |
| Explicit reads incl. Skill | 10 | 11 |
| Unique repository files | 6 | 6 |
| Test executions | 3 | 3 |
| Time to first edit (s) | 47.762 | 41.123 |
| Time to first targeted success (s) | 48.804 | 42.348 |
| Searches before first edit | 6 | 6 |
| Unique repository files before first edit | 6 | 6 |
| Tool calls before first edit | 5 | 4 |
| Post-success tool calls | 7 | 8 |
| Post-success searches | 1 | 0 |
| Post-success repository reads | 0 | 1 |
| Post-success tests | 2 | 2 |
| Edits after first success | 2 | 2 |
| Edits after last validation | 1 | 0 |
| Last edit (s) | 110.357 | 105.892 |
| Last test (s) | 93.964 | 107.211 |
| Last validation (s) | 100.147 | 107.211 |
| Calls between first success and final edit | 5 | 4 |
| Calls after final edit | 1 | 3 |
| Final edit revalidated | no | yes |

### Pair 3

| Metric | V1-3 | V2-3 |
| --- | --- | --- |
| Total tokens | 215,486 | 217,248 |
| Duration (s) | 129.039 | 136.303 |
| Tool calls | 15 | 13 |
| Repository searches | 8 | 6 |
| Explicit reads incl. Skill | 13 | 13 |
| Unique repository files | 8 | 6 |
| Test executions | 5 | 4 |
| Time to first edit (s) | 64.710 | 65.993 |
| Time to first targeted success (s) | 65.686 | 67.077 |
| Searches before first edit | 8 | 6 |
| Unique repository files before first edit | 7 | 6 |
| Tool calls before first edit | 7 | 6 |
| Post-success tool calls | 6 | 5 |
| Post-success searches | 0 | 0 |
| Post-success repository reads | 1 | 0 |
| Post-success tests | 3 | 2 |
| Edits after first success | 2 | 2 |
| Edits after last validation | 0 | 0 |
| Last edit (s) | 112.743 | 115.432 |
| Last test (s) | 124.186 | 116.726 |
| Last validation (s) | 124.186 | 116.726 |
| Calls between first success and final edit | 2 | 2 |
| Calls after final edit | 3 | 2 |
| Final edit revalidated | yes | yes |

Pair 1: fewer searches/reads in V2, equal post-success calls/tests, +8.47% tokens and −6.49% duration; final test edit not revalidated in V2. Pair 2: fewer searches but one post-success read versus zero, more calls, equal tests, −2.45% tokens and +4.29% duration; V2 revalidated and V1 did not. Pair 3: equal zero searches, fewer reads/calls/tests, +0.82% tokens and +5.63% duration; both revalidated. No pair improves all six efficiency metrics.

## Completion boundaries for all nine runs

| Run | Last edit (s) | Last test (s) | Last validation (s) | Edits after success | Edits after last test | Edits after last validation | Calls success → final edit | Calls after final edit | Final revalidated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | 129.287 | 131.070 | 131.070 | 7 | 0 | 0 | 10 | 2 | yes |
| V1-1 | 150.196 | 151.463 | 151.463 | 3 | 0 | 0 | 6 | 2 | yes |
| V2-1 | 141.947 | 117.506 | 125.523 | 3 | 1 | 1 | 7 | 1 | no |
| B2 | 124.567 | 109.255 | 109.255 | 2 | 1 | 1 | 5 | 1 | no |
| V1-2 | 110.357 | 93.964 | 100.147 | 2 | 1 | 1 | 5 | 1 | no |
| V2-2 | 105.892 | 107.211 | 107.211 | 2 | 0 | 0 | 4 | 3 | yes |
| B3 | 94.627 | 95.955 | 95.955 | 1 | 0 | 0 | 0 | 3 | yes |
| V1-3 | 112.743 | 124.186 | 124.186 | 2 | 0 | 0 | 2 | 3 | yes |
| V2-3 | 115.432 | 116.726 | 116.726 | 2 | 0 | 0 | 2 | 2 | yes |

| Run | Repo edited after last test | Production after last test | Tests after last test | Validation after final production | Validation after final test edit | Production revalidated | Test edit revalidated |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | no | no | no | yes | yes | yes | yes |
| V1-1 | no | no | no | yes | yes | yes | yes |
| V2-1 | yes | no | yes | yes | no | yes | no |
| B2 | yes | yes | no | no | yes | no | yes |
| V1-2 | yes | yes | yes | no | no | no | no |
| V2-2 | no | no | no | yes | yes | yes | yes |
| B3 | no | no | no | yes | yes | yes | yes |
| V1-3 | no | no | no | yes | yes | yes | yes |
| V2-3 | no | no | no | yes | yes | yes | yes |

Exactly three final edits lack subsequent solver validation: **V2-1** (test file), **B2** (production plus documentation), and **V1-2** (production, tests and documentation). V2-1's last test completed at 117.506 s, failed Black check at 125.523 s, and final test edit at 141.947 s. B2's last test completed at 109.255 s before its final production edit at 124.567 s. V1-2's last test completed at 93.964 s and failed formatter check at 100.147 s before its final mixed edit at 110.357 s. Only Git hygiene followed these edits. Every final production edit in v0.2 was tested; its final test edits were revalidated in 2/3. This observation establishes neither a semantic defect nor that the last change was formatting-only; patches were not manually reviewed.

## Observable chronological trajectories

- **B1:** descriptors/regression and window searches; read descriptors, query, compiler, lookups, AGENTS, tests/models. First descriptor edit 49.503 s → four regressions pass 51.088 s. More query/test edits → eight tests with two failures; docs and test reads, two failed unavailable Black attempts, further edits → full 117 pass 131.070 s. Final diff/status then external 113 pass.
- **V1-1:** load v0.1, search descriptors/query/compiler/window examples; inspect six paths and reproduce four errors. Descriptor/query edit 60.660 s → four pass 61.672 s. Docs/expressions/descriptor reads and two searches; test/docs edits → nine pass, more edits → 118 pass; diff review, final production edit 150.196 s → 118 pass 151.463 s. Final hygiene and 113 pass.
- **V2-1:** load v0.2, search descriptors/query/tests/features; inspect six paths, failed malformed sed followed by valid read, reproduce four errors. Descriptor edit 54.346 s → four pass 55.618 s. Added cases fail; query/docs/tests edit → eight pass then full 117 pass 117.506 s. Config search/diff and failed Black check. Final test edit 141.947 s → hygiene only → 113 pass using original tests.
- **B2:** filename discovery, descriptor/compiler/features searches and reads of seven paths; four errors reproduced. Descriptor edit 56.279 s → four pass 57.423 s. Query/docs/test edit → seven pass. Expressions search/read and full 116 pass 109.255 s; more expressions reads and diff review. Final descriptor/docs edit 124.567 s → hygiene only → 113 pass.
- **V1-2:** load v0.1, filename discovery, descriptor/query/compiler/lookups/docs searches; inspect six paths. Descriptor/query edit 47.762 s → four pass 48.804 s. Docs/test edit → seven pass, full 116 pass 93.964 s. Formatter-config search and failed Black check. Final descriptor/docs/tests edit 110.357 s → hygiene only → 113 pass.
- **V2-2:** load v0.2, descriptor/test and window/lookups/docs searches; six paths inspected. Descriptor/query edit 41.123 s → four pass 42.348 s. Docs/test edit; unavailable Black version check; seven pass. Reread changed test range alongside diff stat, final test edit 105.892 s → full 116 pass 107.211 s; overlapping diff check, then status. External 113 pass.
- **B3:** descriptors/test searches, compiler/window/query/examples/docs follow-ups; seven paths read before editing. Descriptor edit 54.288 s → four pass 55.332 s. Query/docs/tests edit 94.627 s → full 117 pass 95.955 s. Diff review, later query/sticky-filter search and four reads including release notes in frozen repository; no later edit. External 113 pass.
- **V1-3:** load v0.1, filename discovery, descriptor/window/query/test lookups; seven paths inspected and four errors reproduced. Descriptor/query edit 64.710 s → four pass 65.686 s. Test edit and one docs read → six tests fail. Query/docs/tests edit 112.743 s → six pass, full 115 pass 124.186 s. Final diff review and 113 pass.
- **V2-3:** load v0.2, descriptor/test/window/query/docs searches; six paths inspected, including revisited test/query ranges, and four errors reproduced. Descriptor/query edit 65.993 s → four pass 67.077 s. Docs/tests edit → seven tests fail. Docs/tests edit 115.432 s → full 116 pass 116.726 s. Final diff review and 113 pass.

These are command/edit/test event sequences, not inferred internal hypotheses. Different-range reads and reads after edits are revisits, not necessarily redundant. All runs located the same descriptor/query subsystem; baseline B3 additionally inspected SQL query/release notes, while V1-1/B2/V1-3 explicitly read expressions. v0.2 inspected six unique repository files in every repetition. v0.2 reached first edit and passing original targets earlier than v0.1 in pairs 1/2, later in pair 3.

## Post-success activity classification

| Classification | Observable evidence and limits |
| --- | --- |
| Clearly necessary validation | Added or changed production/tests followed by targeted/full-module checks in every condition. Failures from newly added cases required further changes and reruns in B1, V2-1, V1-3, V2-3. V1-1's later 118-test rerun follows another production edit. V2-2's final 116-test run follows a test edit. These are validation of changed state, not unchanged repetition. |
| Potentially necessary validation/review | Diff/check/status and expressions/docs/configuration searches/reads; broader module runs after focused tests cover more original and newly added cases. B3's final query/sticky-filter inspection has no subsequent edit; necessity is not established. Failed formatter checks/availability attempts observe tooling constraints but do not establish correctness. |
| Redundant/repeated activity | B1 attempted the same unavailable Black module twice with no observable installation between attempts. Repeated file paths alone are insufficient evidence of waste. No blanket redundancy label is applied to V1's extra tests or V2's later reads. |
| Unable to classify necessity | Structured edits expose paths and timing, not semantic necessity. Final unrevalidated edits cannot be labeled formatting-only, harmful or unnecessary without patch review. Token differences cannot be attributed to particular hidden decisions. |

The first four tests passing is an operational convergence point, not proof the broader requested task is finished. Every condition added cases/docs and/or subsequent production edits; later work can be necessary. The checkpoint's effect therefore cannot be assessed by automatically minimizing everything after the first targeted success.

## Secondary baseline comparisons

### B -> V1

| Pair | Tokens Δ% | Duration Δ% | Post calls Δ% | Post searches Δ% | Post reads Δ% | Post tests Δ% |
| --- | --- | --- | --- | --- | --- | --- |
| B1 → V1-1 | -3.278 | 11.122 | -30.769 | 100.000 | 150.000 | 50.000 |
| B2 → V1-2 | -21.972 | -13.292 | 0.000 | 0.000 | -100.000 | 0.000 |
| B3 → V1-3 | 6.719 | -0.387 | 50.000 | -100.000 | -75.000 | 200.000 |

### B -> V2

| Pair | Tokens Δ% | Duration Δ% | Post calls Δ% | Post searches Δ% | Post reads Δ% | Post tests Δ% |
| --- | --- | --- | --- | --- | --- | --- |
| B1 → V2-1 | 4.918 | 3.914 | -30.769 | 0.000 | -100.000 | 50.000 |
| B2 → V2-2 | -23.887 | -9.577 | 14.286 | -100.000 | -66.667 | 0.000 |
| B3 → V2-3 | 7.591 | 5.221 | 25.000 | -100.000 | -100.000 | 100.000 |

Baseline median/mean tokens are 245,138/234,989; v0.1 215,486/217,943; v0.2 217,248/223,581. Both treatment means are lower than baseline (v0.1 −7.25%, v0.2 −4.85%), with mixed directions across pairs. This does not supersede the primary v0.1→v0.2 comparison. The same task/model/config is reused; there are only three repetitions per condition and fixed execution order. No significance claim or cost estimate is made.

## Answers from observable evidence

1. **Benchmark correctness preserved?** Yes: v0.1 and v0.2 each passed 3/3, 113/113 tests per run. This is benchmark correctness, not proof all new tests or every behavior are valid.
2. **Consistently less post-success exploration?** Searches are lower in two pairs and equal zero in the third (2→1, 1→0, 0→0). Reads fall in pairs 1/3 but rise in pair 2 (5→0, 0→1, 1→0). Mean searches −66.67% and reads −83.33%, so aggregate reduction is observable; a strict reduction in both metrics across all pairs is not.
3. **Consistently less total post-success activity?** No: calls 9→9, 7→8, 6→5; identical mean 7.333 and a higher median 7→8. Test invocations are equal in pairs 1/2, lower in pair 3. Post-success edits have identical mean 2.333 and median 2. Fewer searches/reads did not consistently translate to fewer tool items.
4. **Lower token usage?** No aggregate improvement: changes +8.47%, −2.45%, +0.82%; mean +2.59%, median +0.82%. Input mean +2.65%, cached input mean +3.76%, output mean −0.86%; cache is reported separately, without cost inference.
5. **Lower duration?** No aggregate improvement: −6.49%, +4.29%, +5.63%; mean +0.48%, median +5.63%.
6. **Did v0.2 cause agents to stop earlier?** No consistent earlier finish was observed and causation is not established. Final edit occurred earlier in pairs 1/2 but later in pair 3. Last-test completion was earlier in pairs 1/3 but later in pair 2. Total duration improved only in pair 1; calls after final edit have identical mean/median 2. Timing boundaries describe behavior, not why agents stopped.
7. **Reliable revalidation after later edits?** Not completely: final-edit indicator is true in 2/3 for both v0.1 and v0.2. v0.2 revalidated every final production edit but omitted validation after V2-1's final test edit; v0.1 omitted both production/test revalidation in V1-2. Baseline B2 also omitted production revalidation.
8. **Intended behavioral change?** Partly, at the narrower search/read level. The combined intended outcome—less unnecessary post-success work, lower resources and dependable final revalidation—is not supported. Mean post-success calls were unchanged, tokens increased and final revalidation was not universal.
9. **Retain v0.2 as an established improvement?** No: the observed effect is not large/consistent across the intended outcomes. Reject the broad efficiency claim for this benchmark/configuration and revise the hypothesis before treating v0.2 as a validated improvement. Preserve both versions as experimental artifacts; do not infer a generally harmful Skill or revise its wording from these results alone. No Skill was changed, no v0.3 created, no EVAL-005 started.

## Integrity and reproducibility

Frozen HEAD: `7e9cb01fe632404d84e1da569ebd6fafa4e0aa9d`; all three roots restored to fingerprint `1c8165dad3aa453b8131bcd9478691f120ff3b220998dd976381d35d056911f8`, empty Git status and their registered device/inode. The original Codex 0.160.0 / gpt-6.1-sol / medium / web-disabled configuration and image remain frozen. Skill invocation was absent in baseline and explicit once in each treatment; solvers had only their own workspace mount and corresponding frozen Skill. No observed command accessed sibling workspaces, evaluator-only material, external solutions or future repository versions.

All nine directories contain the expected 13 artifacts (117 total): 99 immutable raw artifacts and 18 authorized derived summaries/trajectories. Every solver completed without infrastructure failure; every initial fixture reproduced the four expected errors and every external grader returned all original 113 IDs as `ok`. Report generation checkpoints preserved all roots. Protected input/history/raw hash verification covers 396 files. The preparation manifest remains the unchanged historical preparation record; [analysis-manifest.json](analysis-manifest.json) records current completion and integrity, and [posthoc-manifest.json](posthoc-manifest.json) records the analysis revision and raw hashes.

Reproduce analysis only:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s evals -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 evals/analyze-EVAL-004.py
```

The runner refuses completed run IDs; none should be rerun. The first-triplet historical smoke report is retained separately; use this COMPLETE analysis and [posthoc-report.md](posthoc-report.md) / [posthoc-aggregate.json](posthoc-aggregate.json) for current results.
