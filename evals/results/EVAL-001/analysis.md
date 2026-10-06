## Executive summary

All six runs passed the original benchmark test. The treatment median was higher
in total tokens (117,533 vs 100,900), similar in duration (33.840s vs 33.518s), and
one item higher in exposed tool activity (10 vs 9). Every treatment performed one
standalone Skill-file read. Excluding that item, both conditions have a median of
9 tool items.

B2/S2 is not simply identical activity with different token usage. S2 performed
one more repository tool item and one more search invocation, but fewer explicit
repository file-read requests and narrower final validation. Those observable
differences do not quantitatively explain its 38.33% higher total tokens. Almost
all of the difference is reported input usage; cached-input accounting differs
substantially. No causal Skill effect or exact token overhead can be isolated.

Scope: only observable commands, file-change items, tool outputs and aggregate
usage are analyzed. No reasoning/agent-message text, reference patch, future
version, or external solution description was used. Commands are never executed
by this analysis. Raw artifacts and benchmark inputs were preserved unchanged.

## B2 vs S2 trajectory

Sources: [B2 raw trace](B2/codex.jsonl), [S2 raw trace](S2/codex.jsonl), their original
metadata, and derived [B2 trajectory](B2/trajectory.json) / [S2 trajectory](S2/trajectory.json).
Item IDs identify the recorded actions; compound commands remain one tool item.

B2:

1. `item_1`: execute the single failing benchmark test; failure reproduced.
2. `item_2`: `git status --short`; content search across `youtube_dl` and `test`.
3. `item_3`: inspect `common.py` lines 1720–2050 and the test file lines 480–690;
   discover `AGENTS.md`/MPD filenames using `rg --files`.
4. `item_4`: read `AGENTS.md` and the MPD fixture; recursive content search across
   the extractor/test directories, piped to `head`; inspect test-file lines 1–85.
5. `item_6`: one structured edit of `youtube_dl/extractor/common.py`.
6. `item_7`: rerun the original benchmark test; passes.
7. `item_8`: execute `test.test_InfoExtractor` and `test.test_YoutubeDL`; 30 tests pass.
8. `item_9`: diff whitespace check, statistics, and source diff.

S2:

1. `item_1`: read `/root/.agents/skills/efficient-coding/SKILL.md`; Skill content is
   present in completed tool output.
2. `item_2`: `pwd`, clean-status check and targeted filename discovery.
3. `item_3`: read `AGENTS.md`; content search in the named test and source files.
4. `item_4`: execute the single failing benchmark test; failure reproduced.
5. `item_5`: inspect test-file lines 492–680 and `common.py` lines 1730–2015.
6. `item_6`: inspect `common.py` lines 2010–2045; content searches in the MPD
   fixture, named extractor files (including `youtube.py`) and the test file;
   one output stream is truncated with `head`.
7. `item_8`: one structured edit of `youtube_dl/extractor/common.py`.
8. `item_9`: rerun the original benchmark test; passes.
9. `item_10`: diff whitespace check, statistics, and source diff.
10. `item_11`: execute `test.test_InfoExtractor`; 9 tests pass.

| Observable | B2 | S2 |
| --- | ---: | ---: |
| First repository action | Execute failing test | pwd/status/filename discovery |
| Exposed tool items | 8 | 10 |
| Tool items excluding standalone Skill loading | 8 | 9 |
| Shell-command items | 7 | 9 |
| Parsed shell operations | 16 | 18 |
| Repository search invocations, including filename discovery | 3 | 4 |
| Explicit repository file-read requests | 5 | 4 |
| Unique explicit repository read targets | 4 | 3 |
| Repeated repository read targets | 1 | 1 |
| Explicit Skill-file reads | 0 | 1 |
| Explicit reads including Skill | 5 | 5 |
| Structured edit operations | 1 | 1 |
| Tool items before first edit, including Skill | 4 | 6 |
| Repository tool items before first edit | 4 | 5 |
| Recognized agent test invocations | 3 | 3 |
| Test cases reported by the three invocations, including reruns | 32 | 11 |
| Final wider validation | 30 tests | 9 tests |
| Input tokens | 86,312 | 119,561 |
| Cached input tokens, already included in input | 61,824 | 106,880 |
| Input minus cached input | 24,488 | 12,681 |
| Output tokens | 739 | 859 |
| Total tokens | 87,051 | 120,420 |
| Agent duration | 28.505s | 36.090s |
| Seconds until first edit/test | unavailable | unavailable |
| Tokens before first edit | unavailable | unavailable |

Repository inspection order:

- B2: `common.py` → test file → `AGENTS.md` → fixture → test file again.
- S2: `AGENTS.md` → test file → `common.py` → `common.py` again; Skill loading precedes these reads.

B2 rereads a different, nonoverlapping part of the test file (1–85 versus 480–690).
S2 reads a continuation of `common.py`, with a six-line overlap (2010–2015).
Counting a repeated filename does not establish unnecessary work.

The unique-file counts above describe **explicit content-inspection requests**,
not all files touched by content searches, tests, imports or other programs. S2
also searches `youtube.py` without a standalone full/range read. B2's directory
searches potentially cover more files, but neither physical file-read totals nor
all scanned filenames are available. Filename discovery alone is not a content read.

Neither historical trace has per-item timestamps or per-action token usage.
Metadata gives total duration only. Event order cannot be converted into seconds,
and aggregate end-of-turn usage cannot be allocated to the pre-edit phase.

## Skill overhead

S1, S2 and S3 each start with exactly one standalone `cat` of the frozen Skill,
with its content present in completed output. The baseline traces contain none.
This is a directly measured loading action, separate from the developer-level
invocation request recorded in metadata. Discovery/catalog/instruction token
costs are not itemized by Codex and cannot be measured exactly here.

| Pair | Raw B/S tool items | After removing the measured Skill-load item |
| --- | --- | --- |
| B1/S1 | 9 / 10 | 9 / 9 |
| B2/S2 | 8 / 10 | 8 / 9 |
| B3/S3 | 9 / 10 | 9 / 9 |

Thus the one-item difference between condition medians is explained by the
observed loading action. B2/S2 has another repository activity difference; it
cannot be assigned to fixed loading overhead. Removing one tool item is an
activity normalization, **not** a subtraction of estimated tokens or elapsed time.

The B2/S2 total-token difference is 33,369 (+38.33%): input contributes 33,249 and
output 120. Cached-input usage is 45,056 higher in S2; noncached reported input
is 11,807 lower. Cached input is already included in reported input and must not
be added again. These are accounting differences, not proof that caching or the
Skill caused the additional model work. No cost inference is made.

Before the edit, repository tool outputs contain 37,590 characters in B2 versus
33,390 in S2 (35,166 when including Skill output). This direct output-size count
also fails to support a simple claim that S2 read substantially more repository
text. Characters are not token counts, and aggregate model input can include
repeated contexts and other material not separated in the trace.

## Behavioral differences

S2 begins with targeted discovery rather than reproducing the test first. It
uses mostly explicit file search targets and one extra search invocation. B2
uses recursive directory searches, reads the full named MPD fixture, and inspects
one more distinct repository file through explicit read commands. There is no
observable basis for claiming that S2 broadly explored more repository content.

Both make one edit in the same source file, run three test commands, and inspect
the final diff. B2's wider validation includes the YoutubeDL test module; S2's
wider validation includes only InfoExtractor. That same validation-scope pattern
appears in all three baseline and all three treatment traces: 32 reported test
cases across baseline invocations versus 11 across treatment invocations,
counting repeated execution. S2 did not validate more aggressively.

The treatment median has more search invocations (4 vs 3), fewer explicit
repository reads (3 vs 5), fewer unique explicit read targets (3 vs 4), and fewer
repeated filename reads (0 vs 1). These small descriptive patterns are observable,
but a Skill-caused change is not established by three runs per condition.

## What we can conclude

- All six solutions passed the original, independently graded benchmark test.
- Every treatment loaded the Skill once; the baseline did not expose a loading action.
- Most task activity is similar and localized: one source edit, three test commands
  and a final diff check, with modest exploration/validation differences.
- The extra median tool item is accounted for by Skill loading; B2/S2 also has
  one extra repository tool item.
- Current v0.1 did not show total-token savings on this task. B2/S2 has observable
  differences, but they do not establish a quantitative or causal explanation
  for the 38.33% token gap.
- Historical explicit command/read/search/test metrics and cached input can be
  recovered. Historical phase timings and pre-edit tokens cannot.

## What we cannot conclude

There are only **three runs per condition**, **high run-to-run token variance**,
**one small/localized debugging task**, and **no statistical significance**.
Baseline total tokens range from 87,051 to 124,398; treatment from 100,888 to
120,420. The within-baseline spread (37,347) exceeds the B2/S2 gap (33,369).

We cannot attribute the gap to a particular Skill instruction, prove that fewer
explicit reads means fewer physical reads, assign exact token/time overhead to
Skill loading, measure pre-edit token spending, or claim general software
correctness from one benchmark. Model routing, service variability and provider
caching are not controlled or itemized by these traces. A fixed alternating order
also does not fully counterbalance time/caching effects.

The evidence reveals no clear, repeatable behavioral problem caused by a specific
Skill instruction. Do not change v0.1 on this basis.

## Recommended next experiment

Choose **both, in this order**: add EVAL-002 with a task that requires broader
repository exploration, then collect more repetitions of both frozen benchmarks
with a predeclared, counterbalanced order. Keep v0.1 unchanged. The broader task
addresses the Skill's intended scope; repetitions help characterize variance.
Use the new receipt-timing sidecar and command analysis, and assess benchmark
success alongside efficiency. This is a recommendation only; no new Codex runs
were performed during this analysis.

Integrity audit: all 69 original raw/frozen input hashes were unchanged after
reanalysis; configuration and tracked benchmark contents still match the frozen
state. The final audit also observed untracked duplicate files in a working
benchmark copy (suffixes `2`/`3`). They were not removed or interpreted by the
analysis, and do not change the frozen historical traces. Preserve/reconcile
these external workspace artifacts before a future evaluation. Audit details:
[raw-artifact-integrity.json](raw-artifact-integrity.json).
