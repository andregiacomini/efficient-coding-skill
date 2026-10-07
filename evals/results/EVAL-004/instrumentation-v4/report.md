# EVAL-004 — PARTIAL

Primary comparison: v0.1 → v0.2. Baseline comparisons are secondary.
No statistical significance is claimed from three repetitions per condition.

| Run | Condition | Success | Total tokens | Duration (s) | Tool calls |
| --- | --- | --- | ---: | ---: | ---: |
| B1 | B | True | 245138 | 142.434 | 18 |
| V1-1 | V1 | True | 237103 | 158.275 | 17 |
| V2-1 | V2 | True | 257194 | 148.009 | 17 |

| Aggregate | B | V1 | V2 |
| --- | ---: | ---: | ---: |
| runs | 1 | 1 | 1 |
| successful_runs | 1 | 1 | 1 |
| success_rate | 1.000 | 1.000 | 1.000 |
| mean total_tokens | 245138 | 237103 | 257194 |
| median total_tokens | 245138 | 237103 | 257194 |
| mean tool_calls | 18 | 17 | 17 |
| median tool_calls | 18 | 17 | 17 |
| mean duration_seconds | 142.434 | 158.275 | 148.009 |
| median duration_seconds | 142.434 | 158.275 | 148.009 |
| mean post_first_success_tool_calls | 13 | 9 | 9 |
| median post_first_success_tool_calls | 13 | 9 | 9 |
| mean post_first_success_searches | N/D | 2 | 1 |
| median post_first_success_searches | N/D | 2 | 1 |
| mean post_first_success_file_reads | N/D | 5 | 0 |
| median post_first_success_file_reads | N/D | 5 | 0 |
| mean post_first_success_test_executions | N/D | 3 | 3 |
| median post_first_success_test_executions | N/D | 3 | 3 |
| mean input_tokens | 241202 | 232525 | 252723 |
| median input_tokens | 241202 | 232525 | 252723 |
| mean cached_input_tokens | 215040 | 181504 | 225792 |
| median cached_input_tokens | 215040 | 181504 | 225792 |
| mean output_tokens | 3936 | 4578 | 4471 |
| median output_tokens | 3936 | 4578 | 4471 |
| mean shell_commands | 10 | 13 | 13 |
| median shell_commands | 10 | 13 | 13 |
| mean repository_search_commands | N/D | 11 | N/D |
| median repository_search_commands | N/D | 11 | N/D |
| mean total_file_reads | 12 | 15 | 10 |
| median total_file_reads | 12 | 15 | 10 |
| mean repository_file_reads | 12 | 14 | 9 |
| median repository_file_reads | 12 | 14 | 9 |
| mean unique_files_inspected | 8 | 8 | 6 |
| median unique_files_inspected | 8 | 8 | 6 |
| mean repeated_file_reads | 4 | 6 | 3 |
| median repeated_file_reads | 4 | 6 | 3 |
| mean test_runs | N/D | 5 | N/D |
| median test_runs | N/D | 5 | N/D |
| mean files_modified | 4 | 4 | 4 |
| median files_modified | 4 | 4 | 4 |
| mean skill_loading_events | 0 | 1 | 1 |
| median skill_loading_events | 0 | 1 | 1 |
| mean tool_items_excluding_skill_loading | 18 | 16 | 16 |
| median tool_items_excluding_skill_loading | 18 | 16 | 16 |
| mean time_until_first_edit_seconds | 49.503 | 60.660 | 54.346 |
| median time_until_first_edit_seconds | 49.503 | 60.660 | 54.346 |
| mean time_until_first_test_seconds | 49.682 | 34.554 | 28.341 |
| median time_until_first_test_seconds | 49.682 | 34.554 | 28.341 |
| mean time_until_first_targeted_success_seconds | 51.088 | 61.672 | 55.618 |
| median time_until_first_targeted_success_seconds | 51.088 | 61.672 | 55.618 |
| mean searches_before_first_edit | N/D | 9 | N/D |
| median searches_before_first_edit | N/D | 9 | N/D |
| mean unique_repository_files_before_first_edit | N/D | 6 | N/D |
| median unique_repository_files_before_first_edit | N/D | 6 | N/D |
| mean unique_source_files_before_first_edit | N/D | 3 | N/D |
| median unique_source_files_before_first_edit | N/D | 3 | N/D |
| mean tool_items_before_first_edit | 3 | 6 | 6 |
| median tool_items_before_first_edit | 3 | 6 | 6 |
| mean time_until_first_repository_search_seconds | 17.432 | 8.623 | 9.283 |
| median time_until_first_repository_search_seconds | 17.432 | 8.623 | 9.283 |
| mean time_until_first_file_read_seconds | 17.432 | 8.502 | 9.126 |
| median time_until_first_file_read_seconds | 17.432 | 8.502 | 9.126 |

## V1 → V2 (primary)

| Repetition | Left run | Right run | Total tokens change (%) |
| --- | --- | --- | ---: |
| 1 | V1-1 | V2-1 | 8.474 |
| 2 | N/D | N/D | N/D |
| 3 | N/D | N/D | N/D |

## B → V1

| Repetition | Left run | Right run | Total tokens change (%) |
| --- | --- | --- | ---: |
| 1 | B1 | V1-1 | -3.278 |
| 2 | N/D | N/D | N/D |
| 3 | N/D | N/D | N/D |

## B → V2

| Repetition | Left run | Right run | Total tokens change (%) |
| --- | --- | --- | ---: |
| 1 | B1 | V2-1 | 4.918 |
| 2 | N/D | N/D | N/D |
| 3 | N/D | N/D | N/D |

First success and post-success counts retain EVAL-003 definitions. Missing values remain N/D;
available-value counts are recorded in aggregate.json. Unknown operations are never inferred from prose.
Infrastructure failures are excluded from aggregates; unsuccessful benchmark runs remain included.
Additional validation after targeted success is not automatically unnecessary work.
