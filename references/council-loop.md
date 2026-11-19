# Council Loop

The loop separates diagnosis from rewriting so that the final edit fixes the
right problems without losing facts.

Use the stages below when a scored loop is selected. A focused edit requires a
baseline audit, candidate review and resolution, with another review after
revision; it does not require round files, review lanes or scoring. Both modes
use the required
[source-frame pass](skeleton-injection.md) for AI-created or clause-level rewritten
sentences, edits to scientific relationships even within a phrase, and every
paragraph in a requested coverage target. Profile skeletons
are optional shape examples, not approved replacements or a fallback bank.

The editor resolves conflicts in the order set in `SKILL.md`: meaning, then
clarity, then genre conventions, then naturalness scores. Run at most four
rounds and never chase a signal to its extreme: the target is the human band,
not the edge. These four rounds are the total candidate budget, including frame
selection; do not nest the focused edit’s three-attempt budget.

## Manuscript Safeguards

- Read the actual root document, relevant includes and surrounding text before
  editing project files. Identify the build engine and dependencies. Inspect
  enough context for consistency without rewriting unrelated material.
- Preserve purpose, audience, voice, structure, document class, bibliography
  and notation conventions unless changing them is part of the request. A
  paper or chapter need not become a survey or teaching document. Add examples
  or derivations only when they aid the intended reader within scope.
- Define nontrivial objects and state assumptions before they are used. Check
  technical claims in the edited text, including derivations, conditions, units
  and citations, as far as the requested scope and supplied material allow.
  Flag visible errors even in a prose-only edit. Repair demonstrable gaps when
  authorized and feasible; otherwise preserve equations and claims, identify
  the gap and propose a concrete correction with its uncertainty. Distinguish
  substantive corrections from style edits and do not imply comprehensive
  verification of the underlying results.
- When sources are supplied for integration, distinguish research papers from
  macro files and style samples. Read the relevant full texts and appendices
  for the claims being used; verify bibliographic details and keep page or
  theorem locations and notation mappings where needed. Preserve attribution,
  disagreements and limits. Distinguish reported evidence, illustrative
  calculations and new results. Report inaccessible sources rather than
  implying review. Do not invent findings or launch substantial experiments
  without authorization.
- Keep the project's macro setup and prefer its existing definitions or the
  user's supplied macros. Keep additions local; do not change a shared macro
  file to resolve a local collision or import a new macro package by default.

## Workspace

Use a task-local workspace when files are involved:

```bash
SKILL=/path/to/academic-writing-skill
WS=/abs/path/to/academic-rewrite
mkdir -p "$WS"/rounds
```

Keep the source draft, score outputs, lane findings, rewrite briefs, and final
draft as separate files.

## Stage 1: Inputs

Record:

- source passage or path;
- section type;
- target venue, audience, and word limit if known;
- required citation or formatting constraints;
- whether to use the bundled fallback profile, the opt-in FS-writing flavor, or
  a user-supplied profile.

Do not invent venue rules. If rules matter and are not supplied, state that the
edit uses general academic conventions.

## Stage 2: Profile

Use `cache/fingerprint.json` and `cache/skeletons.json` if present. Otherwise:

```bash
cd "$SKILL"
uv run --no-project scripts/profile_corpus.py --fallback
```

The `fs-writing` flavor is the author's personal preset; its voice data are not
part of this repository. Use it only when the user asks for that voice:

```bash
uv run --no-project scripts/profile_corpus.py --fallback --flavor fs-writing --out cache/fs-writing
PROFILE=cache/fs-writing/fingerprint.json
SKELETONS=cache/fs-writing/skeletons.json
```

Build from a supplied document set only when the user wants that local
profile, aligned to a venue, genre or project voice:

```bash
uv run --no-project scripts/profile_corpus.py --corpus /abs/path/to/docs
PROFILE=cache/fingerprint.json
SKELETONS=cache/skeletons.json
```

`--corpus` accepts a file or directory of `.txt`, `.md`, `.xml`, `.pdf`
(`pdftotext` required), or simple `.json` documents containing `text` or
`abstract` plus `sections[].paragraphs`. Do not invent a corpus path. If the
user did not supply one, use `--fallback`. The neutral fallback writes default
metric bands and a synthetic skeleton bank; it is not derived from old articles
or any field-specific corpus. The FS-writing fallback writes a synthetic
FS-flavored preset with `flavor: fs-writing` in both JSON files.

A cached profile keeps the bands it was built with, and a corpus-derived
profile also keeps band values computed by the scorer of that time. After the
skill's scripts change, rebuild every cached profile: the fallback with
`--fallback`, a corpus-derived one from its original corpus. Score round 0 and
every later round with the same scorer and the same profile.

Optionally draw a style card when rhythm suggestions would help:

```bash
uv run --no-project scripts/stylometry.py sample \
  --section "$SECTION" \
  --profile "${PROFILE:-cache/fingerprint.json}" \
  --skeletons "${SKELETONS:-cache/skeletons.json}" \
  > "$WS/rounds/style-card.json"
```

Omit `--seed` to draw and record a fresh seed; pass one to reproduce a run.
Ignore sampled section order unless restructuring is authorized and improves
the argument. Voice, genre and logical sequence take priority over the card.

## Stage 3: Baseline Audit And Score

Before editing, record located findings and source gaps against the original
source draft in task notes. Use the claim and proposal checks in `ai-tells.md`.
This baseline audit is separate from the CLI pre-frame audit in Stage 5.

```bash
cd "$SKILL"
uv run --no-project scripts/stylometry.py score \
  --draft "$DRAFT" \
  --profile "${PROFILE:-cache/fingerprint.json}" \
  > "$WS/rounds/round0-score.json"
uv run --no-project scripts/stylometry.py tells "$DRAFT" > "$WS/rounds/round0-tells.json"
```

`DRAFT` can be an absolute path or `-` for stdin. Use the score to guide
revision, not to certify authorship.

## Stage 4: Review Lanes

Run the lanes in `reviewer-roles.md`: reader clarity, AI-tell detector,
stylometry and profile distance, structure and citation placement, meaning
fidelity, and integrity. Each lane returns located findings. No lane changes
the draft. The reader-clarity lane proposes a rewrite for each sentence it
flags; when it cannot tell what a sentence means, it states what is unclear
and proposes no rewrite. Run the reader-clarity lane as a cold read: it gets
the draft and one line on the intended reader, and nothing else.

## Stage 5: Editor Rewrite

Fill `templates/rewrite-brief.md` with:

- the manuscript passage and its supporting evidence;
- selected flavor (`neutral`, `fs-writing`, or user-supplied profile name);
- the preserve list;
- the run's style card, if used (rhythm, opener mix and punctuation suggestions);
- the top score gaps and naturalness signals;
- lane findings;
- optional shape examples for the selected profile;
- accepted source-frame IDs, proposed slots and the fixed text to preserve;
- length and venue constraints.

The Editor produces one continuous revised passage plus a short change note.
It fixes reader-clarity findings first, removes high-confidence AI tells, uses
helpful style-card suggestions, and raises concreteness only from facts in the
manuscript passage or its supporting evidence.
Preserve the document's equations, lists and other meaningful formatting. Stay
within the requested length range unless the user gives a new target.
Run the required source-frame pass on the accepted rewrite: audit that saved
pre-frame draft for the CLI `initial` record. If it changes, redo this audit
against its new bytes. Later review lanes
may reject an unsuitable frame but must not paraphrase its fixed text. Validate
the final file, receipt and required review record after all edits, including
when no frame fits. A frame must improve the sentence and paragraph against the
plain draft; exact rendering alone does not justify keeping it.

Optional external candidates may come from Gemini or Claude
(`rewrite-backends.md`), but the orchestrating agent must re-score and
fact-check them before use.

## Stage 6: Re-Score And Compare

Score the new draft with the same profile, and repeat the reader-clarity lane
on the new draft. Compare against round 0:

- sentences flagged by the reader-clarity lane, and which of them remain;
- hard tell count;
- `style_distance`;
- selected flavor;
- sentence-length variation and per-sentence burstiness;
- aperiodicity and formulaicity (naturalness, read as two-sided bands);
- concreteness (raised only from manuscript facts or supporting evidence);
- passive ratio;
- hedge density;
- type-token and hapax ratios (`richness_watch`);
- fact preservation.

## Stage 7: Stop Or Iterate

Run at most four rounds. Stop earlier when the draft meets the criteria below,
when a round no longer improves clarity or style while preserving meaning, or
when the remaining issue needs information absent from the manuscript and its evidence.

Stop criteria:

- no sentence remains flagged by the reader-clarity lane, or each remaining
  one is reported with the reason it stays;
- `pass: true` and `scored_coverage_ok: true`;
- hard AI tells are gone, and soft candidates have been reviewed in context;
- `style_distance` is within tolerance;
- naturalness signals sit inside their bands: `formulaicity` two-sided,
  `pp_burstiness` and `aperiodicity` above their floors, `concreteness` not
  raised by invented detail;
- changes in type-token and hapax ratios have been reviewed; necessary repetition
  of technical terms is not a defect;
- every number, citation, quoted term, equation, source label, and named entity
  survives unchanged, apart from verified substantive corrections authorized by
  the user and reported separately;
- if FS flavor was requested, the scorecard records `flavor: fs-writing`, and
  the rewrite uses only content supported by the manuscript and its evidence in FS-shaped sentences.

Stop early if the remaining weakness requires facts absent from the manuscript
and its supporting evidence.
Do not chase the score by adding unsupported detail or smoothing away necessary
precision. If literal wording, a quotation, or the argument's structure requires
an exception, preserve it and report the remaining diagnostic, even when
`pass` is false. A passing score does not replace review of soft tells or of
the reader-clarity findings.

After the last change, review the exact final text for meaning, readability,
flow and style and resolve the findings. If the budget ends, retain the original
baseline or clearest reviewed candidate and review it too. Never substitute
synthetic profile or example content. Report unresolved source gaps
and incomplete checks; never invent changes to a clean draft.
When the source-frame pass applies, use its independent editorial review and
budget rules. A score or a completed replacement quota cannot close an unresolved
sentence-relationship finding. Apply the default edit's clarity-over-brevity rule.

## Output

For a scored revision, return, in this order:

1. The rewritten passage as continuous prose, with no commentary inside it.
2. A short scorecard, round 0 against final: sentences flagged by the
   reader-clarity lane, `ai_tell_count`, `style_distance`, the selected
   `flavor`, and key metric moves.
3. Bullets naming the major changes.
4. Any residual gap or clause preserved for fidelity.
5. A one-line caveat that local scores are heuristic revision aids, not a
   commercial detector verdict.
