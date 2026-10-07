# Observable instrumentation, schema v2

Reanalyze existing artifacts without Docker, agent execution or benchmark writes:

```sh
python3 evals/run-eval.py --eval EVAL-002 --reanalyze
```

This updates derived `summary.json`, creates `trajectory.json`, and regenerates
`report.md`. Raw JSONL, stderr, metadata, patches, statuses, archives, and test
outputs are read-only. Existing duration, success, final modified-file inventory,
configuration and benchmark commit are preserved.

EVAL-001 is permanently frozen. Its historical instrumentation and runner are
preserved by the annotated `eval-001` tag. The current CLI refuses to rerun or
rewrite that experiment; `--eval EVAL-001 --report` prints its saved report.
New interpretations of EVAL-001 must be separate derived documents.

## Event and command rules

- Deduplicate `item.started`/`item.updated`/`item.completed` by item ID; retain the
  first raw line for order/timing and the latest item contents for results.
- Tool count is unique recognized structured tool items, not shell subcommands.
  Unknown tool schemas make that count unavailable. Agent/ reasoning messages
  contribute no operations; their text is never inspected by the analyzer.
- One `command_execution` is one shell-command item. Supported outer
  `sh`/`bash`/`zsh -c/-lc` wrappers are unwrapped with `shlex`. Semicolon and pipe
  syntax is parsed without executing anything. Quoted pattern pipes stay quoted
  data. Compound commands produce several classified operations but one tool item.
- Unsupported programs, dynamic read operands, redirects, conditional branches
  and nested `find -exec` are marked opaque. Search/test completeness is false
  and complete counts are null; independently recognized observations are retained.
- Repository discovery: `pwd`, `ls`, `tree`, `stat`, filename-mode `rg --files`,
  and `find`. Search: `rg`, `grep`, `egrep`, `fgrep`. Repository-search count includes
  content and filename queries but excludes simple `pwd`/`ls`.
- File inspection: explicit literal operands of supported `cat`, numeric
  `sed -n 'START,ENDp'`, or supported `head`/`tail` forms. Each file operand is a
  read request; one command with several operands is one read operation. Piped
  `head`/`tail` without operands filters a stream and adds no file read.
- Paths normalize relative to `/workspace`; `a.py`, `./a.py` and
  `/workspace/a.py` share a target. Skill/external paths remain separate. Unknown
  variables/globs are not expanded; no current repository filesystem is consulted.
- Explicit repository targets determine `unique_files_inspected`. Repeated reads
  sum `max(target_count - 1, 0)` across repository targets. Retain range information:
  repeated targets need not indicate redundant sections. Search scanning, imports,
  Git output and tests are excluded from these scoped inspection counts.
- `total_file_reads` means explicit named content-inspection requests, including
  the Skill. `repository_file_reads` excludes it. These are not physical filesystem
  read totals or a complete inventory of everything the agent saw. The old
  comprehensive `files_inspected` remains null. Partial command coverage is exposed.
- Test execution: `pytest`/`py.test` executables or Python `-m unittest/pytest`.
  Reading a test file or searching for a test name is not test execution. An opaque
  Python program might run tests internally; then comprehensive observable-command
  counts are unavailable. Counts include failed attempted test commands and reruns.
  Test-case counts are extracted only from unittest reports in tool output.
- Editing: structured `file_change`, `apply_patch`/`patch`, or recognized in-place
  `sed`. Structured changed paths describe edit activity; final files modified
  still come from the original-to-final Git comparison, not filename mentions.
- Build/setup: known `make`, `cmake`, package-install/build entry points. Git
  operations classify separately as `git/status/diff`. Everything else is `other`;
  opaque programs can prevent complete metrics.
- One standalone Skill read is a loading item; a mixed Skill/repository command
  is not removed wholesale when calculating tool items excluding loading.
  `skill_invocation_requested` comes from frozen invocation metadata, and is not
  equivalent to proof the Skill was loaded or followed. Tool output containing
  the Skill frontmatter/instruction text is retained as loading evidence.

## Tokens and timings

Input/output/cached input come only from `turn.completed.usage`. Missing fields or
incomplete traces yield null. Total = input + output; cached input is already part
of input. No usage is inferred from character counts, filenames or model prose.

Future runs stream stdout verbatim into `codex.jsonl`. A separate
`event-timing.jsonl` records each raw line number and monotonic host receipt time
relative to process launch. First-edit/test timing uses the first recorded event
for that observable action. It measures **event receipt**, not an exact provider
execution start; buffering/network delay can affect it. The sidecar does not change
the agent prompt/configuration and adds no model-facing instructions.

Historical traces have no item timestamps; phase times remain null. Pre-edit tokens
remain null because final aggregate usage cannot be partitioned by action. Native
per-action usage would be required to recover that metric in future runs as well.

Duration remains process elapsed time; raw historical values are never reconstructed
from file mtimes or total setup timestamps. New `trajectory.json` contains only
observable action categories, commands, read targets/ranges, tool IDs, output-size
counts and reported test counts, not reasoning or agent-message content.

## Starting workspace integrity

New evaluations load an evaluator-owned `EVAL-NNN-config.json`. The configuration,
selection notes and results are never mounted inside either solving container.
Each arm is an independent clone with no remote or shared Git object storage.
Before replacing an existing checkout, the runner rejects unexpected untracked
and ignored files, retaining them for review. A successful artifact capture is
required before discarding files created by an agent run.

The reset recreates the checkout from its frozen seed, runs `reset --hard` and
`clean -fdx` in the new staging checkout, then verifies the result. Required
benchmark support files must be tracked in the seed and have explicitly listed
hashes; they are restored, not discarded as contamination. Validation runtimes
must keep Python/test caches outside the repository.

New snapshots also verify the entire Git object inventory, including unreachable
objects. Exactly the frozen synthetic history is allowed; clean `git status`
alone cannot detect hidden fixed/future commit objects. Transplanted benchmark
test hashes are checked against evaluator-only provenance before execution.

Starting fingerprints hash a sorted inventory of tracked paths, modes and actual
bytes (symlink targets for symlinks), HEAD, expected support-file hashes, shared
agent configuration, test command, image ID and evaluator configuration hash.
Workspace location and treatment-only Skill availability are excluded. Both arms
must agree in infrastructure checks, and each agent run records its fingerprint
in metadata before any model request. Runtime mounts remain limited to that
arm's workspace, with frozen benchmark-provided tests mounted read-only in a
separate grader. For EVAL-002 these include the official test-only transplant;
they are not characterized as original tests from the buggy commit. Pytest grading
uses its final test counts, so expected application ERROR logs are not confused
with collection/setup errors.

## EVAL-003 convergence metrics (schema v3)

Historical EVAL-001/EVAL-002 traces and summaries remain frozen; they are not
reanalyzed with this schema. Future traces also record receipt time to first
repository search (including filename discovery), first explicit file read,
first explicit repository file read, edit and test. First file read includes
Skill loading, so the separate repository-read metric avoids that ambiguity.

Pre-edit metrics count supported search operations, unique explicit targets
under configured production `source_roots`, and structured tool items before
the first edit item. Operations inside one item share a receipt timestamp;
unknown commands make complete pre-edit search/source counts unavailable.
No edit or no timing data yields null, never inferred phase usage. Tool-item
counts include Skill loading. Native pre-edit tokens remain unavailable.

Configured literal Python `test_entrypoints` (EVAL-003: `tests/runtests.py`)
are recognized as test executions. Arbitrary Python scripts remain opaque.
Django grading verifies the complete frozen 113-test inventory, exact count,
no skipped tests and successful statuses, including all official FAIL_TO_PASS
and PASS_TO_PASS entries. Multiline unittest docstrings retain method IDs.
This is a local adapter to the official task/test data, with additional
prefetch-module coverage, not a claim of running the full official SWE-bench
Docker harness. Read-only frozen test mounts are retained.

See [WORKSPACE-LIFECYCLE.md](WORKSPACE-LIFECYCLE.md) for prepared root identities,
reset logging, before/after state snapshots and read-only report checks.
