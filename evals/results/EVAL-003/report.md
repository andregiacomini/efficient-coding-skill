# EVAL-003 report

Explicit Skill invocation experiment; no statistical significance is claimed.

| Run | Condition | Success | Tokens | Seconds | Tool items | Infrastructure failure |
| --- | --- | --- | ---: | ---: | ---: | --- |
| B1 | baseline | True | 211361 | 93.62 | 12 | — |
| S1 | skill | True | 445148 | 136.72 | 21 | — |
| B2 | baseline | True | 185850 | 73.455 | 13 | — |
| S2 | skill | True | 258224 | 92.755 | 15 | — |
| B3 | baseline | True | 273667 | 78.361 | 16 | — |
| S3 | skill | True | 322938 | 95.105 | 20 | — |

| Metric | Baseline | Efficient Coding v0.1 |
| --- | ---: | ---: |
| Runs | 3 | 3 |
| Successful runs | 3 | 3 |
| Success rate | 100.0% | 100.0% |
| Median total tokens | 211361 | 322938 |
| Median duration | 78.361 | 95.105 |
| Median tool calls | 13 | 20 |
| Median cached input tokens | 183040 | 292096 |
| Median repository searches | 7 | 8 |
| Median unique files inspected (explicit repository reads) | 6 | 8 |
| Median total file reads (explicit; includes Skill) | 11 | 14 |
| Median repository file reads (explicit) | 11 | 13 |
| Median repeated reads (repository) | 5 | 5 |
| Median test runs | 3 | 5 |
| Median Skill loading events | 0 | 1 |
| Median tool items excluding Skill loading | 13 | 19 |

Infrastructure failures are listed individually and excluded from aggregates.
Medians use available values only; missing metrics are not zero.
Success is a benchmark-test proxy, not proof of complete correctness.
Read metrics count explicit named inspection requests, not all physical reads; search scanning is excluded.
Test counts describe recognized observable shell invocations, not hidden interpreter/subprocess activity.
First-action timing and pre-edit tokens are unavailable for historical runs without per-event timing/usage.
