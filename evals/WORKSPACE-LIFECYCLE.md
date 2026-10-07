# Evaluation workspace lifecycle

## Finding and historical boundary

EVAL-002's six run-level before/after checks and first final audit passed. A later
post-report audit found the baseline path absent, with suffix-named paths nearby.
No recorded run reported an infrastructure failure; the 78 captured files retain
their hashes. The cause is **not proven**. Filesystem synchronization or another
process must not be asserted as the cause without evidence.

The old `reset_workspace()` cloned into a sibling `.reset` directory, recursively
removed the existing root, then renamed the clone. This introduced an avoidable
interval with no root and silently recreated a missing root on the next reset.
It is a lifecycle hazard, not proof that it caused the later disappearance.
The old `report()` only wrote evaluator output; no post-report workspace cleanup
was found in the runner. Historical behavior/inputs remain in tag `eval-002`.

## Mutation/cleanup inventory

| Location | Old behavior | Current boundary |
| --- | --- | --- |
| `run-eval.py: reset_workspace` | Clone, hard reset/clean staging, remove workspace root, rename staging | Stage a verified independent clone in OS temporary storage, replace only root children, retain and verify root device/inode |
| `run-eval.py: preflight` | Remove/recreate frozen test fixtures | Create fixtures only with explicit `--prepare`; otherwise compare complete fixture inventory without changing it |
| `run-eval.py: run_one` | Recreate before run, recreate after capture, then report | Verify prepared roots before inference; reset captured contents after stopping containers; verify both roots before/after reporting |
| `run-eval.py: check_only` | Recreate both roots during checks | Read prepared state, run graders, verify state; no root/content reset |
| `run-eval.py: report/reanalyze` | Write evaluator-derived results | Check workspace state before/after report, write only evaluator outputs; frozen evals reject reanalysis |
| `run-eval.py: remove_container` | Force-remove container | Container filesystem only; bind-mounted workspace is not deleted |
| `run-eval.py: save` | Replace temporary metadata/report files | Evaluator results/preparation files only, never workspace roots |
| `setup-EVAL-002.py` | Temporary transport/checkout/snapshot cleanup; create bare seed and call checks | Frozen EVAL-002 is rejected before changes; historical reconstruction uses its tag |
| `reset-EVAL-001.sh`, `EVAL-001-setup.sh` | Delegate to shared `--check` | Current CLI rejects all frozen workspace mutations; historical behavior remains in its tag |
| `test_run_eval.py` | Cleanup synthetic temporary fixtures | Synthetic OS-temporary directories only; no historical benchmark workspace |
| Future preparation | Explicit snapshot/seed generation and initial cloning | Roots created once, never implicitly adopted/replaced; temporary preparation cleanup cannot target experiment roots |

No workspace cleanup occurs after report generation. Releasing the evaluator's
`.runner.lock` is bookkeeping outside solver mounts, not workspace cleanup.

## Protections for new evaluations

`--prepare` explicitly creates both independent roots and records each absolute
path, device/inode and frozen fingerprint in evaluator-only
`evals/preparation/EVAL-NNN/workspace-registration.json`. Existing unregistered
roots are retained and rejected. A missing/replaced registered root is rejected,
never automatically recreated. Portable reproduction requires explicit preparation
on the new host; host-specific identity is not part of the common fingerprint.

Runs verify existence, identity, HEAD, cleanliness, full Git object inventory,
test/support hashes and the registered fingerprint before any model request.
Metadata includes before/after workspace snapshots. `lifecycle.jsonl` records
checkpoints for both arms and logs each harness removal with operation, absolute
target, UTC timestamp and reason **before** execution; logging failure prevents
the removal. Logs are evaluator-only and add no agent instructions.

Post-run reset requires stopped containers and successful artifact capture. It
replaces root children, including Git storage, from a verified `--no-local` clone.
This removes changed source, caches, ignored files, refs/hooks and unreachable
objects without deleting or renaming the prepared root. Every root-child removal
and temporary staging cleanup is logged. Unexpected pre-run untracked/ignored
files still fail and are retained. Staging failure leaves the original root intact.
Interrupted restoration remains detectable and does not silently repair itself.

Report generation reads workspace state with Git optional writes disabled, writes
only evaluator reports/logs and checks both roots again afterward. Disappearance,
identity/content changes or fingerprint mismatches fail loudly. No reset is called
by the reporter. These protections detect external interference at checkpoints;
they cannot prevent arbitrary external filesystem changes between checks.

## Verification

Synthetic tests cover root identity preservation, independent Git object cleanup,
contamination retention, missing/replaced roots, staging failure, failed artifact
capture, read-only reporting (including Git index refresh), disappearance/content
changes during reporting, frozen-eval rejection, and observable convergence metrics.

```sh
python3 -m unittest discover -s evals -p 'test_*.py' -q
```

No real coding-agent request is made by these tests.

During private EVAL-003 snapshot authoring, temporary cleanup encountered a
`gc.pid` disappearing, consistent with concurrent Git maintenance. That separate,
observed file-removal race does **not** explain EVAL-002's missing root. Future
harness/setup Git commands disable automatic GC/maintenance and detached GC;
prepared and reset Git configurations also disable automatic maintenance.
Read-only Git operations additionally disable optional index writes. The private
cleanup retry was logged; no experiment root was deleted to address it.
