# EVAL-004 — COMPLETE

Primary comparison: v0.1 → v0.2. Baseline comparisons are secondary.
No statistical significance is claimed from three repetitions per condition.

| Run | Condition | Success | Total tokens | Duration (s) | Tool calls |
| --- | --- | --- | ---: | ---: | ---: |
| B1 | B | True | 245138 | 142.434 | 18 |
| V1-1 | V1 | True | 237103 | 158.275 | 17 |
| V2-1 | V2 | True | 257194 | 148.009 | 17 |
| B2 | B | True | 257909 | 133.114 | 15 |
| V1-2 | V1 | True | 201240 | 115.420 | 14 |
| V2-2 | V2 | True | 196303 | 120.366 | 14 |
| B3 | B | True | 201920 | 129.540 | 10 |
| V1-3 | V1 | True | 215486 | 129.039 | 15 |
| V2-3 | V2 | True | 217248 | 136.303 | 13 |

| Aggregate | B | V1 | V2 |
| --- | ---: | ---: | ---: |
| runs | 3 | 3 | 3 |
| successful_runs | 3 | 3 | 3 |
| success_rate | 1.000 | 1.000 | 1.000 |
| mean total_tokens | 234989 | 217943 | 223581.667 |
| median total_tokens | 245138 | 215486 | 217248 |
| mean tool_calls | 14.333 | 15.333 | 14.667 |
| median tool_calls | 15 | 15 | 14 |
| mean duration_seconds | 135.029 | 134.245 | 134.893 |
| median duration_seconds | 133.114 | 129.039 | 136.303 |
| mean post_first_success_tool_calls | 8 | 7.333 | 7.333 |
| median post_first_success_tool_calls | 7 | 7 | 8 |
| mean post_first_success_searches | 1 | 1 | 0.333 |
| median post_first_success_searches | 1 | 1 | 0 |
| mean post_first_success_file_reads | 3 | 2 | 0.333 |
| median post_first_success_file_reads | 3 | 1 | 0 |
| mean post_first_success_test_executions | 1.667 | 2.667 | 2.333 |
| median post_first_success_test_executions | 2 | 3 | 2 |
| mean input_tokens | 231273.667 | 214076.333 | 219748.333 |
| median input_tokens | 241202 | 211851 | 213734 |
| mean cached_input_tokens | 196010.667 | 181418.667 | 188245.333 |
| median cached_input_tokens | 215040 | 181504 | 187648 |
| mean output_tokens | 3715.333 | 3866.667 | 3833.333 |
| median output_tokens | 3617 | 3635 | 3515 |
| mean shell_commands | 10 | 12 | 11.333 |
| median shell_commands | 10 | 12 | 11 |
| mean repository_search_commands | 7 | 8.667 | 6.667 |
| median repository_search_commands | 6 | 8 | 6 |
| mean total_file_reads | 13.667 | 12.667 | 11.333 |
| median total_file_reads | 14 | 13 | 11 |
| mean repository_file_reads | 13.667 | 11.667 | 10.333 |
| median repository_file_reads | 14 | 12 | 10 |
| mean unique_files_inspected | 8.333 | 7.333 | 6 |
| median unique_files_inspected | 8 | 8 | 6 |
| mean repeated_file_reads | 5.333 | 4.333 | 4.333 |
| median repeated_file_reads | 5 | 4 | 4 |
| mean test_runs | 3 | 4.333 | 4 |
| median test_runs | 3 | 5 | 4 |
| mean files_modified | 4 | 4 | 4 |
| median files_modified | 4 | 4 | 4 |
| mean skill_loading_events | 0 | 1 | 1 |
| median skill_loading_events | 0 | 1 | 1 |
| mean tool_items_excluding_skill_loading | 14.333 | 14.333 | 13.667 |
| median tool_items_excluding_skill_loading | 15 | 14 | 13 |
| mean time_until_first_edit_seconds | 53.357 | 57.711 | 53.820 |
| median time_until_first_edit_seconds | 54.288 | 60.660 | 54.346 |
| mean time_until_first_test_seconds | 47.355 | 39.602 | 36.870 |
| median time_until_first_test_seconds | 49.682 | 36.320 | 40.947 |
| mean time_until_first_targeted_success_seconds | 54.614 | 58.721 | 55.015 |
| median time_until_first_targeted_success_seconds | 55.332 | 61.672 | 55.618 |
| mean searches_before_first_edit | 6 | 7.667 | 6.333 |
| median searches_before_first_edit | 5 | 8 | 6 |
| mean unique_repository_files_before_first_edit | 7 | 6.333 | 6 |
| median unique_repository_files_before_first_edit | 7 | 6 | 6 |
| mean unique_source_files_before_first_edit | 3.333 | 3.333 | 3 |
| median unique_source_files_before_first_edit | 3 | 3 | 3 |
| mean tool_items_before_first_edit | 4.333 | 6 | 5.333 |
| median tool_items_before_first_edit | 4 | 6 | 6 |
| mean time_until_first_repository_search_seconds | 8.291 | 8.251 | 9.557 |
| median time_until_first_repository_search_seconds | 7.812 | 8.201 | 9.283 |
| mean time_until_first_file_read_seconds | 15.683 | 8.106 | 9.398 |
| median time_until_first_file_read_seconds | 16.782 | 8.043 | 9.126 |

## V1 → V2 (primary)

| Repetition | Left run | Right run | Total tokens change (%) |
| --- | --- | --- | ---: |
| 1 | V1-1 | V2-1 | 8.474 |
| 2 | V1-2 | V2-2 | -2.453 |
| 3 | V1-3 | V2-3 | 0.818 |

## B → V1

| Repetition | Left run | Right run | Total tokens change (%) |
| --- | --- | --- | ---: |
| 1 | B1 | V1-1 | -3.278 |
| 2 | B2 | V1-2 | -21.972 |
| 3 | B3 | V1-3 | 6.719 |

## B → V2

| Repetition | Left run | Right run | Total tokens change (%) |
| --- | --- | --- | ---: |
| 1 | B1 | V2-1 | 4.918 |
| 2 | B2 | V2-2 | -23.887 |
| 3 | B3 | V2-3 | 7.591 |

First success and post-success counts retain EVAL-003 definitions. Missing values remain N/D;
available-value counts are recorded in aggregate.json. Unknown operations are never inferred from prose.
Infrastructure failures are excluded from aggregates; unsuccessful benchmark runs remain included.
Additional validation after targeted success is not automatically unnecessary work.
