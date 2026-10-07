# efficient-coding-skill

An experimental, instruction-only Agent Skill for coding tasks.

Coding agents can spend unnecessary context and tokens exploring unrelated files,
rereading information, and repeating tool calls. We are investigating whether a
Skill that encourages targeted exploration and evidence-driven context expansion
can reduce this waste without sacrificing correctness.

The hypothesis is unproven. We will compare coding-agent runs with and without
the Skill on the same tasks, using comparable conditions. We will measure:

- Success: whether the requested task was completed correctly.
- Tokens: total reported token usage.
- Duration: elapsed time for the run.
- Files inspected: distinct files read.
- Tool calls: total calls made.
- Test results: checks run and their outcomes.

The Skill is in [SKILL.md](SKILL.md). Record the first comparison in
[evals/EVAL-001.md](evals/EVAL-001.md).

## Experiments

| Eval | Task type | Skill | Runs | Result |
| --- | --- | --- | --- | --- |
| [EVAL-001](evals/EVAL-001.md) | Localized debugging | v0.1 | 6 | Inconclusive |
| [EVAL-002](evals/EVAL-002.md) | Broader debugging / retry-history behavior | v0.1 | 6 | Positive signal, inconclusive |
| [EVAL-003](evals/EVAL-003.md) | Repository navigation / sliced relationship prefetch | v0.1 | 6 | NEGATIVE EFFICIENCY RESULT FOR v0.1 |
| [EVAL-004](evals/EVAL-004.md) | Same frozen EVAL-003 task; completion checkpoint | baseline / v0.1 / v0.2 | 0 (9 planned) | Prepared; not run |

EVAL-001 is frozen. All six runs passed its benchmark test, but no reliable
resource-efficiency improvement was demonstrated. See its documentation for
variation and contamination limitations.

EVAL-002 is complete and frozen at `eval-002`. All six runs passed. Repository
searches were lower in every Skill pair; mean and median tokens were lower by
7.27% and 2.96%, with mixed paired differences. Three runs per condition, a
localized observed trajectory, narrower treatment validation and an environment
persistence issue prevent causal or general efficiency claims. See the
[report](evals/results/EVAL-002/report.md) and
[frozen manifest](evals/results/EVAL-002/manifest.json). The frozen runs used v0.1.

EVAL-003 is complete and frozen at `eval-003`: both conditions passed 3/3 on the Django task spanning
relationship prefetching, query limits and ordering. Treatment tokens were higher
in all pairs; the earlier successful convergence seen in S1 did not repeat in
S2/S3. These task-specific observations do not establish general effectiveness.
See the [complete analysis](evals/results/EVAL-003/analysis.md) and
[lifecycle protections](evals/WORKSPACE-LIFECYCLE.md). Workspaces retain their
roots and frozen state. Mean tokens increased **52.98%**, median **52.79%**;
paired increases were **110.61%, 38.94%, 18.00%**. Correctness was preserved.
The [frozen manifest](evals/results/EVAL-003/manifest.json) records hashes.
Additional validation is not automatically unnecessary work.

The current Skill is experimental **v0.2**: only a concise completion checkpoint
was added. It preserves necessary validation and stops after sufficient evidence
for the task's success criteria. See the [exact diff and hypothesis](versions/v0.2/README.md).
[Frozen version copies/hashes](versions/manifest.json) and Git tags preserve v0.1.
EVAL-004 prepares fresh baseline/v0.1/v0.2 comparisons on the same Django snapshot,
with identical controls and instrumentation; no new solving-agent runs have been made.
