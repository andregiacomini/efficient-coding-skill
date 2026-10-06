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
