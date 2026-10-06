# EVAL-002 report

All six runs completed and passed the frozen independent benchmark test. No run infrastructure failure occurred. Efficient Coding v0.1 used fewer repository search commands in all three pairs. Total tokens were lower in S2/S3 and higher in S1; these descriptive results do not establish a general or causal Skill benefit.

## Frozen experiment

BugsInPy Luigi bug 9; sanitized commit `a5704160099a5301fd68941d1c05a6f3d0c16fa2`.
All six recorded the same clean starting fingerprint:
`b197225d2a08b9a18fa4420a45cd3068f2d8c3e4ca2790e330cf216623d0e8c4`.
Codex CLI 0.160.0, `gpt-6.1-sol`, medium reasoning, disabled web search, and unchanged task/configuration/instrumentation. Fresh sessions and independent workspaces; explicit Skill invocation/loading only in S runs. Execution order: B1, S1, B2, S2, B3, S3. B1/S1 were the earlier smoke check and were not rerun or rewritten.

## Aggregate values

| Metric | Baseline | Efficient Coding v0.1 |
| --- | --- | --- |
| Runs | 3 | 3 |
| Successful runs | 3 | 3 |
| Success rate | 100% | 100% |
| Median total tokens | 109,940 | 106,683 |
| Mean total tokens | 117,925.67 | 109,349.00 |
| Median input tokens | 109,160 | 105,850 |
| Median cached input tokens | 93,312 | 91,264 |
| Median output tokens | 780 | 833 |
| Median duration (seconds) | 27.38 | 26.675 |
| Median tool calls | 8 | 9 |
| Median repository searches | 4 | 2 |
| Median explicit file reads | 5 | 6 |
| Median unique files inspected | 3 | 3 |
| Median repeated reads | 2 | 2 |
| Median test executions | 3 | 3 |
| Median repository file reads | 5 | 5 |
| Median files modified | 1 | 1 |
| Median edit operations | 1 | 1 |
| Median Skill load events | 0 | 1 |
| Median tool items excluding Skill loading | 8 | 8 |

Median total tokens decreased 2.96%; mean total tokens decreased 7.27%. Each group has only three observations on one bug; paired directions are mixed and no statistical significance is claimed.

## Individual runs

| Run | Success / benchmark passed | Total tokens | Input tokens | Cached input tokens | Output tokens | Duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| [B1](B1/summary.json) | Yes | 107,934 | 107,157 | 93,312 | 777 | 29.451 |
| [S1](S1/summary.json) | Yes | 122,016 | 121,119 | 107,648 | 897 | 33.839 |
| [B2](B2/summary.json) | Yes | 109,940 | 109,160 | 82,432 | 780 | 27.38 |
| [S2](S2/summary.json) | Yes | 99,348 | 98,545 | 86,272 | 803 | 25.097 |
| [B3](B3/summary.json) | Yes | 135,903 | 135,071 | 118,784 | 832 | 26.791 |
| [S3](S3/summary.json) | Yes | 106,683 | 105,850 | 91,264 | 833 | 26.675 |

| Run | Tool calls | Repo searches | Explicit reads | Repo reads | Unique files | Repeated reads | Test executions | Files modified | Skill loads |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | 8 | 4 | 5 | 5 | 3 | 2 | 3 | 1 | 0 |
| S1 | 9 | 3 | 6 | 5 | 3 | 2 | 3 | 1 | 1 |
| B2 | 8 | 3 | 5 | 5 | 3 | 2 | 2 | 1 | 0 |
| S2 | 9 | 2 | 6 | 5 | 3 | 2 | 3 | 1 | 1 |
| B3 | 9 | 5 | 6 | 6 | 4 | 2 | 3 | 1 | 0 |
| S3 | 9 | 2 | 7 | 6 | 3 | 3 | 3 | 1 | 1 |

Every run recorded one edit operation in `luigi/execution_summary.py`. Each S run has 8 tool items after excluding its one standalone Skill-loading item; baseline values are 8, 8, 9.

## Paired total-token differences

Difference = `(Skill total - baseline total) / baseline total × 100`; positive means more tokens with the Skill.

| Pair | Baseline tokens | Skill tokens | Absolute difference (S − B) | Percentage difference |
| --- | --- | --- | --- | --- |
| B1 vs S1 | 107,934 | 122,016 | +14,082 | +13.05% |
| B2 vs S2 | 109,940 | 99,348 | -10,592 | -9.63% |
| B3 vs S3 | 135,903 | 106,683 | -29,220 | -21.50% |

## Observable trajectories and interpretation

See [analysis.md](analysis.md) for search scopes, explicit read ranges, editing and validation trajectories, loading overhead, and answers to the seven evaluation questions. Sources are structured tool events, named read operands, recorded changed paths, test output and native aggregate usage; no hidden reasoning or generated patch contents were interpreted.

- Search counts: B/S = 4/3, 3/2, 5/2. Baselines used directory-wide content searches; treatments used named source/test targets. All remained localized around the execution summary.
- Explicit repository read requests: 5/5, 5/5, 6/6. Unique targets: 3/3, 3/3, 4/3. Treatments requested smaller numeric ranges; B3 additionally read the return-code implementation.
- Repeated-path counts: 2/2, 2/2, 2/3. These concern distinct ranges, with only one-line boundary overlaps in B1/B3. They do not demonstrate redundant rereading or its reduction.
- One recorded edit and one final modified application file per run. Patch capture was checked through metadata, valid archives and numstat; patches were not manually reviewed.
- All six reproduced the failing test and passed independent final grading. Baselines additionally validated return-code tests; treatments validated the execution-summary file only after a focused passing rerun.
- Treatments loaded the Skill once (1,776 output characters, one read/tool item each). Its token/time overhead is not separately available and is not estimated.

## Metric scope and verification

All requested metrics were captured and matched a fresh read-only parse of each saved trace. All command classifications are complete under the frozen supported-command rules; comprehensive physical reads and pre-edit tokens remain unavailable by design. Input already includes cached input, and total = input + output. Duration measures the agent process, excluding setup and grading. Explicit reads include Skill loading; unique/repeated reads cover repository paths only, excluding search scans/imports/Git output. Test counts are agent invocations, including failed attempts, excluding harness grading.

Each run has all 13 expected artifacts: raw JSONL, stderr, per-event timing, metadata, summary, trajectory, initial/final grader output, patch, diff statistics, status, modified paths and untracked archive. Every trace event has a matching monotonic timing entry; Codex and final grader exit codes are zero. Recorded trace/timing event counts in order: 22, 24, 22, 24, 24, 24.

Integrity checks passed before and after each newly authorized run, with identical fingerprints and empty Git status. Both workspaces were clean, independent and restored to the frozen state at the first final audit. A later post-report check found the baseline workspace missing; see the integrity exception below. All 194 protected tracked/input/historical files, including B1/S1 and EVAL-001 artifacts, remain byte-identical. No leftover EVAL-002 containers were found. No Skill/configuration/instrumentation changes or EVAL-003 execution occurred.

The earlier B1 smoke check had a post-reset anomaly: 104 untracked files appeared in duplicate-looking paths, origin unconfirmed. They were preserved outside both solver workspaces; both fingerprints were reverified before S1. That quarantine was not altered by this continuation, and all before/after checks for the four new agent runs passed. The earlier observation remains an integrity caveat rather than evidence of different recorded starting states.

Evidence: [six-run-verification.json](six-run-verification.json), earlier [smoke-verification.json](smoke-verification.json), and unchanged [integrity-quarantine](integrity-quarantine/). Preparation documentation/manifest remain historical frozen records; this report records the completed runs.

### Post-report integrity exception — execution stopped

After the successful six-run audit and report generation, another read-only check found `experiments/EVAL-002-baseline` absent. Suffix-named directories (`EVAL-002-baseline 2`, `3`, `4`) exist nearby; their contents were not inspected and their origin is unconfirmed. The Skill workspace still verifies against the frozen fingerprint. All 194 protected files and every artifact hash from all six runs remain unchanged.

This is a host workspace/state-integrity failure after the recorded runs, separate from the six runs' successful traces and grader results. It limits claims about reliable persistence/reset and prevents treating the current host setup as ready for another run. No workspace restoration, substitution, additional agent run or EVAL-003 setup was attempted. The audit retains both the earlier successful clean-state checkpoints and this latest failed-state observation. The recorded starting fingerprints match, but those records do not prove that host state remained stable between checkpoints.
