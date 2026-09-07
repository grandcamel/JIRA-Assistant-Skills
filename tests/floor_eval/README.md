# Knowledge Floor evaluation

A host-triggered job for the Jira and Confluence skills inventories (JAS-53).
It asks every one of the **153 historical gotcha hypotheses** cold, five times
on each floor model, then asks a stronger judge to score each group of five.
Defaults are Sonnet 5, GPT-5.6 Terra and Opus 5 as judge: **1,530 trial calls
plus 306 judge calls**, at most four concurrent subprocesses. The driver uses
only Python 3.10+ standard-library modules on macOS/Linux. No Atlassian site
access or Jira/Confluence credentials are needed.

The job is run **on the host, never in GitHub Actions**, before each plugin
release and after floor-model/judge changes in the organization's
`docs/agents/standing/fleet-posture.json`. The release owner updates
[commands.json](commands.json) to match the new policy and starts a fresh run.
There is no automatic policy watcher or publishing workflow. See the
[Jira release checklist](../../docs/TESTING.md#before-each-plugin-release) and
the Confluence repository's matching checklist. The existing JIRA GitHub test
loop uses the old `plugins/jira-assistant-skills/skills` path and does not
execute this root-level suite; the offline pytest command below does.

## Host execution

From the JIRA-Assistant-Skills checkout, using authenticated host CLI logins:

```bash
python3 tests/floor_eval/run_eval.py --output tests/floor_eval/runs/full
# After interruption or an incomplete run:
python3 tests/floor_eval/run_eval.py --output tests/floor_eval/runs/full --resume
```

Choose one output directory per evaluation input/policy version and retain it
between attempts. Runs are bound to their inventory, commands, selection,
judge semantics and fake/live mode; incompatible resume is refused. Use the
same arguments on resume. Never copy a fake run into a live output directory.
Successful raw calls are reused; failures or corrupt/unverifiable receipts
are retried. A competing process cannot own the same output directory.

Each failed subprocess or malformed judge response gets **one retry** after a
short backoff. Persistent failures are recorded, remaining calls continue,
and affected facts are `incomplete`, never floor/gotcha. Exit 0 means all
selected facts completed; exit 1 means an incomplete run; exit 2 means a
configuration, selection or ownership refusal. Resume only when the host
quota/service is available again. The job does not change model policy,
fall back to another model or perform live fact verification.

Expect approximately **65–90 minutes** for the full host run, excluding quota
waits/retries. This is an estimate from the prototype's 6.8s Sonnet and 10.6s
Terra mean trial latencies and 105.8s for 40 judges at concurrency four;
longer citation-bearing judge prompts may take more time. Preserve the raw
files when a quota resets; there is no need to collect completed trials again.

## Model commands and cold context

The JSON command table carries one `model_id` per role; argv uses that field
through a placeholder so changing a model ID requires one edit. It preserves
the prototype's commands:

```text
claude -p --model claude-sonnet-5 --safe-mode --tools "" --output-format text "<question>"
codex exec -s read-only -m gpt-5.6-terra --skip-git-repo-check -o <outfile> "<question>" < /dev/null
claude -p --model claude-opus-5 --safe-mode --tools "" --output-format text "<judge prompt>"
```

Each invocation has a fresh empty temporary working directory outside the
checkouts and closed stdin, with no shell interpolation. Trial models receive
only the question, whose preamble is exactly:

> Answer from your own knowledge only, in at most 3 sentences. Do not use tools.

The expected assertion and source excerpts are passed only to the judge.
Each call is a new CLI invocation; no conversation is resumed between trials.
Claude's prototype flags disable tools and project customizations. The Codex
command retains the prototype's read-only sandbox and no-tools instruction;
it is not a separate CLI-enforced no-tools permission profile. The host owner
must keep the prototype's clean CLI configuration for comparable cold trials.
Command-table files are trusted executable configuration, not model output.

## Filters and offline checks

```bash
# One-fact real host smoke run (12 calls, before retries):
python3 tests/floor_eval/run_eval.py --facts G028 --output tests/floor_eval/runs/smoke
# Selected original inventory IDs:
python3 tests/floor_eval/run_eval.py --facts G009,G028,G114 --output tests/floor_eval/runs/selected
# Jira or Confluence only; shared facts match either citation repository:
python3 tests/floor_eval/run_eval.py --repo confluence --output tests/floor_eval/runs/confluence
# First two matching facts; --workers accepts 1 through 4:
python3 tests/floor_eval/run_eval.py --repo jira --limit 2 --workers 2 --output tests/floor_eval/runs/limit

# Offline public-CLI tests; no model executable is launched:
python3 -m pytest tests/floor_eval -q -p no:cacheprovider
# Offline full-inventory pipeline and zero-new-call resume:
python3 tests/floor_eval/run_eval.py --fake-models tests/floor_eval/fake_models --output tests/floor_eval/runs/fake
python3 tests/floor_eval/run_eval.py --fake-models tests/floor_eval/fake_models --output tests/floor_eval/runs/fake --resume
```

`--fake-models DIR` requires a local `stub.py` and `scenarios.json`; it invokes
only that Python stub and never falls back to `claude` or `codex`. The fixture
covers all-correct, four/five, three/five, uncertainty and confident
contradiction, plus failure injection for recovery tests. Its invocation log
provides independent evidence that a completed resume made zero calls.
Use `--help` for timeout and retry controls. Filters are smoke/diagnostic
runs; **the full 153 facts must complete before the inventory is treated as a
cut list**. Fake output is only evidence about plumbing.

## Inventory and citation provenance

[inventory.json](inventory.json) preserves every numbered item from the
September 2026 `skills-content-classification-2026-09.md` research document.
IDs `G001`–`G153` are inventory numbers, **not** the prototype's `G1`–`G10`.
Matching prototype questions are reused or extended/split to cover all clauses
of the full inventory item; `prototype_claim` records the calibration link.
No new floor hypothesis is substituted for an inventory item.

Each fact records its primary `repo`, all citation `repos`, topic, cold
question, verbatim expected assertion, original item and source line,
original gotcha-hypothesis quote, and structured citations. Citations retain
original repo-relative file and line numbers, source hashes, context excerpt
line spans and an audit status. Each cited assertion remains a **historical
hypothesis**, even when the source or current platform may contradict it.
Neither successful path validation nor a model's score establishes current
API truth.

The 228 citations include 16 references to collaborator documents from the
**uncommitted working tree of main, not HEAD `beaeb47`**. These match the
research's inputs; their snapshots were supplied by the supervisor under
`evidence/jira-collaborate-worktree`. They are marked
`uncommitted_main_snapshot`. The HEAD-based lane has shorter/different files:
four original line numbers exceed it and other pointers land on different
text. Original locations were retained, and only the snapshot used for the
evaluation changed. Other citations come from Jira `beaeb47` and Confluence
`403eac8` lane files. All source excerpts are embedded, so running the job
after the skills are rewritten does not lose its reference evidence.

Additional review notes call out shifted G063 (the account-ID requirement is
at lines 99–100), G135's self-contradictory duration-spacing assertion, G151's
bulk/UI overstatement, and other source-scope caveats. Review these before
adopting classifications; do not silently reinterpret a questionable source
as evidence that a model lacks knowledge.

Re-audit with explicit checkouts (the host main working tree should match the
collaborator snapshots):

```bash
mkdir -p tests/floor_eval/runs
python3 tests/floor_eval/audit_inventory.py \
  --jira-root . --confluence-root ../Confluence-Assistant-Skills \
  --output tests/floor_eval/runs/citation-audit.json
```

For a HEAD-based worker lane, add
`--jira-snapshot ../evidence/jira-collaborate-worktree` to use the supplied
snapshot for explicitly marked citations only. The auditor returns 1 for
missing/out-of-range citations, changed source bytes or excerpt mismatches,
and 2 for invalid inputs. It does not rewrite sources or repair citations.
Create the audit output's parent directory first, or omit `--output` for the
terminal summary.

## Classification and review

Floor means **every floor model scored at least four of five** against the
expected fact; any complete model below four keeps the fact as gotcha.
Unknown, hedged and partial answers count as incorrect, as in the prototype.
An incomplete trial or judge yields an incomplete fact and a nonzero run.
The judge separately identifies confident contradiction versus uncertainty;
any confident contradiction flags live re-verification, with consistently
opposing answers further identified. A stale candidate can reflect a stale
source or a mistaken model; the job never chooses between them automatically.

The output directory contains the machine-readable classification, per-call
raw answers and receipts, a manifest, `run_summary.json`,
`flipped-to-floor.md` and `stale-facts.md`. Classification includes each fact's
per-model counts/reasons, verdict and source/review flags. The floor list
quotes the original gotcha hypothesis once per flipped fact: the disproved
hypothesis is **that the model would not know it**, not necessarily the
assertion's factual content. The stale list includes readable source
citations and contradiction evidence.

Archive the entire output directory with the release review. Review model
threshold disagreements, source-audit notes and contradictory answers by
hand; record any human ruling separately with fact ID, original model scores,
source evidence, decision and reason. Do not overwrite raw evidence to encode
an override. Complete, non-fake full-inventory results plus that review are
the input for the later skill cut-list work; the evaluator does not edit the
skills or publish a release.

## Raw files and recovery receipts

```text
<output>/manifest.json
<output>/classification.json
<output>/run_summary.json
<output>/flipped-to-floor.md
<output>/stale-facts.md
<output>/raw/sonnet/G001_t1.txt           # likewise terra, trials 1–5
<output>/raw/sonnet/G001_t1.meta.json
<output>/raw/judge/G001_sonnet.raw.txt    # likewise terra
<output>/raw/judge/G001_sonnet.json
<output>/raw/attempts/<trial|judge>/<model>/<fact>_t<trial>/<unique>.txt
<output>/raw/attempts/<trial|judge>/<model>/<fact>_t<trial>/<unique>.json
```

The attempt receipt includes exit status, timeout, timing, stdout/stderr,
prompt and answer hash; judge receipts also retain the strict parsed verdict
and input-answer dependency hashes. Every retry/resume gets a new attempt
name. A successful attempt can reconstruct a missing canonical receipt
without a new model call. An answer without a successful matching receipt
cannot establish a score. Malformed judge text remains available for diagnosis.

`run_summary.json` lists `incomplete_fact_ids`, attempted trial/judge call
counts (including retries), reused calls and elapsed seconds for this
invocation. Both it and the classification are marked `running` before
collection and `complete` or `incomplete` afterward. SIGINT/SIGTERM cancel
queued work and allow at most the in-flight calls and their retries to finish
before saving an incomplete report; force-kill may leave status `running`,
which is never a completed run. Do not delete the output lock file or attempt
receipts to force recovery.

Default call timeouts match the prototype: Claude 120 seconds, Terra 180.
`--timeout SECONDS` overrides both; `--retry-backoff SECONDS` defaults to one
second. Run configuration must match for resume; use the original timeout and
worker settings. The command table is trusted host configuration, so review
its argv before a real run.
