# EVAL-003 candidate selection

Hypothesis: unchanged Efficient Coding v0.1 may be more useful when a task
requires discovering and coordinating behavior across multiple repository parts.
Selection predicts navigation demand; it does not assume a Skill benefit or
claim how many files a correct solution actually changes.

## Data and isolation

Four shortlisted tasks use the official SWE-bench Verified `test` split,
`princeton-nlp/SWE-bench_Verified`, revision
`c104f840cc67f8b6eec6f759ebc8b2693d585d4a`.
The Parquet reader projected only repository/task IDs, base revision, problem
statement, test-only patch, FAIL_TO_PASS/PASS_TO_PASS, version and environment
setup revision (not fetched). **Gold `patch` and `hints_text` were never decoded,
printed or used.** The binary transport stayed in evaluator-private temporary
storage and is never mounted to a solving container. No fixed source, future
commit, reference answer or solution-derived changed-file count was inspected.

Only exact base commits were fetched into private shallow checkouts. Benchmark
patch paths were restricted to `tests/`; application source was not changed.
Evidence below comes from tasks, tests, reproduced output and base-tree structure.
[Allowed dataset schema](https://github.com/SWE-bench/SWE-bench/blob/main/docs/guides/datasets.md)
and [official evaluation](https://www.swebench.com/SWE-bench/guides/evaluation/)
explain task/base/test data and benchmark criteria.

BugsInPy remained an option, but EVAL-001/002 showed localized observed working
sets despite structural selection hypotheses. SWE-bench supplies issue text and
explicit regression/nonregression lists, allowing selection by requested behavior
instead of another single failing assertion. The trade-off is a small local
Django verifier adapter and test-only patch transplantation. We reuse Docker and
the frozen Codex image, add pinned Python/test dependencies, and use SQLite;
no database service, full SWE-bench infrastructure stack or new evaluator backend.

## Scoring

Score out of 10: cross-component behavior (0–3), plausible implementation areas
(0–3), externally observable test diversity (0–2), local runtime/reproducibility
(0–2). Subtract 1 for an implementation-localizing traceback. Scores are evaluator
judgment from permitted evidence, not solution-derived facts.

| Project / task | Exact base revision | Reproducibility | Repository size | Structural breadth / plausible areas | Localization | Expected navigation | Runtime / environment | Score |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| Django / `django__django-13121` | `ec5aa2161d8015a3fe57dcbbfe14200cd18f0a16` | 179 tests, expected duration-expression error; 4 unrelated backend skips | 6,267 tracked files; 850 production Python; 37.53 MB | Expression construction, SQL compilation, duration conversion, backend operations; ~3–4 areas | Trace identifies a conversion endpoint; single new failing case | Trace value representation across expression/backend boundary | 1.801 s including container; SQLite, no server | 6 |
| Django / `django__django-15525` | `fbacaa58ffc5a62456ee68b90efa13957f761ce4` | 58 tests, expected natural-key dependency error; 1 unrelated skip | 6,617 files; 863 production Python; 40.97 MB | Fixture loading, serializer construction, related descriptors, database routing; ~4 areas | Long trace exposes serializer construction; one failing scenario | Follow database alias through dependency resolution and lazy relation access | 1.626 s; two in-memory SQLite aliases | 7 |
| Django / `django__django-15629` | `694cf458f16b8d340a3195244196980b2dec34fd` | 123 tests, 2 expected collation failures; 1 unrelated skip | 6,629 files; 863 production Python; 41.41 MB | Model relationship metadata, schema generation, migration create/alter behavior; ~3 areas | SQL examples constrain the missing property, without one Python fix line | Relate PK/FK metadata to initial and altered schema | 2.286 s; SQLite proxy for original MySQL issue limits backend validation | 8 |
| Django / `django__django-15957` | `f387d024fc75569d2a4a338bfda76cc2f328f627` | 113 tests: 109 pass, 4 expected errors, no skips | 6,647 files; 863 production Python; 41.73 MB | QuerySet/Prefetch coordination, generated relation managers, query limits/ordering, SQL execution; ~4 areas | Trace surfaces the generic slice guard; it does not implement per-parent behavior | Discover FK and both M2M pathways, limits/offsets, ordering, caching and query-count contract | 1.955 s; SQLite, all official cases executed | **9** |

Runtime is one measured preparation execution, not an agent duration estimate.
Production Python counts are tree inventory, not files inspected by an agent.
[Reproduction evidence](preparation/EVAL-003-candidates/) records commands,
outputs, allowed task metadata and tree sizes for all four candidates.

An earlier title-screened candidate, `django__django-11138`, was rejected before
checkout: its issue points directly to a MySQL implementation line and its single
regression case offers less navigation opportunity. It is not in the eligible
shortlist and no solution data was consulted.

## Selected: Django prefetch with sliced querysets

`django__django-15957` offers the strongest combination of API variants, observable
contracts and complete cheap local validation. The four new tests exercise M2M
forward, M2M reverse, FK reverse and reversed ordering. They compare per-parent
related objects with the expected slices, require a bounded number of SQL queries
and verify that results are already available without additional queries.

All four fail with `TypeError: Cannot filter a query once a slice has been taken.`
The remaining 109 prefetch-module tests pass. All 4 official FAIL_TO_PASS and 89
PASS_TO_PASS identifiers map to executed test methods, including docstring aliases.
The local success criterion runs all 113 tests, adding 20 cases to the official
93-item matrix. No reference implementation was applied as a positive control.

**Why more opportunity for the Skill?** The base code has multiple distinct
`get_prefetch_queryset` implementations in generated relation managers, a
separate Prefetch coordination layer in `django/db/models/query.py`, and separate
query-state/compiler modules for limits and ordering. A developer plausibly needs
several production files plus model fixtures/tests to understand these boundaries.
The generic slice guard is a symptom shared by relation types; simply finding
that line does not satisfy the per-parent slicing, ordering and query-budget
contracts. This is materially different from one parser assertion or missing
summary dictionary entry in the earlier experiments.

Potential useful working-set locations include the coordinator, related
managers/descriptors, query-state representation, compiler and relation fixtures.
These are hypotheses from the base tree, **not a prescribed fix**, and these notes
are never exposed to the solving agents. A capable agent may still solve this
with few reads or a single production edit; actual navigation will be measured.

The selected workspaces are built from an exact base archive, the official
**test-only** patch and shared runtime instructions, then initialized with one
neutral root commit. No upstream Git history or evaluator notes remain. The
Skill stays external and is installed/invoked only for future S runs.
