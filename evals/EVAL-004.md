# EVAL-004 — completion checkpoint on the frozen EVAL-003 Django task

Status: **PREPARED; NO SOLVING RUNS**. All three arms reproduced the expected
109 passing tests / 4 errors, with clean workspaces and no untracked/ignored files. The benchmark is SWE-bench Verified,
Django `django__django-15957`, dataset revision
`c104f840cc67f8b6eec6f759ebc8b2693d585d4a`. This reuses the exact EVAL-003
sanitized repository; no new benchmark was selected or solution inspected.

## Preparation verification

All three workspaces have HEAD `7e9cb01fe632404d84e1da569ebd6fafa4e0aa9d`,
empty `git status --short` and the same full fingerprint:

`1c8165dad3aa453b8131bcd9478691f120ff3b220998dd976381d35d056911f8`.

| Arm | Workspace | Skill visibility |
| --- | --- | --- |
| B | `experiments/EVAL-004-B` | No Skill |
| V1 | `experiments/EVAL-004-V1` | Only v0.1, frozen SHA-256 verified |
| V2 | `experiments/EVAL-004-V2` | Only v0.2, frozen SHA-256 verified |

The repository archive SHA-256 is
`ea494d2f69cfe6a2409c5c714e2257e9b423800f80d25791652d696bcc1367d9`,
identical to EVAL-003's sanitized seed. Preparation recorded one own-workspace
mount per solver, matching Python/CLI versions and zero model requests in the
[three isolation records](preparation/EVAL-004/). All **48 synthetic harness tests**
passed. Root identities/fingerprints remained intact after read-only reporting.
No B/V1/V2 run directory exists and no solver was executed.

## Hypothesis and preregistered comparisons

The primary hypothesis is that v0.2's completion checkpoint reduces unnecessary
work after sufficient correctness evidence compared with v0.1, while preserving
benchmark success. It remains untested. EVAL-003 showed increased tokens/tool calls
in all pairs and additional post-success activity, but did not establish that all
additional checks were unnecessary, or that the Skill is generally harmful.

| Arm | Skill | Runs |
| --- | --- | --- |
| B | No Efficient Coding Skill | B1, B2, B3 |
| V1 | Exact frozen v0.1 text | V1-1, V1-2, V1-3 |
| V2 | v0.2 with section 7 added | V2-1, V2-2, V2-3 |

Primary comparison: **V1 → V2**. Secondary: B → V1 and B → V2. Report all
individual runs, paired repetitions and available-value means/medians. Percentage
change is `(right - left) / left * 100`; a zero/unavailable denominator remains
unavailable. Three runs per condition support no statistical-significance claim.
Failed benchmark runs remain in aggregates; infrastructure failures are flagged
and excluded. Neither post-success activity nor lower tokens alone prove efficiency.
Correctness and adequacy of validation must be considered together.

## Frozen controls

- Upstream base: `f387d024fc75569d2a4a338bfda76cc2f328f627`.
- Sanitized one-commit HEAD: `7e9cb01fe632404d84e1da569ebd6fafa4e0aa9d`.
- Repository archive SHA-256 and three equal configuration-inclusive fingerprints
  are recorded in [manifest.json](results/EVAL-004/manifest.json).
- [Frozen prompt](EVAL-004-task.md) is byte-for-byte EVAL-003's prompt:
  SHA-256 `9c4b3148539451ca326ee780612d3d4a4297e3b49204fd100c8af60e80312097`.
- Codex CLI **0.160.0**, model **gpt-6.1-sol**, reasoning **medium**, web disabled;
  `danger-full-access` inside the isolated container, approval `never`,
  `--ignore-user-config`, `--no-daemon`, fresh sessions, multi-agent disabled.
- Exact same source-free Docker image:
  `sha256:d307634c1cc808d6f98d111060e5bef40a5f5c4cfeb80d05263fa9fc3decfb3c`.
- Python **3.10.16**, same EVAL-003 virtual environment/pinned dependencies and
  environment; SQLite test databases, no external database service.
- Agent command, task bytes and runtime are identical across arms except explicit
  Skill invocation/version. Both Skill arms use the same discovery path/name,
  `/root/.agents/skills/efficient-coding/SKILL.md`.
- [Skill snapshots and hashes](../versions/manifest.json) are external to all
  benchmark repositories. V1 never receives V2; B receives neither.
- [Configuration](EVAL-004-config.json) pins runtime, tests, input hashes,
  conditions, run order, parser and preparation helper. No instrumentation change:
  schema **4**, revision **4.1**, parser bytes identical to frozen EVAL-003.

The common full fingerprint includes evaluator configuration, which differs from
EVAL-003 because this experiment declares three arms. It must match across all
three EVAL-004 roots. Repository HEAD, full Git object inventory and the complete
repository archive are identical to EVAL-003; the cross-evaluation fingerprint
change does not indicate a changed Django snapshot.

## Verifier and first success

The unchanged verifier requires **all 113 exact frozen test IDs to report `ok`,
no skips and exit 0**. It includes all four official FAIL_TO_PASS and 89
PASS_TO_PASS tests plus 20 additional cases. This local strict adapter is not the
full official SWE-bench Docker harness. Preparation must reproduce **109 pass,
4 errors, no skips**, with `TypeError: Cannot filter a query once a slice has been taken.`

Inside the matching runtime:

```bash
/opt/eval-003-venv/bin/python tests/runtests.py prefetch_related --settings=test_sqlite --parallel=1 --verbosity=2
```

The same four original regression IDs are in PrefetchLimitTests:
`test_foreignkey_reverse`, `test_m2m_forward`, `test_m2m_reverse`, `test_reverse_ordering`.
The evaluator mounts the entire original test tree read-only for grading, so
solver edits to tests cannot change the success criterion.

**First success is identical to EVAL-003**: the earliest completed structured test
execution whose observable output includes a unittest test-count report and
unambiguous `ok` results for each of the four originally failing regression IDs.
It measures targeted regression success, not full benchmark success. No inference
from agent prose, generic `OK`, or missing test IDs is allowed. Post-success activity
counts only tool items first observed after that successful item's completion;
overlapping/already-started items are excluded. Unidentifiable success/unsupported
operations leave applicable metrics unavailable, not guessed or zero.

## Metrics

Primary: **success rate, total tokens, total tool calls, duration, post-first-success
tool calls, repository searches, repository file reads and test executions**.

Retain existing input/cached/output tokens, explicit/repeated/unique reads, searches,
tests, edits/modified paths, Skill load events and observable trajectories. Secondary
convergence measures include time to first edit, first test and first targeted
success, pre-edit searches, unique repository/source files and tool calls. Definitions
remain in [INSTRUMENTATION.md](INSTRUMENTATION.md); token totals already include
cached input. Reads mean observable explicit inspections, not every physical read;
test executions count recognized invocations, not necessarily successful tests.

## Isolation, preparation and lifecycle

Separate independent clones: `experiments/EVAL-004-B`, `experiments/EVAL-004-V1`,
`experiments/EVAL-004-V2`. They have no remotes, shared Git storage or extra history.
Each solver container mounts only its own root and receives one matching Skill
copy, or none. Evaluator notes, results, traces, patches, sibling workspaces, host
Skill installations and Docker socket are never mounted. Host login credentials
are copied into fresh containers as in EVAL-003; they are not written to artifacts.
Web search is disabled; the runtime is not network air-gapped. The frozen prompt
prohibits external known solutions/reference patches/future source.

[Lifecycle protections](WORKSPACE-LIFECYCLE.md) retain root device/inode, verify
HEAD/status/content/object inventory and registered fingerprint before inference,
quiesce containers before capture, reset only root children from a verified seed
and check every arm again after reset/report. Missing/replaced roots, unexpected
untracked/ignored files, changed inputs/fingerprints, infrastructure errors and
contamination stop execution. Reports never reset workspace contents. Failed
artifact capture retains dirty evidence; do not silently repair it or rerun.

Preparation uses only the existing neutral EVAL-003 **bare seed**, never a solved
checkout. Reproduce/check on this host without any model request:

```bash
python3 evals/setup-EVAL-004.py
python3 evals/run-eval.py --eval EVAL-004 --check
```

On another host, supply an independently transferred exact sanitized bare seed
with `--seed-path /absolute/path/to/seed.git` and restore the pinned runtime image.
The helper verifies the full object inventory and archive before cloning with
`--no-local`. Missing runtime/seed/authentication stops preparation. Host root
identities are registered locally; they are not part of the common fingerprint.
Existing unregistered roots are rejected and retained. Setup must precede runs;
plain `--prepare` requires the EVAL-004 seed already available. Never copy solved
workspaces, raw agent traces, patches or evaluator directories into solver roots.

## Commands prepared for future authorization

Run from this project root. **No command below was executed during preparation.**

Individual runs:

```bash
python3 evals/run-eval.py --eval EVAL-004 B1
python3 evals/run-eval.py --eval EVAL-004 V1-1
python3 evals/run-eval.py --eval EVAL-004 V2-1
```

Complete condition (alternative to an interleaved full experiment):

```bash
python3 evals/run-eval.py --eval EVAL-004 --condition B
python3 evals/run-eval.py --eval EVAL-004 --condition V1
python3 evals/run-eval.py --eval EVAL-004 --condition V2
```

All nine, in frozen interleaved blocks B1/V1-1/V2-1, B2/V1-2/V2-2, B3/V1-3/V2-3:

```bash
python3 evals/run-eval.py --eval EVAL-004 --all
```

Do not mix execution modes on already populated result directories: completed
runs are never overwritten or skipped silently. Use the full interleaved order
for the planned comparison; whole-condition commands are alternative schedules
and their order must be reported if used. A project-level runner lock prevents
concurrent execution. Each invocation creates fresh agent containers/sessions;
benchmark failure alone is recorded, whereas infrastructure/integrity failure
stops the sequence.

```bash
python3 evals/run-eval.py --eval EVAL-004 --report
```

The [report](results/EVAL-004/report.md) and [aggregate](results/EVAL-004/aggregate.json)
are currently empty of run results. The report generator already supports all
three comparisons and records available-value denominators. Interpretation and
conclusion remain pending; EVAL-004 preparation is not evidence for v0.2 efficacy.
