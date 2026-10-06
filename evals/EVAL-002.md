# EVAL-002 — task execution and history reporting

Status: PREPARED. Date: 2026-10-06. Skill: v0.1. Agent runs: **0**.
No B1/S1 or solving-agent experiment has been executed.

Efficient Coding v0.1 may provide more measurable benefit on tasks requiring
broader repository exploration than on the localized debugging task used in
EVAL-001. No Skill advantage is assumed. The task's navigation demand is an
inference from its observable execution/reporting boundaries, not a measured
agent outcome; an agent may still solve it with a short trajectory.

## Benchmark and selection

- Benchmark: BugsInPy, revision `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Project: Luigi. Bug ID: **9**.
- Upstream buggy commit: `f7e0b7710fd8b12f27625b1efb62a8fde6e206c4`.
- Sanitized starting commit: `a5704160099a5301fd68941d1c05a6f3d0c16fa2`.
- Relevant test: `test/execution_summary_test.py::ExecutionSummaryTest::test_status_with_task_retry`.
- Initial failure: `KeyError: 'ever_failed'` at the test's summary assertion;
  one failed test. The fixture deliberately fails a task on its first run and
  then runs it again. That expected fixture exception is separate from the
  unexpected summary failure.
- Reproduction: stable in two candidate containers, both permanent workspaces,
  and an independently reconstructed snapshot. No application fix was attempted.

[Candidate scoring](EVAL-002-candidates.md) records ten genuine reproduced bugs
and all rejection reasons. Luigi 9 scores 5/9 after a one-point reporting-API
penalty. It was selected over higher-scoring large trees whose tests immediately
identify one implementation module. The observable retry/history sequence links
execution state and a reporting result, offering a different navigation hypothesis
from EVAL-001's direct parser assertion. This does not identify a required fix.
Candidate-selection notes are evaluator-only and never available to solving agents.

## Test provenance and sanitized state

Tests were obtained through the unmodified official `bugsinpy-checkout -p luigi
-i 9 -v 0` process, which transplants the declared test files from its fixed
revision onto buggy application source. The transport used a private shallow
mirror containing only the required two revisions. Preparation may access that
revision to obtain tests; solving cannot access the preparation environment.
No corrected application source, reference/gold patch or solution was inspected.
Fix-bearing checkout stdout remained private and was not exported.

The exact transplanted file is `test/execution_summary_test.py`, SHA-256:
`f9ec5b603919e5a61f54169db6eff3cb6c75087266602d09c3e49a014b0c6234`.
It is **benchmark-provided**, not original to the buggy commit. The hash is in
[EVAL-002-config.json](EVAL-002-config.json) and the
[manifest](results/EVAL-002/manifest.json), and is verified before each run.
Other tracked application/test files match the buggy upstream tree byte for byte.

The final repository was initialized anew from a buggy `git archive`, with only
that test file overlaid and a shared neutral `AGENTS.md` added for the runtime/test
command. It has one root commit with a neutral message, no upstream history,
remotes or shared Git storage. All Git objects, including unreachable objects,
are checked against the frozen inventory. The known fixed commit was explicitly
probed with `git cat-file` and cannot be resolved locally. The fixed hash itself,
fix-bearing messages, benchmark metadata and preparation logs are absent from
both workspaces. Each agent container mounts only its own workspace; it sees no
host preparation directories, evaluator repository, sibling workspace or Docker
socket. External known-solution access remains prohibited by the task; web search
is disabled. This is a local content/history isolation guarantee, not an
assertion of an air-gapped network.

Expected extra support file: `AGENTS.md`, tracked and hash-verified. Dependencies
live in the container, not the repository. No `bugsinpy_bug.info`, patch files,
virtualenv, evaluator notes or Skill is copied into either benchmark checkout.
The entire frozen `test/` tree is mounted read-only in a separate grading container
so agent changes to tests cannot change the success criterion.

## Conditions and configuration

Baseline: a fresh agent/container without efficient-coding installed or invoked.
Treatment: another fresh agent/container with unchanged v0.1 at
`/root/.agents/skills/efficient-coding/SKILL.md`, invoked using the same developer
instruction as EVAL-001: `Use the $efficient-coding Skill v0.1 for this task.`
The Skill stays external to the benchmark repository. Installation/isolation was
verified without a model request. Both use exactly [EVAL-002-task.md](EVAL-002-task.md).

Inherited: Codex CLI **0.160.0**, model **`gpt-6.1-sol`**, reasoning **`medium`**,
web search **`disabled`**, multi-agent **false**, ignored user configuration,
no daemon/session resume, approval policy **never**, a **1,800-second** timeout,
and sandbox **danger-full-access inside the isolated container**. Only auth is
copied from the host; its contents are never printed. The Skill is the sole
intended experimental variable. Changes by either arm are inaccessible to the
other. `--all` starts fresh sessions in B1, S1, B2, S2, B3, S3 order.

Runtime: Python **3.8.20**, pytest **5.4.2**, pinned dependencies in
`EVAL-002-runtime/requirements.txt`. The dataset specifies 3.8.3; this patch-level
adaptation is explicit and shared. Platform-specific dependency dumps were not
installed verbatim; official compile/test helpers used the pinned preinstalled
dependencies. The final image contains no installed Luigi package or benchmark
source. It derives from the frozen EVAL-001 runtime/CLI base.

Frozen local image:
`sha256:d061c543ffcc6143cc93fda23d66f6d86780673486008dd9a6720deb45f97a46`.
Its Dockerfile/pinned requirements and the harness/instrumentation hashes are
recorded. Rebuilt image IDs can differ; a replacement must be deliberately
revalidated/refrozen for **both** arms before any run, never silently substituted.

## Verified workspaces

- Baseline: `/Users/andregiacomini/Documents/GitHub/efficient-coding-skill/experiments/EVAL-002-baseline`
- Skill: `/Users/andregiacomini/Documents/GitHub/efficient-coding-skill/experiments/EVAL-002-skill`

Both HEADs: `a5704160099a5301fd68941d1c05a6f3d0c16fa2`.
Both `git status --porcelain` outputs are empty. No unexpected untracked/ignored
files or setup duplicates exist. Their 337 tracked paths have identical bytes
and modes. Common starting fingerprint:
`b197225d2a08b9a18fa4420a45cd3068f2d8c3e4ca2790e330cf216623d0e8c4`.
See [workspace fingerprints](preparation/EVAL-002/workspace-fingerprints.json).
Failure outputs are [baseline](preparation/EVAL-002/baseline-failure.txt) and
[Skill](preparation/EVAL-002/skill-failure.txt); both show the same test/KeyError.
PID, random worker IDs and elapsed times naturally vary between containers.

Unexpected untracked/ignored files stop a reset and are preserved for review.
Once artifacts are captured successfully, the runner reclones from the single-
commit seed to remove experiment changes, old objects, refs and caches. Required
support files are restored from the seed, not blindly deleted. Python and pytest
caches are disabled in the checkout. Before each model request the runner checks
state/test hashes/history/object inventory and records a deterministic fingerprint.

## Reproduction and run commands

Prerequisites: Docker Desktop running; the frozen runtime image present; host
Codex authentication in `${CODEX_HOME:-$HOME/.codex}/auth.json`. From this evaluator
repository, reset/verify both arms **without** starting a coding agent:

```sh
python3 evals/run-eval.py --eval EVAL-002 --check
```

The exact focused test command inside the runtime is:

```sh
/opt/eval-venv/bin/python -m pytest -q test/execution_summary_test.py::ExecutionSummaryTest::test_status_with_task_retry
```

To reconstruct a missing seed, use the pinned BugsInPy checkout and the tested
setup helper. Existing seeds are verified, never silently replaced:

```sh
python3 evals/setup-EVAL-002.py --bugsinpy /private/tmp/efficient-coding-EVAL-001/BugsInPy
```

The helper executes the official test transplantation in temporary preparation
storage, verifies test hashes and the exact deterministic synthetic commit,
creates only the sanitized seed, deletes the temporary fixed-access environment,
and runs infrastructure checks. It never invokes a solving agent. Seed reconstruction
was independently verified in a temporary evaluator checkout. On another machine,
provide a local BugsInPy checkout at the pinned revision and the same frozen image.

Ready commands for the later experiments (not executed during preparation):

```sh
python3 evals/run-eval.py --eval EVAL-002 B1
python3 evals/run-eval.py --eval EVAL-002 S1
python3 evals/run-eval.py --eval EVAL-002 --all
```

[Instrumentation](INSTRUMENTATION.md) collects native input/output/total/cached
tokens, duration, tool items, observable searches, explicit file reads, unique and
repeated repository reads, test commands, edits, Skill loading and event-receipt
timestamps. Unsupported metrics remain null; explicit reads are not all physical
reads. Infrastructure failure remains separate from bug-fix success. Success will
mean the frozen benchmark test passes in the independent grader, a correctness
proxy rather than proof of complete correctness. Results remain empty until runs.

EVAL-001 and its tag/manifest/raw artifacts remain unchanged. No Skill edit,
application fix, B1/S1 or six-run experiment was performed during this preparation.
