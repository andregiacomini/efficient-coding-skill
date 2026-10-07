# EVAL-004 first triplet — post-hoc schema 5 reanalysis

B1/V1-1/V2-1 were reprocessed, never rerun. All 33 raw artifacts retain their hashes. Original schema-4 derived outputs and smoke analysis are archived in instrumentation-v4/. Tokens, timings, benchmark success and raw metadata are unchanged.

| Metric | B1 | V1-1 | V2-1 |
| --- | ---: | ---: | ---: |
| repository_search_commands | 6 | 11 | 8 |
| test_runs | 3 | 5 | 5 |
| searches_before_first_edit | 5 | 9 | 7 |
| unique_repository_files_before_first_edit | 7 | 6 | 6 |
| post_first_success_searches | 1 | 2 | 1 |
| post_first_success_file_reads | 2 | 5 | 0 |
| post_first_success_test_executions | 2 | 3 | 3 |
| last_edit_time_seconds | 129.287 | 150.196 | 141.947 |
| last_test_time_seconds | 131.070 | 151.463 | 117.506 |
| last_validation_time_seconds | 131.070 | 151.463 | 125.523 |
| edits_after_first_targeted_success | 7 | 3 | 3 |
| edits_after_last_validation | 0 | 0 | 1 |
| test_edited_after_last_test | False | False | True |
| production_edited_after_last_test | False | False | False |
| final_edit_revalidated | True | True | False |
| final_production_edit_revalidated | True | True | True |
| final_test_file_edit_revalidated | True | True | False |
| tool_calls_between_first_success_and_final_edit | 10 | 6 | 7 |
| tool_calls_after_final_edit | 2 | 2 | 1 |

B1 recovered searches/tests (6/3), pre-edit searches/files (5/7), and post-success searches/reads/tests (1/2/2). V2 recovered searches/tests (8/5) and pre-edit searches/files (7/6). No remaining unclassified operation exists in these three traces. Failed malformed sed contributes zero reads; failed Black load is not a successful check or edit.

V2-1 made a final test-file edit at 141.947 s, after its last test at 117.506 s and failed formatter check at 125.523 s. Subsequent git diff/check/status is hygiene, not behavioral revalidation: final_edit_revalidated=false. B1 and V1-1 have true indicators; every final production edit has a subsequent passing relevant test. The V2 observation does not establish an incorrect patch or invalid test. The external 113-test grader passed but does not cover edited/new solver tests.

The primary interpretation remains mixed: V2 performs fewer post-success searches/explicit reads, but equal tool calls/tests, +8.47% tokens and −6.49% duration. This triplet supports no efficacy conclusion or Skill change. Indicator methodology is in ../../EVAL-004-posthoc.md.
