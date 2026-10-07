# EVAL-004 post-hoc report — COMPLETE

Primary comparison: v0.1 → v0.2. Three repetitions provide no significance claim.

| Run | Success | Tokens | Seconds | Tools | Searches | Reads | Tests | Final edit revalidated |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| B1 | True | 245138 | 142.434 | 18 | 6 | 12 | 3 | True |
| V1-1 | True | 237103 | 158.275 | 17 | 11 | 15 | 5 | True |
| V2-1 | True | 257194 | 148.009 | 17 | 8 | 10 | 5 | False |
| B2 | True | 257909 | 133.114 | 15 | 5 | 15 | 4 | False |
| V1-2 | True | 201240 | 115.420 | 14 | 7 | 10 | 3 | False |
| V2-2 | True | 196303 | 120.366 | 14 | 6 | 11 | 3 | True |
| B3 | True | 201920 | 129.540 | 10 | 10 | 14 | 2 | True |
| V1-3 | True | 215486 | 129.039 | 15 | 8 | 13 | 5 | True |
| V2-3 | True | 217248 | 136.303 | 13 | 6 | 13 | 4 | True |

| Aggregate | B | V1 | V2 |
| --- | ---: | ---: | ---: |
| runs | 3 | 3 | 3 |
| successful_runs | 3 | 3 | 3 |
| success_rate | 1.000 | 1.000 | 1.000 |
| mean total_tokens | 234989 | 217943 | 223581.667 |
| median total_tokens | 245138 | 215486 | 217248 |
| mean input_tokens | 231273.667 | 214076.333 | 219748.333 |
| median input_tokens | 241202 | 211851 | 213734 |
| mean cached_input_tokens | 196010.667 | 181418.667 | 188245.333 |
| median cached_input_tokens | 215040 | 181504 | 187648 |
| mean output_tokens | 3715.333 | 3866.667 | 3833.333 |
| median output_tokens | 3617 | 3635 | 3515 |
| mean duration_seconds | 135.029 | 134.245 | 134.893 |
| median duration_seconds | 133.114 | 129.039 | 136.303 |
| mean tool_calls | 14.333 | 15.333 | 14.667 |
| median tool_calls | 15 | 15 | 14 |
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
| mean time_until_first_edit_seconds | 53.357 | 57.711 | 53.820 |
| median time_until_first_edit_seconds | 54.288 | 60.660 | 54.346 |
| mean time_until_first_targeted_success_seconds | 54.614 | 58.721 | 55.015 |
| median time_until_first_targeted_success_seconds | 55.332 | 61.672 | 55.618 |
| mean searches_before_first_edit | 6 | 7.667 | 6.333 |
| median searches_before_first_edit | 5 | 8 | 6 |
| mean unique_repository_files_before_first_edit | 7 | 6.333 | 6 |
| median unique_repository_files_before_first_edit | 7 | 6 | 6 |
| mean tool_items_before_first_edit | 4.333 | 6 | 5.333 |
| median tool_items_before_first_edit | 4 | 6 | 6 |
| mean post_first_success_tool_calls | 8 | 7.333 | 7.333 |
| median post_first_success_tool_calls | 7 | 7 | 8 |
| mean post_first_success_searches | 1 | 1 | 0.333 |
| median post_first_success_searches | 1 | 1 | 0 |
| mean post_first_success_file_reads | 3 | 2 | 0.333 |
| median post_first_success_file_reads | 3 | 1 | 0 |
| mean post_first_success_test_executions | 1.667 | 2.667 | 2.333 |
| median post_first_success_test_executions | 2 | 3 | 2 |
| mean last_edit_time_seconds | 116.160 | 124.432 | 121.091 |
| median last_edit_time_seconds | 124.567 | 112.743 | 115.432 |
| mean last_test_time_seconds | 112.093 | 123.204 | 113.815 |
| median last_test_time_seconds | 109.255 | 124.186 | 116.726 |
| mean last_validation_time_seconds | 112.093 | 125.265 | 116.487 |
| median last_validation_time_seconds | 109.255 | 124.186 | 116.726 |
| mean edits_after_first_targeted_success | 3.333 | 2.333 | 2.333 |
| median edits_after_first_targeted_success | 2 | 2 | 2 |
| mean edits_after_last_test_execution | 0.333 | 0.333 | 0.333 |
| median edits_after_last_test_execution | 0 | 0 | 0 |
| mean edits_after_last_validation | 0.333 | 0.333 | 0.333 |
| median edits_after_last_validation | 0 | 0 | 0 |
| mean tool_calls_between_first_success_and_final_edit | 5 | 4.333 | 4.333 |
| median tool_calls_between_first_success_and_final_edit | 5 | 5 | 4 |
| mean tool_calls_after_final_edit | 2 | 2 | 2 |
| median tool_calls_after_final_edit | 2 | 2 | 2 |

| Indicator (true / false / unavailable; proportion true) | B | V1 | V2 |
| --- | --- | --- | --- |
| final_edit_revalidated | 2 / 1 / 0; 0.667 | 2 / 1 / 0; 0.667 | 2 / 1 / 0; 0.667 |
| repository_edited_after_last_test | 1 / 2 / 0; 0.333 | 1 / 2 / 0; 0.333 | 1 / 2 / 0; 0.333 |
| production_edited_after_last_test | 1 / 2 / 0; 0.333 | 1 / 2 / 0; 0.333 | 0 / 3 / 0; 0.000 |
| test_edited_after_last_test | 0 / 3 / 0; 0.000 | 1 / 2 / 0; 0.333 | 1 / 2 / 0; 0.333 |
| validation_after_final_production_edit | 2 / 1 / 0; 0.667 | 2 / 1 / 0; 0.667 | 3 / 0 / 0; 1.000 |
| validation_after_final_test_file_edit | 3 / 0 / 0; 1.000 | 2 / 1 / 0; 0.667 | 2 / 1 / 0; 0.667 |
| final_production_edit_revalidated | 2 / 1 / 0; 0.667 | 2 / 1 / 0; 0.667 | 3 / 0 / 0; 1.000 |
| final_test_file_edit_revalidated | 3 / 0 / 0; 1.000 | 2 / 1 / 0; 0.667 | 2 / 1 / 0; 0.667 |

## V1 -> V2 (primary)

| Pair | Tokens Δ% | Duration Δ% | Post tools Δ% | Post searches Δ% | Post reads Δ% | Post tests Δ% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V1-1 / V2-1 | 8.474 | -6.486 | 0.000 | -50.000 | -100.000 | 0.000 |
| V1-2 / V2-2 | -2.453 | 4.285 | 14.286 | -100.000 | N/D | 0.000 |
| V1-3 / V2-3 | 0.818 | 5.629 | -16.667 | N/D | -100.000 | -33.333 |

## B -> V1

| Pair | Tokens Δ% | Duration Δ% | Post tools Δ% | Post searches Δ% | Post reads Δ% | Post tests Δ% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B1 / V1-1 | -3.278 | 11.122 | -30.769 | 100.000 | 150.000 | 50.000 |
| B2 / V1-2 | -21.972 | -13.292 | 0.000 | 0.000 | -100.000 | 0.000 |
| B3 / V1-3 | 6.719 | -0.387 | 50.000 | -100.000 | -75.000 | 200.000 |

## B -> V2

| Pair | Tokens Δ% | Duration Δ% | Post tools Δ% | Post searches Δ% | Post reads Δ% | Post tests Δ% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B1 / V2-1 | 4.918 | 3.914 | -30.769 | 0.000 | -100.000 | 50.000 |
| B2 / V2-2 | -23.887 | -9.577 | 14.286 | -100.000 | -66.667 | 0.000 |
| B3 / V2-3 | 7.591 | 5.221 | 25.000 | -100.000 | -100.000 | 100.000 |

Counts/time/indicator definitions: [EVAL-004-posthoc.md](../../EVAL-004-posthoc.md).
Available-value sample counts are in posthoc-aggregate.json. A zero denominator yields N/D.
Repeated reads, post-success activity and unrevalidated final edits are observations, not automatic defects/waste.
External grader success is separate from solver-side final-edit revalidation.
