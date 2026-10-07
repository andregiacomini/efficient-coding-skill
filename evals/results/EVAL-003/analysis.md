# EVAL-003 complete report and observable analysis

**COMPLETE: six runs, baseline 3/3 and Efficient Coding v0.1 3/3 pass the identical 113-test verifier. No infrastructure, lifecycle or contamination failure occurred.** No Skill modification or v0.2 implementation was made. B1/S1 were reprocessed, never rerun.

B2, S2, B3, S3 executed in exactly that order, after instrumentation tests passed. Codex CLI 0.160.0, gpt-6.1-sol, medium reasoning, web disabled, Skill v0.1 and frozen benchmark configuration/prompt/start state remain unchanged. One dedicated Skill read was observed in every treatment and none in baseline.

## Uniform instrumentation and provenance

41 tests pass. Schema v4 recognizes multi-range sed as one read request per operand with its selected ranges retained, and a conservative AST subset for literal Python -c/heredoc file reads, file-content regex searches, literal subprocess searches/tests, runtime probes and test entrypoints. No Python is executed by the analyzer; unknown intent/control flow stays opaque.

B1/S1 raw traces, metadata, test outputs and patch/status/archive artifacts are unchanged. Original v3 instrumentation and derived B1/S1 summaries are retained in instrumentation-v3/. Runtime v4 inputs/overlay are retained in instrumentation-v4/. Revision 4.1 adds Black --check as format validation after observing that sole opaque command in S2/S3, then reprocesses all six uniformly. This is a documented post-run measurement extension, not a change to agent behavior. The separately pinned instrumentation overlay leaves the original benchmark config hash and starting fingerprint unchanged.

S1 previously unavailable totals recover as 8 searches, 7 test-invocation attempts, 6 pre-edit searches and 3 pre-edit source targets. Explicit read requests become 17 and repeated repository requests 7. The seven invocations include five direct commands and two inline probes: one probe fails on the runtests API before any cases execute, the other runs one failing added case. Thus invocation attempts must not be confused with successfully started suites or passed cases. B1 native usage/success/duration and S1 native usage/success/duration are unchanged.

All six final command classifications are complete under this defined supported-operation scope. Imports, validator internals, SQL, search scanning and hidden filesystem activity are excluded from explicit-read counts. One repeated target may represent different selected ranges, not redundant work. Tokens come only from native turn usage; cached input is already included in input. Per-action token usage is unavailable, so token increases cannot be assigned numerically to post-success work.

## First-success operational boundary

First success requires a recognized test invocation, a completed structured tool event, a test-case count report and unambiguous verbose ok results for all four original FAIL_TO_PASS method IDs. Bare OK/model prose is insufficient. All six first successes were focused four-test runs. Success time measures tool-completion receipt, while first edit/test/search/read times measure first-event receipt.

Post-first-success activity counts tool items first observed strictly after that successful completion line. Concurrent already-started items are excluded. Missing/ambiguous targeted evidence or opaque phase operations leave complete metrics unavailable; none remain unavailable for the requested final metrics. This boundary means original regression tests pass, not that implementation/validation is finished.

## Aggregates

| Metric | Baseline | Efficient Coding v0.1 |
| --- | ---: | ---: |
| Runs | 3 | 3 |
| Successful runs | 3 | 3 |
| Success rate | 100% | 100% |
| Mean total tokens | 223,626 | 342,103.333 |
| Median total tokens | 211,361 | 322,938 |
| Median input tokens | 208,098 | 319,064 |
| Median cached input tokens | 183,040 | 292,096 |
| Median output tokens | 3,185 | 3,874 |
| Median duration (s) | 78.361 | 95.105 |
| Median tool calls | 13 | 20 |
| Median repository searches | 7 | 8 |
| Median explicit read requests | 11 | 14 |
| Median unique repository files | 6 | 8 |
| Median repeated repository reads | 5 | 5 |
| Median test invocation attempts | 3 | 5 |
| Median first edit (s) | 35.200 | 39.047 |
| Median first test invocation (s) | 35.359 | 20.781 |
| Median first targeted success (s) | 36.212 | 40.006 |
| Median post-success tool calls | 6 | 11 |

Mean total tokens are **+52.98%**, median **+52.79%** in the Skill condition. Mean process duration is **+32.25%**. These are descriptive benchmark observations; no statistical significance or general causal claim is made.

## B1 versus S1

Total-token difference (S−B)/B: **+110.61%**.

| Metric | B1 | S1 |
| --- | ---: | ---: |
| Success | Yes | Yes |
| 113-test verifier passed | Yes | Yes |
| Total tokens | 211,361 | 445,148 |
| Input tokens | 208,098 | 439,456 |
| Cached input tokens | 183,040 | 406,144 |
| Output tokens | 3,263 | 5,692 |
| Duration (s) | 93.620 | 136.720 |
| Tool calls | 12 | 21 |
| Repository searches | 7 | 8 |
| Explicit read requests (includes Skill) | 11 | 17 |
| Repository read requests | 11 | 16 |
| Unique repository files inspected | 6 | 9 |
| Repeated repository read requests | 5 | 7 |
| Test invocation attempts | 2 | 7 |
| Files modified | 4 | 4 |
| Skill load events | 0 | 1 |
| First edit (s) | 44.614 | 31.586 |
| First test invocation (s) | 44.774 | 17.463 |
| First passing targeted test, completion (s) | 45.610 | 35.392 |
| Tool calls before first edit | 4 | 7 |
| Searches before first edit | 5 | 6 |
| Unique repository files before first edit | 5 | 7 |
| Unique source files before first edit | 2 | 3 |
| Post-first-success tool calls | 6 | 12 |
| Post-first-success searches | 2 | 2 |
| Post-first-success repository reads | 2 | 6 |
| Post-first-success test invocation attempts | 1 | 5 |

## B2 versus S2

Total-token difference (S−B)/B: **+38.94%**.

| Metric | B2 | S2 |
| --- | ---: | ---: |
| Success | Yes | Yes |
| 113-test verifier passed | Yes | Yes |
| Total tokens | 185,850 | 258,224 |
| Input tokens | 182,768 | 254,667 |
| Cached input tokens | 162,816 | 228,864 |
| Output tokens | 3,082 | 3,557 |
| Duration (s) | 73.455 | 92.755 |
| Tool calls | 13 | 15 |
| Repository searches | 8 | 8 |
| Explicit read requests (includes Skill) | 11 | 13 |
| Repository read requests | 11 | 12 |
| Unique repository files inspected | 6 | 7 |
| Repeated repository read requests | 5 | 5 |
| Test invocation attempts | 3 | 4 |
| Files modified | 4 | 4 |
| Skill load events | 0 | 1 |
| First edit (s) | 35.200 | 39.047 |
| First test invocation (s) | 35.359 | 25.053 |
| First passing targeted test, completion (s) | 36.212 | 40.006 |
| Tool calls before first edit | 5 | 6 |
| Searches before first edit | 8 | 7 |
| Unique repository files before first edit | 6 | 6 |
| Unique source files before first edit | 3 | 3 |
| Post-first-success tool calls | 6 | 7 |
| Post-first-success searches | 0 | 1 |
| Post-first-success repository reads | 0 | 1 |
| Post-first-success test invocation attempts | 2 | 2 |

## B3 versus S3

Total-token difference (S−B)/B: **+18.00%**.

| Metric | B3 | S3 |
| --- | ---: | ---: |
| Success | Yes | Yes |
| 113-test verifier passed | Yes | Yes |
| Total tokens | 273,667 | 322,938 |
| Input tokens | 270,482 | 319,064 |
| Cached input tokens | 243,712 | 292,096 |
| Output tokens | 3,185 | 3,874 |
| Duration (s) | 78.361 | 95.105 |
| Tool calls | 16 | 20 |
| Repository searches | 5 | 8 |
| Explicit read requests (includes Skill) | 14 | 14 |
| Repository read requests | 14 | 13 |
| Unique repository files inspected | 9 | 8 |
| Repeated repository read requests | 5 | 5 |
| Test invocation attempts | 3 | 5 |
| Files modified | 4 | 4 |
| Skill load events | 0 | 1 |
| First edit (s) | 33.386 | 41.928 |
| First test invocation (s) | 33.552 | 20.781 |
| First passing targeted test, completion (s) | 34.369 | 43.039 |
| Tool calls before first edit | 4 | 7 |
| Searches before first edit | 5 | 7 |
| Unique repository files before first edit | 8 | 8 |
| Unique source files before first edit | 5 | 5 |
| Post-first-success tool calls | 10 | 11 |
| Post-first-success searches | 0 | 1 |
| Post-first-success repository reads | 1 | 0 |
| Post-first-success test invocation attempts | 2 | 3 |

## Observable trajectories

- **B1:** Targeted filename/symbol searches → descriptors/query coordination/tests/fixtures → first descriptor edit at 44.614 s → four targeted tests pass at 45.610 s → broader production/test edits and 116-case module pass → documentation/read/diff work and another production edit. Final external 113-test verifier passes.
- **S1:** Skill load → targeted descriptor/query/window/compiler exploration → initial four-test failure at 17.463 s → first descriptor edit at 31.586 s → four targeted tests pass at 35.392 s → added-case failures, more query-state/expression reads and two Python debugging probes → adjusted eight-case class passes, then 117-case module passes → final production/doc edits. External verifier passes.
- **B2:** Eight searches and six supported repository targets before editing → first descriptor edit at 35.200 s → four targeted tests pass at 36.212 s → query/doc/test edits and six-case focused pass → further doc/test edits and 115-case module pass. No post-targeted-success searches or explicit reads. External verifier passes.
- **S2:** Skill load → seven searches and six supported repository targets before editing → initial four-test failure at 25.053 s → first descriptor edit at 39.047 s → four targeted tests pass at 40.006 s → production/test edits and six-case pass → doc/production/test edits, 115-case module pass and one unavailable Black format-check attempt. External verifier passes.
- **B3:** Five searches and eight supported repository targets before editing, including five production modules → first descriptor edit at 33.386 s → four targeted tests pass at 34.369 s → broader edits and a seven-case failure → test/doc revisions, 116-case module pass → final production edit. External verifier passes.
- **S3:** Skill load → seven searches and eight supported repository targets before editing → initial four-test failure at 20.781 s → first descriptor edit at 41.928 s → four targeted tests pass at 43.039 s → production/test edits, seven-case failure, test/doc revision and seven-case pass → 116-case module pass, unavailable Black format check, final descriptor/test edit. External verifier passes.

Every final changed-path inventory contains the same four paths: related_descriptors.py, query.py, tests/prefetch_related/tests.py and docs/ref/models/querysets.txt. Both conditions therefore coordinate two production files plus tests/documentation. Detailed commands, read ranges, timings and targeted-test results are in each trajectory.json; no reasoning/agent-message text was used. Generated patches were captured and hashed without manually inspecting their contents.

S1 revisits SQL/query and expression code after added-test failures. B3 also revises added tests after a failure. Subsequent work has observable triggers and must not automatically be labeled waste. Several runs edit production after their final agent-run suite; the external verifier checks the final state, but it covers the frozen 113 cases, not every agent-added case. A completion rule must retain validation after relevant final edits.

## Answers to the exploratory questions

1. **First edit consistently earlier? No.** S1 earlier, S2/S3 later.
2. **Passing targeted test consistently earlier? No.** S1 earlier (35.392 vs 45.610 s), S2/S3 later (40.006 vs 36.212; 43.039 vs 34.369). All treatments run their first test earlier, but those initial tests fail. This distinguishes early checking from early successful convergence.
3. **Less exploration before editing? No consistent reduction.** Pre-edit searches are 6 vs 5, 7 vs 8, 7 vs 5. Unique repository targets are 7 vs 5, 6 vs 6, 8 vs 8; source targets 3 vs 2, 3 vs 3, 5 vs 5. Pre-edit tool items are higher in every S run, even before interpreting their different granularity.
4. **More exploration after targeted success? Mixed by measure.** Post-success tool items are higher in every treatment (12/7/11 vs 6/6/10); searches are equal in pair 1 and higher in pairs 2/3 (2/1/1 vs 2/0/0). Explicit reads rise in pairs 1/2 but fall in pair 3 (6/1/0 vs 2/0/1). Each of S2/S3 has exactly one Black-check item after success; excluding that validation-only item, their post-success tool-item counts equal the respective baseline. Higher activity is not uniformly broader file exploration.
5. **Benchmark correctness preserved? Yes.** Baseline 3/3 and Skill 3/3 pass the same 113 cases; this is benchmark correctness, not proof of complete Django correctness.
6. **Overall tokens reduced or increased? Increased in every pair:** +110.61%, +38.94%, +18.00%; mean +52.98%, median +52.79%. Duration and total tool items also rise in every treatment. Scope is this task/model/configuration, not general Skill effectiveness.
7. **S1 early convergence followed by more work repeated? Not as a full pattern.** Higher tokens/tool activity repeat, but earlier edit and earlier passing regression do not. S2/S3 check the initial failing behavior earlier yet reach the first targeted pass later. Phase-level token causation cannot be established from final aggregate usage.
8. **Enough for a specific v0.2 hypothesis? Yes, as a testable hypothesis, not evidence to implement/claim improvement.** Test an explicit post-regression validation/completion checkpoint: list remaining acceptance risks, use available repository validations, revalidate relevant final edits, and stop when those criteria have evidence; add optional checks or new exploration only for a concrete unmet criterion. Predict fewer tool turns/attempts at unavailable optional tools without loss of benchmark or added-regression correctness. Do not simply stop after four tests pass.

## Integrity and limitations

Both roots retain their registered device/inode identities and clean neutral HEAD `7e9cb01fe632404d84e1da569ebd6fafa4e0aa9d`, with common frozen fingerprint `7253a1d91093fdb8513f9982b04f9feeafdb45ed4578d2f9a5dc409d661090c1`. Before/after-run and before/after-report checkpoints agree. All 13 expected artifacts exist per run; 78 total. Raw originals, benchmark config, prompt, Skill, preparation metadata and EVAL-001/002 artifacts remain unchanged. Captured containers mount only their own workspace; no sibling/evaluator/gold/future source was exposed.

Only three trials per condition, one benchmark task, fixed execution order, model/runtime-specific behavior and receipt-based timing limit inference. Measurement v4.1 was extended after observing Black checks; original revisions are archived and all six use uniform final analysis. Token caches and tool granularity affect reported input; no phase token partition, cost estimate or significance claim is made. Baseline and treatments both add test/doc work after original regression success, so post-success activity alone does not identify unnecessary work.

The original preparation manifest remains an immutable preparation record. This report and analysis-manifest.json record the completed experiment. No v0.2 Skill was implemented, and no further evaluation was started.
