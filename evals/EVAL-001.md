# EVAL-001

Compare the same task from the same repository revision in separate clean runs,
using the same agent, model, settings, and task prompt. Enable the Skill only for
the Skill run. Record observed values; mark unavailable metrics as unknown.

| Setup | Value |
| --- | --- |
| Repository | URL/path and starting revision: |
| Agent | Name and version: |
| Model | Identifier and settings: |
| Task | Exact prompt and acceptance criteria: |
| Baseline run | Run ID/link; Skill disabled: |
| Skill run | Run ID/link; Skill enabled and Skill revision: |

| Metric | Baseline run | Skill run |
| --- | --- | --- |
| Success | | |
| Tests passed | | |
| Tokens | | |
| Duration | | |
| Files inspected | | |
| Tool calls | | |

Use success to record whether acceptance criteria were met. For tests, record
checks run and pass/fail counts. Use total reported tokens, elapsed duration,
distinct files read, and total tool calls; note the measurement source and any
limitations below.

## Notes

Record failures, reruns, differences in conditions, and missing measurements.

## Conclusion

Compare correctness and resource use. State what this experiment supports and
what remains uncertain.
