# EVAL-003 — sliced prefetch across relationship types

Status: **COMPLETE AND FROZEN at `eval-003` — six runs, Skill v0.1**.
Classification: **NEGATIVE EFFICIENCY RESULT FOR v0.1**. Baseline **3/3** and
Skill **3/3** pass the same 113-test verifier; no infrastructure/lifecycle failure.
B1/S1 were reprocessed, not rerun. B2, S2, B3, S3 executed in that order.

See the [aggregate report](results/EVAL-003/report.md),
[complete paired/trajectory analysis](results/EVAL-003/analysis.md),
[completion manifest](results/EVAL-003/analysis-manifest.json), and
[instrumentation revision](EVAL-003-instrumentation-v4.json).
Mean treatment tokens increased **52.98%**, median **52.79%**; each pair increased.
S1's earlier edit/passing-regression pattern did not repeat in S2/S3. These are
observations from one task and three trials per condition, not general causal
claims. The original preparation manifest is preserved byte-for-byte as
[preparation-manifest.json](results/EVAL-003/preparation-manifest.json).
The [frozen manifest](results/EVAL-003/manifest.json) records input/result SHA-256
hashes. All six raw runs and their derived analyses remain unchanged.

Paired token increases: **+110.61%, +38.94%, +18.00%**. Treatment used more
tool calls in all three pairs. First-edit timing, targeted-test success timing
and pre-edit exploration did not consistently improve. Benchmark correctness was
preserved. Extra post-success activity occurred, but necessary validation must
not be classified as waste solely because it happened after targeted success.
This is a negative efficiency result for this task, not evidence of general harm.

## Historical preparation record (before the six runs)

The following describes preparation at creation time; “not run”, future commands
and zero model requests below apply to that earlier stage.

Status: **PREPARED; NOT RUN**. Skill: unchanged **v0.1**. Agent runs/model
requests during preparation: **0**. No B1/S1 or other solving session was executed.

Hypothesis: Does Efficient Coding v0.1 become more useful when a task requires
discovering and coordinating behavior across multiple parts of a repository?

## Task and selection

- Benchmark: **SWE-bench Verified**, `test` split.
- Dataset: `princeton-nlp/SWE-bench_Verified`, revision
  `c104f840cc67f8b6eec6f759ebc8b2693d585d4a`.
- Project/task: Django, **`django__django-15957`**.
- Title: “Prefetch objects don't work with slices”.
- Exact upstream base: `f387d024fc75569d2a4a338bfda76cc2f328f627`.
- Sanitized starting commit: `7e9cb01fe632404d84e1da569ebd6fafa4e0aa9d`.
- Task prompt: [EVAL-003-task.md](EVAL-003-task.md), unchanged between conditions.
- [Four-candidate selection](EVAL-003-candidates.md) uses task/test/buggy-tree
  evidence only. No gold/reference patch or fixed/future application source was
  obtained or inspected. No solution-derived file count was used.

The requested feature spans per-parent slices, offsets, both M2M directions,
reverse FK, ordering, prefetch caching and query budgets. The base has separate
queryset/prefetch coordination, relation-manager and query-state/compiler layers.
Several production files and fixtures plausibly need inspection. This creates
more opportunity for navigation discipline than the earlier one-parser/one-summary
assertions. It is a structural hypothesis, not a guarantee of broad actual agent
exploration or multiple production edits; actual trajectories will be measured.

## Reproduction and success criterion

The benchmark's test-only patch adds four externally observable tests:

- `prefetch_related.tests.PrefetchLimitTests.test_foreignkey_reverse`
- `prefetch_related.tests.PrefetchLimitTests.test_m2m_forward`
- `prefetch_related.tests.PrefetchLimitTests.test_m2m_reverse`
- `prefetch_related.tests.PrefetchLimitTests.test_reverse_ordering`

All four reproduce `TypeError: Cannot filter a query once a slice has been taken.`
The complete prefetch module runs **113 tests: 109 pass, 4 errors, no skips**.
All 4 official FAIL_TO_PASS and 89 PASS_TO_PASS identifiers map to executed
methods, including multiline docstring aliases. This local adapter requires all
113 tests to pass, with the exact frozen inventory and no skips, adding 20 cases
beyond the official 93-item matrix. It is not the full official SWE-bench Docker
harness and should not be presented as an official leaderboard score.

Reproduced in the private candidate checkout, the independently reconstructed
sanitized seed, and both permanent workspaces. See
[baseline failure](preparation/EVAL-003/baseline-failure.txt),
[Skill failure](preparation/EVAL-003/skill-failure.txt) and
[test inventory](preparation/EVAL-003/test-inventory.json).
No reference fix was applied as a positive control.

The command inside the frozen container is:

```sh
/opt/eval-003-venv/bin/python tests/runtests.py prefetch_related --settings=test_sqlite --parallel=1 --verbosity=2
```

A separate grader mounts the full frozen `tests/` tree read-only. Agent edits to
tests cannot change the grading inventory or expectations. Benchmark failure is
separate from infrastructure failure; missing/skipped/unrecognized required tests
fail infrastructure verification rather than silently being counted as success.

## Frozen configuration and environment

Codex CLI **0.160.0**, model **`gpt-6.1-sol`**, reasoning **medium**, web **disabled**,
multi-agent **false**, ignored user configuration, fresh non-resumed sessions,
approvals **never**, 1,800-second timeout, full sandbox permissions inside the
isolated container. The identical prompt is supplied via stdin. Efficient Coding
v0.1 is the only intended within-experiment variable.

Runtime image:
`sha256:d307634c1cc808d6f98d111060e5bef40a5f5c4cfeb80d05263fa9fc3decfb3c`.
It derives from the frozen source-free EVAL-002 runtime, retaining the exact CLI.
Python **3.10.16** and five pinned Django test dependencies replace the Python 3.8
execution environment. This explicit per-benchmark adaptation avoids a compiler-
dependent timezone backport on ARM64; both arms use the same runtime. SQLite is
in-process/in-memory; no database server or heavier benchmark stack is added.
The image contains no Django installation, benchmark source, dataset or gold data.

Inputs/image/test/support hashes are in [EVAL-003-config.json](EVAL-003-config.json)
and the [preparation manifest](results/EVAL-003/manifest.json). Rebuilding an image
can change its ID; never silently substitute it after preparation. Before building,
verify the base tag's ID against EVAL-002's frozen image. Candidate preparation used
only column-projected allowed metadata; gold/hints were never decoded.

## Sanitization, isolation and lifecycle

The seed was reconstructed from an exact base `git archive`, with only the official
`tests/prefetch_related/tests.py` patch and shared neutral `AGENTS.md` overlaid.
Application bytes match the base tree. A new Git repository with one neutral root
commit removes upstream messages, refs, future/fixed commits and unreachable
objects. Both clones have independent object storage, no remotes or alternates,
and the entire object inventory is checked. Only each agent's own root is mounted;
no evaluator repository, dataset, candidates, seed, sibling root or Docker socket
is visible. External known-solution use is forbidden, with web search disabled;
this is content/history isolation, not an air-gap claim.

- Baseline: `/Users/andregiacomini/Documents/GitHub/efficient-coding-skill/experiments/EVAL-003-baseline`
- Skill: `/Users/andregiacomini/Documents/GitHub/efficient-coding-skill/experiments/EVAL-003-skill`
- Both HEADs: `7e9cb01fe632404d84e1da569ebd6fafa4e0aa9d`.
- Both `git status --short`: empty; no unexpected ignored files.
- Both fingerprints: `7253a1d91093fdb8513f9982b04f9feeafdb45ed4578d2f9a5dc409d661090c1`.
- Tracked files: 6,648, including shared runtime instructions.

Skill code is external to both repositories. Baseline containers have no efficient-
coding Skill. Future S containers install the unchanged file under
`/root/.agents/skills/efficient-coding/SKILL.md`, with the explicit developer
instruction `Use the $efficient-coding Skill v0.1 for this task.`

Roots were created once during explicit preparation and registered by path,
device/inode and fingerprint. Future runs never recreate missing roots, and
post-capture reset restores children without deleting or renaming a root. Every
harness destructive operation logs target/time/reason before execution. Workspace
snapshots are recorded before/after runs and report generation; the reporter is
read-only for workspaces. Missing/replaced/changed roots fail loudly. See
[workspace lifecycle](WORKSPACE-LIFECYCLE.md) and
[lifecycle log](results/EVAL-003/lifecycle.jsonl). External interference between
checkpoints remains possible; neither the historical persistence cause nor a
complete prevention guarantee is claimed.

## Reproduction and later run commands

Prerequisites: Docker running, frozen image available, host Codex auth available.
The standard-library-only helper reconstructs the seed from the exact base and
frozen test patch, then explicitly creates/registers roots and verifies failure:

```sh
python3 evals/setup-EVAL-003.py
```

Existing registered roots are verified, not silently recreated/adopted. On another
host, create fresh roots through preparation to record its local identities.
If the seed exists, explicit prepare/check commands are:

```sh
python3 evals/run-eval.py --eval EVAL-003 --prepare
python3 evals/run-eval.py --eval EVAL-003 --check
```

The following are **ready but have not been executed**:

```sh
python3 evals/run-eval.py --eval EVAL-003 B1
python3 evals/run-eval.py --eval EVAL-003 S1
python3 evals/run-eval.py --eval EVAL-003 --all
```

`--all` is an alternative for a completely empty six-run result set. Existing run
artifacts are never overwritten; do not use it to resume a partially completed set.

## Instrumentation and empty results

Preserve native success, input/output/cached/total tokens, duration, structured tool
calls, searches, explicit reads, unique/repeated repository targets, tests, edits,
modified files, Skill loading and per-event receipt timing.

Schema v3 additionally captures first repository search, first file read (including
Skill), first repository file read, first edit/test, unique explicit source targets
under `django/` before first edit, searches before first edit and tool items before
first edit. Receipt times are host observations, not provider execution starts;
pre-edit tokens remain unavailable. Unknown commands/absent events remain null.
See [instrumentation](INSTRUMENTATION.md). Historical EVAL-001/002 artifacts are
not reanalyzed with the new schema.

Baseline runs, Skill runs, success, tokens, duration, exploration, validation and
conclusions remain **unmeasured**. Preparation tests and CLI help/version/login
checks made no model request. The preparation report was generated to verify
workspace persistence, not to report experiment results.
