# EVAL-001 report

Explicit Skill invocation experiment; no statistical significance is claimed.

| Run | Condition | Success | Tokens | Seconds | Tool items | Infrastructure failure |
| --- | --- | --- | ---: | ---: | ---: | --- |
| B1 | baseline | True | 124398 | 33.518 | 9 | — |
| S1 | skill | True | 117533 | 33.84 | 10 | — |
| B2 | baseline | True | 87051 | 28.505 | 8 | — |
| S2 | skill | True | 120420 | 36.09 | 10 | — |
| B3 | baseline | True | 100900 | 37.247 | 9 | — |
| S3 | skill | True | 100888 | 30.069 | 10 | — |

| Metric | Baseline | Efficient Coding v0.1 |
| --- | ---: | ---: |
| Runs | 3 | 3 |
| Successful runs | 3 | 3 |
| Success rate | 100.0% | 100.0% |
| Median total tokens | 100900 | 117533 |
| Median duration | 33.518 | 33.84 |
| Median tool calls | 9 | 10 |
| Median cached input tokens | 88448 | 105088 |
| Median repository searches | 3 | 4 |
| Median unique files inspected (explicit repository reads) | 4 | 3 |
| Median total file reads (explicit; includes Skill) | 5 | 4 |
| Median repository file reads (explicit) | 5 | 3 |
| Median repeated reads (repository) | 1 | 0 |
| Median test runs | 3 | 3 |
| Median Skill loading events | 0 | 1 |
| Median tool items excluding Skill loading | 9 | 9 |

Infrastructure failures are listed individually and excluded from aggregates.
Medians use available values only; missing metrics are not zero.
Success is a benchmark-test proxy, not proof of complete correctness.
Read metrics count explicit named inspection requests, not all physical reads; search scanning is excluded.
Test counts describe recognized observable shell invocations, not hidden interpreter/subprocess activity.
First-action timing and pre-edit tokens are unavailable for historical runs without per-event timing/usage.
