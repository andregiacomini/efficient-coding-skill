# efficient-coding-skill

An experimental research and engineering project testing whether instruction-only
Agent Skills can help coding agents use resources more efficiently while
preserving correctness. The repository contains Skill versions, an evaluation
harness, frozen task prompts, and recorded experiments.

## Original hypothesis

Coding agents can spend unnecessary context and tokens exploring unrelated files,
rereading information, and repeating tool calls. The original hypothesis was that
instructions encouraging targeted exploration, evidence-driven context expansion,
and progressive validation could reduce this work without sacrificing task success.

We compare fresh coding-agent sessions on identical starting repositories and
frozen prompts, with and without the Skill. Recorded measures include benchmark
success, input/cached/output/total tokens, duration, inspected files, searches,
tool calls, edits, and test results. Later experiments also measure convergence
and activity after the originally failing targeted tests first pass.

These are small, task-specific experiments. **Results do not claim statistical
significance, general effectiveness, or a causal explanation for token changes.**
Additional validation and repeated file reads are not automatically wasted work.

## Skill versions

- **[Efficient Coding v0.1](versions/v0.1/efficient-coding/SKILL.md):** understand
  the task, form initial location hypotheses, explore narrowly, expand with
  evidence, avoid repeated work, validate progressively, and preserve correctness.
- **[Efficient Coding v0.2](versions/v0.2/efficient-coding/SKILL.md):** keeps v0.1
  and adds a concise completion checkpoint intended to limit unnecessary work
  after sufficient correctness evidence, while preserving necessary validation.
  The [exact diff and preregistered hypothesis](versions/v0.2/README.md) explain
  the change.

The root [SKILL.md](SKILL.md) contains v0.2. Both versions remain experimental;
v0.2 is not presented as a demonstrated improvement. [Version hashes](versions/manifest.json)
and Git tags `v0.1` / `v0.2` preserve the evaluated instruction texts.

## Experiments

| Evaluation | Benchmark / task | Conditions and runs | Main finding |
| --- | --- | --- | --- |
| [EVAL-001](evals/EVAL-001.md) | BugsInPy, youtube-dl bug 2; localized debugging | Baseline vs v0.1; 6 runs | Inconclusive; no reliable efficiency improvement |
| [EVAL-002](evals/EVAL-002.md) | BugsInPy, Luigi bug 9; retry-history reporting | Baseline vs v0.1; 6 runs | Positive behavioral signal, not conclusive |
| [EVAL-003](evals/EVAL-003.md) | SWE-bench Verified, Django `django__django-15957`; sliced relationship prefetching, limits and ordering | Baseline vs v0.1; 6 runs | Clear negative efficiency result for v0.1 on this benchmark |
| [EVAL-004 results](evals/results/EVAL-004/analysis.md) | Same frozen Django task; completion-checkpoint comparison | Baseline vs v0.1 vs v0.2; 9 runs | No meaningful aggregate efficiency improvement from v0.2 over v0.1 |

**EVAL-001:** all six runs passed the benchmark test. Token usage varied, and no
reliable resource-efficiency improvement was demonstrated. The historical
record includes contamination limitations. See the [analysis](evals/results/EVAL-001/analysis.md).

**EVAL-002:** all six runs passed. Repository searches decreased in every Skill
pair; mean and median tokens decreased **7.27%** and **2.96%**, with mixed paired
directions. Small sample size, narrower treatment validation, and an environment
persistence issue limit interpretation. See the [report](evals/results/EVAL-002/report.md)
and [frozen manifest](evals/results/EVAL-002/manifest.json).

**EVAL-003:** all six runs passed the 113-test verifier. v0.1 used more tokens in
every pair: **+110.61%, +38.94%, +18.00%**. Mean tokens increased **52.98%** and
median **52.79%**. Earlier convergence followed by more work in the first Skill
run did not repeat consistently. This is a negative efficiency result for this
benchmark/configuration, not a claim that the Skill is generally harmful.
See the [complete analysis](evals/results/EVAL-003/analysis.md) and
[frozen manifest](evals/results/EVAL-003/manifest.json).

**EVAL-004:** all nine runs passed the same 113-test verifier. The primary
comparison was v0.1 → v0.2. v0.2 had fewer aggregate post-success searches and
explicit reads, but mean tokens increased **2.59%**, median **0.82%**, and mean
post-success tool calls were unchanged. Duration did not improve in aggregate.
Final edits were revalidated in **2/3 runs in each condition**; passing the
external verifier does not validate newly edited solver tests. See the
[complete analysis](evals/results/EVAL-004/analysis.md),
[aggregate metrics](evals/results/EVAL-004/posthoc-report.md), and
[completion audit](evals/results/EVAL-004/analysis-manifest.json).
The [preparation document](evals/EVAL-004.md) and its manifest remain historical
pre-run records; the linked complete analysis contains the final results.

## What we've learned so far

- Coding-agent token usage has substantial run-to-run variance in these experiments.
- Fewer searches or tool actions do not necessarily translate into fewer tokens.
- Instruction-only efficiency guidance changed observable behavior in some runs,
  including exploration and validation patterns; this does not establish causation.
- v0.1 did not produce reliable efficiency improvements across benchmarks.
- EVAL-003 showed a clear negative efficiency result for v0.1 on that benchmark.
- The v0.2 completion checkpoint did not produce a meaningful aggregate efficiency
  improvement over v0.1 in EVAL-004.
- Correctness was preserved in the evaluated runs according to their benchmark
  criteria. These checks are correctness proxies, not exhaustive proofs.

## Current direction

The next research direction is likely to explore **context acquisition and
clarification before coding**, rather than continue optimizing generic efficiency
instructions. This is a research direction, not an implemented clarification
system or an existing feature. No v0.3 or EVAL-005 is included.

## Reading and reproducing the work

Start with the experiment documents and linked reports above. Historical raw
traces, patches, test outputs, manifests, and archived instrumentation are retained
as evidence; conclusions have not been rewritten. Evaluation freezes are tagged
`eval-001`, `eval-002-prep`, `eval-002`, and `eval-003`. EVAL-004 completion is
recorded in its analysis manifest; it has no evaluation tag yet.

The [instrumentation definitions](evals/INSTRUMENTATION.md),
[EVAL-004 post-hoc definitions](evals/EVAL-004-posthoc.md), and
[workspace lifecycle protections](evals/WORKSPACE-LIFECYCLE.md) explain the measures
and integrity checks. Run the existing synthetic harness tests from the repository
root without starting coding-agent experiments:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s evals -p 'test_*.py' -q
```

Local benchmark workspaces, sanitized Git seeds, virtual environments, credentials,
and Docker images are not committed. A clone alone is not a ready-to-run benchmark
environment. Preparation documents describe required frozen inputs and runtime
setup, including exact seed/image requirements. Absolute host paths and identities
inside historical logs/manifests describe the original runs; they are evidence,
not documentation navigation links or portable defaults. Raw traces and patches
must stay outside solver workspaces to avoid exposing solutions to later runs.
