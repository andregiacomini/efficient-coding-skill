# EVAL-001 — explicit Skill invocation experiment

Hypothesis: targeted exploration with `efficient-coding` v0.1 can reduce unnecessary
context, tokens, and tool activity while preserving task success. Compare three
baseline runs with three treatment runs. No statistical significance is claimed
from this sample.

The previous manual B1 state and results were discarded. The six automated evaluations have completed. All three baseline and three
treatment runs passed the original benchmark test without infrastructure failures.
Both arms were restored cleanly afterward. Results are in `evals/results/EVAL-001/`.

## Final status

```text
Status: FROZEN
Date: 2026-10-06
Skill version: v0.1
Runs: B1, S1, B2, S2, B3, S3
Result: INCONCLUSIVE
```

All six runs passed the benchmark test. No reliable token-efficiency improvement
was demonstrated. Token usage varied substantially between runs; observable
exploration and validation differed slightly. Every treatment added one Skill-load
action. The large B2/S2 token difference could not be explained quantitatively by
observable tool activity. No statistical significance is claimed.

**Known contamination limitation:** untracked duplicate files were discovered in
the baseline environment during the post-experiment audit and preserved during
analysis. Their influence on EVAL-001 cannot be ruled out. Future evaluations must
enforce stricter clean-workspace checks. This limitation is retained in the frozen
record and must not be removed when interpreting these results.

Historical artifacts are immutable. Do not rerun, overwrite, or reanalyze this
results directory in place. Future interpretations belong in new derived analyses.
Use the `eval-001` tag to inspect/reproduce the frozen harness; preserve original
artifacts separately if rerunning for reproduction.

## Frozen configuration

| Field | Value |
| --- | --- |
| Benchmark | BugsInPy |
| Project / bug / version | youtube-dl / 2 / `0` |
| BugsInPy revision | `11c5f1eea954a42132cfd06bf257766a7963e0fd` |
| Upstream buggy commit | `84f085d4bdb66ee025fb337bcd571eab7469da97` |
| Experiment commit | `735bffc07ddef89128de379913b6d5dfc67f9789` |
| Agent | Codex CLI `0.160.0` |
| Model | `gpt-6.1-sol` |
| Reasoning effort | `medium` |
| Sandbox | `danger-full-access`, inside isolated Docker containers |
| Approval policy | `never`, for non-interactive execution in the containers |
| Web search | `disabled` |
| Agent sessions | New process and new container/home for every run; no resume or fork |
| User configuration | Ignored; only authentication is copied |
| Multi-agent feature | Disabled in both conditions |
| Skill version | v0.1, identified by the unchanged Skill file hash below |
| Image | `sha256:9c4211b7d47308c04df8a441127ef77894efc3ff71a1e2bf692d1796864ac1a9` |
| Runtime | Linux arm64, Python `3.12.15`; no project dependencies |
| Agent timeout | 1800 seconds; timeout is an infrastructure failure |
| Task prompt | [EVAL-001-task.md](EVAL-001-task.md), exact bytes through stdin in both conditions |
| Prompt SHA-256 | `de96b2e6a7b5fe6ad572c966276f49d26711f05b44527e9de8547e45bbe8c2d1` |
| Skill SHA-256 | `f149e53c49360da6eebcd78c35b6450032d4ea9beba450a2955a5ea91925d8c2` |

The runner pins these settings; it does not consult an environment-variable model
or fall back to another model. Account access to the exact model is not proven by
infrastructure checks. An unsupported-model/authentication error is recorded as
an infrastructure failure and stops execution. Changing the model/settings is a
new experiment configuration and must be deliberate and documented.

## Workspaces and conditions

- Baseline: `/Users/andregiacomini/Documents/GitHub/efficient-coding-skill/experiments/EVAL-001-baseline`.
- Skill: `/Users/andregiacomini/Documents/GitHub/efficient-coding-skill/experiments/EVAL-001-skill`.

Both start at the experiment commit above with empty `git status --short` and
identical contents. That commit adds only the installed benchmark regression test
and shared `AGENTS.md` runtime instructions to the upstream buggy commit. No
application source was changed during preparation.

Independent Git storage is recreated from `experiments/.EVAL-001-seed.git` before
and after each run. The seed has only the two permitted commits. Re-cloning removes
prior run commits, reflogs, hooks, ignored files, and untracked changes; it avoids
leaking previous trials through a simple hard reset. Each clone is then explicitly
hard-reset/cleaned and its HEAD and clean status are checked. There are no remotes
or Git object alternates. Worktrees were avoided because they share Git storage.

Each agent receives a new container with only its own workspace mounted at
`/workspace`. It cannot see the host project, sibling arm, frozen seed, grading
fixtures, results, Docker socket, or BugsInPy metadata. Only authentication is
copied from the host; previous session files and configuration are not copied.
Legacy interactive containers are removed when resetting their respective arms.

B1/B2/B3 have no experimental Skill installed and empty developer instructions.
S1/S2/S3 get the frozen Skill copied to the container's user Skill directory,
`/root/.agents/skills/efficient-coding/SKILL.md`, outside the benchmark checkout.
The source Skill remains in this project and is never modified by the harness.
The treatment developer instruction is exactly:

```text
Use the $efficient-coding Skill v0.1 for this task.
```

This is an **explicit Skill invocation** experiment. The user task prompt remains
unchanged. Skill availability and this invocation are the only intended treatment
changes. Inspect the saved treatment trace afterward to confirm actual loading;
availability/invocation alone does not prove compliance.

## Original failure and grading

Test: `test.test_InfoExtractor.TestInfoExtractor.test_parse_mpd_formats`.

Command inside the Python runtime:

```sh
/opt/eval-venv/bin/python -m unittest -q \
  test.test_InfoExtractor.TestInfoExtractor.test_parse_mpd_formats
```

Expected initial result: exit `1`, one failed test, with:

```text
AssertionError: 7 != 6 : Expect a list of length 7, but got a list of length 6 for field None
```

The failure was reverified in both clean arms without investigation. Historical
setup output: [EVAL-001-initial-failure.txt](EVAL-001-initial-failure.txt).

Before each agent run, the harness verifies this initial failure. After Codex
finishes, its container is removed to stop any background writers, and a fresh
container grades its changed application with the **original test directory**
mounted read-only. These tests come from the frozen experiment snapshot. They
are never exposed to the coding agent through an extra mount and are not derived
from a solution. Agent changes to tests cannot weaken the grading fixture.

A recognizable unittest failure is a task failure; invalid harness output,
missing runtime, invalid/incomplete Codex JSONL, nonzero Codex exit, timeout, or
API/authentication errors are infrastructure failures. Infrastructure failures
are recorded and stop `--all`. The direct unittest exit code is used because the
historical BugsInPy wrapper returned `0` even for the expected failing test.

## Running and resetting

Prerequisites: Python 3.9+, Git, the existing frozen Docker image and seed, a running
Docker engine, and a valid host Codex `auth.json`. The existing experiment is ready.
No API requests are made by `--check` or by report generation.

From the project root, reset and validate without asking Codex to solve the task:

```sh
python3 evals/run-eval.py --check
# Equivalent helper:
bash evals/reset-EVAL-001.sh
```

Run a single evaluation:

```sh
python3 evals/run-eval.py B1
python3 evals/run-eval.py S1
```

Run all six sequentially:

```sh
python3 evals/run-eval.py --all
```

The order is B1, S1, B2, S2, B3, S3. Before execution the runner prints Codex version,
model, reasoning effort, commit, prompt path, Skill version, and order. Every
agent invocation uses non-interactive `codex exec --json` with a fresh process.
Existing nonempty run directories are never silently overwritten. The runner
uses a lock to prevent two simultaneous harness processes from changing an arm.
After an interruption, confirm no runner remains before removing a stale lock.

Artifacts are saved under `evals/results/EVAL-001/<run-id>/`:

- `codex.jsonl` and `codex-stderr.txt`: raw structured output and diagnostics.
- `patch.diff`: binary-capable diff against the frozen commit, including staged,
  unstaged, and agent-committed tracked changes.
- `diff-stat.txt`, `git-status.txt`, `modified-paths.json`: final tracked/nonignored
  untracked change evidence.
- `untracked.tar`: additions not represented by Git diff; symlinks are not followed.
- `initial-test-output.txt`, `test-output.txt`: initial failure and trusted final check.
- `metadata.json`: configuration, actual invocation, timestamps, exits, usage/events,
  command list, and measurement limitations.
- `summary.json`: metrics and any infrastructure failure.

Artifacts are captured before the final workspace reset. If capture/save fails,
the harness leaves the workspace intact rather than discarding unsaved evidence.
Resetting the workspaces does not delete result directories. Archive results before
explicitly clearing a run directory for another trial. The manual B1 artifacts
were intentionally discarded for this new experiment.

Regenerate the report without running an agent:

```sh
python3 evals/run-eval.py --report
```

## Metrics

Schema v2 adds deterministic observable command classification, scoped explicit
file-read inventories/repeats, repository searches, recognized test executions,
Skill loading/invocation evidence, and cached input tokens. Historical phase times
and pre-edit tokens remain unknown. Comprehensive physical reads are not measured;
explicit inspection-request counts are clearly labeled in the report.

See [INSTRUMENTATION.md](INSTRUMENTATION.md) for parsing rules, scope, null handling
and future host-receipt timestamps. Regenerate summaries/trajectories and the report
from existing raw artifacts without running an agent:

```sh
python3 evals/run-eval.py --reanalyze
```

The [behavioral analysis](results/EVAL-001/analysis.md) compares B2/S2 and separates
observed loading activity from repository behavior. Existing raw metadata/JSONL,
patches, logs and test outputs remain unchanged. `summary.json`, `trajectory.json`
and `report.md` are derived artifacts.

## Integrity and limitations

- Fresh sessions, identical model/settings, exact frozen prompt, repository state,
  and runtime image are required for every run.
- Never inspect the reference patch, check out the fixed version, search for the
  known solution, or mount original BugsInPy setup metadata into agent containers.
- Never share patches, traces, sessions, or workspaces between runs.
- The runner does not modify the Skill, frozen prompt, benchmark definition, or seed.
- Docker provides isolation; the nested Codex Linux sandbox is blocked by Docker's
  default namespace policy. Full-access mode is used only inside these dedicated
  containers with a single benchmark mount. Automated approvals are `never` in
  both conditions; this differs deliberately from the discarded interactive setup.
- The current official image uses Python 3.12 instead of historical benchmark
  metadata Python 3.7.0. The expected failure was reproduced without application edits.
- A passing benchmark test does not prove complete correctness or minimality of
  the change; broader review remains necessary before claiming improvement.
- Native JSONL tool items are observable activity, not guaranteed visibility into
  every internal tool call. Explicit command/read counts are recoverable, but
  comprehensive physical reads and opaque subprocess activity are unavailable.
- Three runs per arm do not establish statistical significance. Account load,
  model service changes, caching, and wall-clock variability can affect results.
- The pinned runner image is a local frozen artifact. Preserve it with `docker save`
  and import with `docker load` for identical arm64 runtime reuse. Rebuilding the
  original Dockerfile can change packages/image IDs; deliberately record and
  verify a new frozen image before changing the runner's image constant.
- Both setup/reset helpers now call the safe `--check` mode. They never invoke
  BugsInPy checkout, check out a fixed version, or access original metadata.
  Keep the frozen seed and image; a machine without these artifacts must restore
  them before running this harness. The experiment does not refetch a benchmark
  from the network.

## Infrastructure validation

`--check` succeeded on the actual containers: both HEADs matched the frozen commit,
both Git status outputs were empty, and both trusted tests reproduced the original
failure. No model task was submitted.

Synthetic lifecycle/parser tests validate artifact preservation, fresh Git resets,
API-error handling, missing metrics, and deduplication without touching benchmark
source or invoking real Codex inference:

```sh
python3 -m unittest discover -s evals -p 'test_run_eval.py' -v
```

All six real automated runs completed with the pinned CLI/model and structured
JSONL output. Skill content was observed in completed tool output for S1, S2,
and S3; evidence is recorded in `results/EVAL-001/skill-loading-check.json`.
Unexpected future CLI schemas are retained and reported conservatively.

## Conclusion

Both conditions passed the benchmark in 3/3 runs. Median total tokens were
100,900 for baseline and 117,533 for treatment (16.5% higher); median duration
was 33.518s versus 33.840s; median exposed tool items were 9 versus 10.
This small experiment did not demonstrate resource savings from v0.1. These
results are descriptive, not statistically significant, and success remains
a single-benchmark-test proxy. See `results/EVAL-001/report.md` for all runs.

The enriched analysis found one standalone Skill load in every treatment, equal
median repository tool items after excluding loading, fewer explicit repository
reads in treatment and narrower validation. It does not causally explain the
B2/S2 token difference or justify changing v0.1. No new benchmark runs were made.
