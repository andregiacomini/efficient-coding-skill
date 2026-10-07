# EVAL-004 post-hoc analysis — schema 5 / revision 5.0

This analysis is separate from the frozen execution instrumentation. The original
`run-eval.py`, `trace_analysis.py`, configuration, verifier, prompt, Skills and
agent image are unchanged. `analyze-EVAL-004.py` invokes the frozen native trace
reader with the new `posthoc_trace.analyze_actions` function only in its own
analysis process. Nothing is mounted into the solver. The runner still captures
raw artifacts and enforces the original lifecycle/fingerprint checks. Its initial
schema-4 derived outputs are archived before post-hoc replacement; raw artifacts
and historical EVAL-001/002/003 files are never rewritten.

## Deterministic classification additions

- Quote-aware splitting of unquoted `;`, pipes, `&&`, `||` and newlines; quoted
  operator strings remain arguments. Opaque shell syntax remains unavailable.
- A completed pure AND chain with exit 0 proves each invocation ran. Literal
  `true`/`false` may prove a following AND/OR command executed or was skipped.
  Mixed/failing chains with unknown intermediate status remain unavailable;
  a final `|| true` never proves an earlier test/search ran.
- Black availability checks and formatting checks are distinct from searches,
  explicit file reads and tests. `black --check` and `python -m black --check`
  are recognized attempts even when Black is unavailable. A non-check formatter
  invocation with an explicit failed module-load diagnostic is a failed attempt,
  not an edit. Successful formatting without changed-path evidence has an
  unknown edit outcome, never assumed harmless.
- Numeric sed addresses accept whitespace, multiple ranges and multiple `-e`
  operands. A narrowly matched malformed literal range plus the saved sed
  expression-parse diagnostic and nonzero exit, at the command's final segment,
  establishes a failed inspection with zero reads. Other malformed/dynamic forms
  remain unavailable. The invalid expression is never silently corrected.
- Compound searches, reads, tests and supported literal inline probes retain
  their separate operation counts. No agent prose is consulted or executed.

The original four-regression first-success definition remains unchanged, as do
native token/tool-item/timing measures and the convention excluding overlapping
items from post-success activity. Explicit reads still exclude search scanning,
Git diff output and implicit imports/formatter reads. Tests count invocations,
including failed attempts, not test cases.

## Completion-checkpoint definitions

Times are elapsed seconds from the solver CLI's monotonic start, using the saved
host receipt sidecar. Last-edit/test/validation times are completion-event times;
`last_edit_started_seconds` is also retained. Missing receipt times stay null.
These measure observed event boundaries, not hidden internal execution times.

An edit is one completed successful structured `file_change` item, regardless of
how many paths it contains. Failed edit items are excluded. Opaque writers or
shell edits without changed-path evidence make edit-completion metrics unavailable.
Production paths are under the frozen `source_roots` (`django`); test paths are
under `tests/` or `test/`; other repository paths are reported separately.

A validation attempt is a completed recognized test invocation or formatting
check. A Black failure remains a validation attempt, not a passing validation.
Git diff/check/status are hygiene/review, excluded from semantic revalidation.

- Edits after first success/last test/last validation must **start after** the
  boundary's completion event. Overlapping edit intervals leave affected counts
  unavailable. Counts refer to edit items, not files/lines.
- Repository/production/test edited-after-last-test flags use those same edit
  items and path scope. They do not assert that an edit was wrong.
- Validation-after-final-production/test-edit requires a relevant test invocation
  starting after that edit completes. Separate revalidated flags additionally
  require passing test output/exit status.
- For this task, a full `prefetch_related` module run covers prefetch test files.
  A targeted subset cannot establish coverage of arbitrary test-file edits.
  Production revalidation uses that full module or an execution reporting all
  original regression IDs. Scope relevance is a measurement rule, not proof that
  every correctness risk was exhausted.
- Tool calls between first success and final edit exclude both boundary items.
  Calls after final edit must start after the final edit's completion.

`final_edit_revalidated` measures whether the **code paths in the final edit**
received relevant passing behavioral test validation in the solver trace:

- **true:** a relevant test starts after the final edit completes and passes.
- **false:** no such later passing test is observed, with sufficiently complete
  edit/validation coverage. Failed tests and hygiene/formatting checks cannot
  establish behavioral revalidation.
- **null:** no final code edit exists, scope/order/coverage is ambiguous, a later
  targeted test cannot be mapped to arbitrary changed test-file scope, or an
  overlapping test began before the edit completed.

For mixed code/documentation edit items, this indicator concerns their code paths;
documentation-only final edits remain null. The external grader is excluded: it
runs after the solver and mounts original tests, so it cannot revalidate new
solver-authored tests. A false value is observable missing evidence, not proof of
a defect. In particular, formatting-only edits may leave valid older evidence,
but the parser does not infer that semantic fact from unseen patch contents.

## Reprocessing and reporting

```bash
python3 -m unittest discover -s evals -p 'test_*.py' -q
python3 evals/analyze-EVAL-004.py
```

The first triplet's schema-4 summaries, trajectories and smoke report are preserved
in `results/EVAL-004/instrumentation-v4/`. New derived summaries/trajectories use
schema 5; every completed run is analyzed uniformly. Native raw metadata remains
schema 4 and records the actual execution setup.

`posthoc-aggregate.json` and `posthoc-report.md` report means/medians and available
sample counts, all three comparisons, and per-pair differences. Boolean indicators
use true/false/unavailable counts and proportions among available runs, rather
than pretending missing values are false. A zero baseline denominator makes a
percentage difference unavailable. Three repetitions support no significance
claim. Post-success activity is not automatically unnecessary work.
