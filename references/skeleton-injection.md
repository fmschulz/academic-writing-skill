# Source-derived sentence frames

A frame is an original article sentence with named content slots. Its template
keeps every character outside those slots fixed. A bank record adds the source
sentence, attribution and review decision. The donor article supplies sentence structure;
the task supplies the facts. Publication date alone does not prove human authorship.

## Required writing pass

Use this pass for sentences the AI creates or rewrites at the clause level, such
as changing a predicate, clause order or sentence structure, and edits that add
or change a scientific relationship even within a phrase. Spelling, punctuation
and citation-only corrections do not put an otherwise human sentence in scope.
Without an explicit coverage request, leave effective human prose intact. With
one, apply the coverage contract below to every original prose paragraph,
regardless of authorship. Preserve quotations, equations and document syntax.

Keep working files and decisions in the current task's directory, normally
`tasks/<task-name>/`. Record the in-scope sentence count and a concise no-fit or
rejection summary per passage. Only an uncovered requested paragraph needs the
attempt record specified in the coverage contract.

1. Save a clear pre-frame draft as `draft.md` or `draft.txt`. Audit it before
   choosing frames. This is the CLI `initial` pre-frame audit, distinct from
   the before-edit audit of the original source retained in task notes. Record
   located findings and lock numbers, units, comparisons,
   negation, causal strength, uncertainty and citations. The plain draft is the
   default against which candidates are judged.
2. Use `list --query` to find accepted frames with the same rhetorical function.
   Search across all families first, then narrow if useful. Search predicates,
   hedges and connectives, such as `compared`, `did not differ` or `consistent
   with`. Start from the relationships identified in the sentence audit, such
   as ranking methods by the performance of their outputs. With requested
   coverage or an authorized literature-retrieval pass, expand a no-fit bank
   search to original full text using the semantic retrieval procedure below.
   Try alternate predicates separately: `subjected`, `exposed` and
   `treated` describe different actions. Search results are candidates, not
   proof of semantic fit. A broad search can still end with no suitable frame.
   `--family` filters that function; `--section` matches an exact source heading.
   Families are `background`, `purpose`, `method`, `observation`, `contrast`,
   `interpretation`, `negative_evidence` and `limitation`. Choose a frame only if
   it improves readability or precision, or provides requested structural variety
   with meaning and readability preserved in the whole paragraph. Without a
   requested coverage target, zero frames is valid. Accept added words that
   clarify an object, actor, criterion or scope; do not penalize length alone.
   When a needed relation does not fit the slot constraints, reject that frame.
   Reject redundant expansions, stronger verbs and collective subjects such as “the pair” used
   only to force plural entities into a singular frame. Natural passive voice
   and `we` remain valid.
   Do not change an otherwise clear paragraph's tense or narrow the manuscript's claim
   solely to fit a frame. Retrieve a compatible frame or use another sentence.
3. Fill only named slots with task facts. Keep determiners inside noun-phrase
   slots. Reference slots may contain a single absolute HTTP or HTTPS URL,
   without credentials or surrounding prose; percent-encode trailing sentence
   punctuation if it is part of the URL. The renderer does not fetch it.
   Follow phrase length and agreement
   constraints; never put a clause in a noun-phrase slot. Check fixed predicates,
   hedges and logical relations too. Lexical guards cannot prove grammar or
   meaning. `render` is an optional preview, not a separate input to `apply`.
4. Create `replacements.json` and use `apply` to write `final.md` and
   `receipt.json`. Without a coverage target, use `[]` when no frame improves
   the draft. Never retype a
   selected frame. Obtain the independent editorial review below. Resolve findings with reasons; revise
   and review again when needed. Keep intermediate edits and findings in task
   notes. Without a coverage request, a clean draft needs no further edits.
5. Try up to three candidate attempts per passage by default, then keep the
   original baseline or clearest reviewed candidate and review that exact text
   too. An explicit coverage target requires continued retrieval under the
   coverage contract below. Never substitute synthetic profile or example content.
   The scored loop's four rounds are its total budget; do not nest this budget.
   A candidate budget never closes a clarity finding. Repair it in ordinary
   prose when the manuscript and its evidence support a repair. If a supported
   repair remains undone, report the pass as incomplete; do not label the
   finding a source gap or dismiss it to meet the budget.
   If the saved pre-frame draft changes, redo its pre-frame audit, recalculate
   offsets and rerun `apply`. Never hand-edit the rendered file or receipt.
6. Record the pre-frame audit as `initial` and the exact final text review as
   `final` in
   `review.json` using the schema below. Run `check --review review.json` last.
   Any later change requires another final review and check. Disclose unresolved
   source gaps to the author; do not hide gaps or failed checks to pass.

The pass is complete when selected frames meet the writing objective, findings
have been resolved or source gaps disclosed, and the final file, receipt and
review record pass `check`. With a coverage target, every inventoried paragraph
must also fall within the requested range. Without one, zero replacements is valid.
Record sentence and replacement counts
in task notes. Missing tools or data leave the pass incomplete; finish the prose
where possible and disclose the missing check. Never substitute synthetic frames.

## Independent editorial review

This review is required in focused edits and scored loops whenever this pass
applies, including zero-selection outcomes. Use a fresh reviewer through
`claude-codex-review`, respecting the user's model choice. The reviewer must not
have written or selected the candidate. Give it the original and revised
paragraphs, necessary adjacent context, factual locks, supporting manuscript
passages for added relations, and located findings with their proposed
dispositions. Include the selected templates, declared slot constraints, slot
values and receipt. Review every in-scope sentence, not only the frame substitutions.

Require located findings on meaning, explicit relationships, readability,
paragraph flow and scientific voice. Apply step 3 of the focused edit, including
its context and genre limits: clarify unclear relationships without repeating
already clear referents or forcing actors into natural passive methods prose.
Verify each slot's declared type, length and agreement, and the fit of every
fixed predicate, hedge and relation to the manuscript's claim. Do not reward a shorter
variant for leaving these relations implicit. Extra words and repeated technical
terms are acceptable when they clarify the science; unsupported details are not.
Preserve effective prose, natural passive voice and varied sentence structures.

Record each finding and the editor's supported repair, reasoned rejection or
author-visible source gap. A proposed rejection of a relationship finding must
quote the passage that already resolves it, or identify the applicable context
or genre limit; give that disposition to the final reviewer. If the reviewer
disputes it, repair and re-review the text. If the dispute is still unresolved,
disclose the disagreement, record the finding as `open` in `final`, and state
`incomplete` in the delivery note. Do not issue a passing final review for an
unresolved dispute. Resolve
clarity findings independently of paragraph coverage. A no-fit
frame outcome cannot excuse a repair supported by the manuscript and its evidence.
Review the exact final paragraphs again after any text change or a newly proposed
rejection of a relationship finding, retaining the reviewer
identity, input/output hashes and actual review artifact in the task record.
If review cannot run, label the pass incomplete; self-review is not a substitute.
The final review record below summarizes that evidence. A parser pass does not
establish that the prose reads naturally or that the reviewer was independent.

## Requested paragraph coverage

When the author requests a number of replacements per paragraph, use that range
as a completion criterion, below meaning, clarity and genre but above the plain-draft
default. This applies regardless of who wrote the manuscript and authorizes
restructuring selected sentences in otherwise effective prose. Inventory every
prose paragraph from the unedited manuscript before drafting or selection,
including captions when the scope is the whole
manuscript. Record exclusions for headings, equations, table cells, references
and placeholders; record any other exclusion as an unmet target unless the
author approved it. Preserve the paragraph inventory through revision so splitting
or merging text cannot change the denominator.

Maintain one coverage row per original paragraph: its ID, original and final
hashes, frame IDs, donor sources, qualifying structural-change count, total
rendered-frame count, structural change types and final review/check
status. Link each receipt entry to its original sentence or clause, paragraph
ID and pre-frame span, and retain the receipt input/output and delivered-file
hashes. A receipt entry is necessary but does not itself qualify as a replacement. Count only
sentences that differ structurally from the unedited manuscript: record a change
in subject, voice, clause order, predicate construction or connective. Ordinary
edits, sentence splits, unchanged renderings and synonym-only changes do not
satisfy the target, nor does adding a sentence without an original counterpart.
The minimum applies to qualifying changes; the maximum applies to all rendered
frames in the paragraph. Keep fixed predicates, hedges and
connectives intact; never hide a rewritten clause in a noun-phrase slot.

For an uncovered paragraph, try other sentences and compatible rhetorical
functions, then expand retrieval. When original full text is available, search
for papers semantically, recover complete donor-author text, filter sentences by the
needed predicate and relation, and rank the remaining candidates. Preserve exact
source spans and provenance. A topical match alone is insufficient. Verify new
frames before rendering; never manufacture a donor or change the strength of a
claim to fill a gap. Keep sentence structures varied across the manuscript and
report repeated frame use. Use a local corpus when searching manuscript text;
external queries use predicates and relations without unpublished wording unless
the author authorized sending it.

An authorized retrieval pass may add a task-local bank without changing the
shared bank. Preserve the donor metadata, exact canonical text, offsets, hashes,
original slots and retrieval lineage. Require `audit-bank`, plus independent
review of each selected donor's author-prose status, fixed syntax and slot
boundaries before final acceptance. A selector may accept a source record for
trial rendering after checking its extraction, but cannot self-certify final
donor review. A different reviewer records their identity, frame ID, source and
template hashes, decision and reasons; a frame without that record does not count.
Use the source/slot criteria in Maintaining the bank for both shared and local
records. For a pass using both, copy the selected shared records into the task-local
bank and render once against that stable bank; do not chain receipts across banks.
Original slot values must reconstruct the donor sentence exactly. Promotion to
the shared bank follows the separate maintenance procedure below.

The ordinary zero-selection fallback and default candidate budget do not waive
an explicit coverage request. The optional scored loop's four-round budget does
not turn an unmet target into completion either. Continue selection, retrieval
and review while useful authorized routes remain. If access, donor availability,
fit or an explicit resource limit prevents coverage, report an incomplete result
as N of M paragraphs with the uncovered IDs. Record the sentences tried, queries,
rejected frame IDs and reasons for each gap. A manuscript's missing evidence is a
separate issue and cannot waive coverage. A passing `check` does not prove coverage by
itself: deliver the coverage table and N of M count, even when the ordinary
output contract calls for only a brief note.

## Review record

The CLI requires this JSON structure (replace digest placeholders with the exact
receipt values and notes with the actual review):

```json
{
  "version": 1,
  "initial": {
    "sha256": "receipt.input_sha256",
    "reviewer": "self-review: editor identity",
    "findings": []
  },
  "final": {
    "sha256": "receipt.output_sha256",
    "reviewer": "independent reviewer identity; artifact path in task record",
    "notes": {
      "meaning": "Comparison against the locked facts.",
      "readability": "Sentence clarity and explicit scientific relationships against the plain draft.",
      "flow": "Connections across the whole paragraph.",
      "style": "Genre, voice and contextual tell review."
    },
    "findings": []
  }
}
```

Each finding has nonempty string fields `quote`, `issue`, `disposition` and
`reason`. Initial dispositions are `open`, `fixed`, `rejected` or `residual`.
Final dispositions are only `rejected` (a suggestion dismissed with a reason)
or `residual` (an author-visible source gap with a reason). A final `open` or
`fixed` finding means another review is needed. Reviewer strings and all four
final notes must be nonempty. The initial audit may be self-review; the final
assessment must summarize the independent editorial review above. Preserve
located findings and their dispositions separately from replacement counts.

The check verifies record structure and hash consistency, not that review took
place, reviewer independence, semantic fidelity or writing quality. Its residual
count is the number of final source gaps recorded, not a quality score.

The initial tool checks plain text and Markdown. For Word, LaTeX or another
structured format, use a plain-text working copy and preserve its checked frames
when editing the requested document. Without an adapter that extracts and checks
the final document, report that only the working copy was verified. Never claim
that pasted chat text or a later edited file is the checked final file.

## Writing commands

Run from the skill directory with `uv`; the renderer uses the standard library.
`list` loads only accepted bank entries and returns templates, slot constraints
and source identifiers. Its default page contains 20 records; use `--offset` and
`--limit` for more. Use repeated `--exclude FRAME_ID` options to find alternatives
to frames already used. Reuse is permitted when meaning requires it; prefer a
suitable alternative over unnecessary repetition.

`--query` matches any query term against fixed template text (without slot
names), review/use notes and the original source sentence. Family labels are not
query evidence; use `--family` for an exact family filter. Source text
keeps masked topic words discoverable, but predicate queries usually find more
transferable frames. Matches are literal words after case folding, a short
stopword list and finite inflection, selected derivation and UK-US spelling
mappings in `SEARCH_VARIANTS` in the script. There is no stemming or synonym
expansion; negation is retained.
The finite map includes procedure verbs such as `simulate`/`simulated`,
`calibrate`/`calibrated` and `rerun`/`reran`, and limitation predicates such as
`establish`, `resolve` and `distinguish` with their inflections.
Selected derivations include `identify`/`identification` and
`collect`/`collection`; these are related lexical forms, not semantic guarantees.
Punctuation is data, not a regular expression. An empty query has no matches.

Results rank by the number of matched fixed-text terms, then notes terms,
then source terms. Ties prefer fewer slots, fewer template words, then frame ID.
Each result includes `search.score` (the three counts), `matched_terms` and
`matched_fields`; the response includes normalized `query_terms`. These scores
measure lexical matches only. Notes may describe restrictions, and a source
topic match does not mean the fixed predicate fits the draft. Check every fixed
predicate, hedge and relation before selecting a frame.

`--max-slots` and `--max-template-words` filter before ranking and pagination.
Template words are whitespace-separated tokens, with each slot counting as one
word; this limit does not bound rendered sentence length. Without `--query`,
`list` keeps bank order and its existing output fields.

```bash
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl list --family method
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl list --query 'compared groups' --max-slots 4 --max-template-words 25
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl list --query 'cannot exclude' --limit 10 --offset 0
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl render --id FRAME_ID --slots slots.json
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl apply --draft draft.md --requests replacements.json --output final.md --receipt receipt.json
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl check --draft final.md --receipt receipt.json --review review.json
```

Each request in `replacements.json` supplies `start`, `end`, `original`, `id` and
`slots`. Offsets count Unicode code points in the saved pre-frame draft; `end` is
exclusive. Requests must not overlap. `original` must equal the draft span. The
`slots` object maps every slot name to a string. A preview slots file contains
that same object. Run `--help` for the exact options.

## Maintaining the bank

This section is for bank updates, not routine manuscript revision.

Accepted records retain the source sentence, exact offsets and hashes, DOI,
date, authors, license link, section, rhetorical function and original slot
values. Those values must reconstruct the source sentence exactly. Only original
author prose is eligible. Exclude generated summaries, figure interpretations,
editor-written digests and synthetic examples. Keep attribution with the record;
it does not make the source paper evidence for a new claim.

To extend the bank, prepare a JSONL manifest with these fields on every row:
`paper_id`, `doi`, `year`, `title`, `license`, `license_url`, `authors` (a list),
`text_path`, `text_sha256`, `xml_path`, `xml_sha256`, `extraction` (the recorded
text transformations) and `sections_path`. Paths are relative to a chosen corpus
root. The sections file is a JSON list of objects with `heading`, `start` and
`end`, using the same Unicode offsets as the canonical text.

Retain original XML alongside canonical text in the corpus. Canonicalization may
normalize whitespace and omit bibliographic citation nodes; record that in
`extraction` and keep all other wording. The extractor's script header pins
spaCy and its English parser. Run it on the verified manifest:

```bash
uv run --script scripts/build_scaffolds.py --manifest sources.jsonl --corpus-root /path/to/corpus --output candidates.jsonl --max-per-paper 50
```

The extractor proposes noun and number slots; it never accepts a frame. Review
each candidate's source, fixed text, slot boundaries and rhetorical function.
Reject poor grammar, citation debris and wording that cannot transfer to another
supported claim. Field-specific fixed verbs are usable only for claims that
already support that action. Do not change fixed wording to rescue a candidate.
For a bad slot boundary, fix the extractor and regenerate before reviewing again.
The extractor keeps complete `in response to`, `with the exception of` and
`(despite) the fact that` connectives fixed. It rejects hidden `few`, `little`
and `lack`, split comparatives, and `respectively` without fixed coordination.
Its agreement hints are conservative and still require editorial checks.
These bounded guards trade recall for caution: they can reject content such as
`a few` or anatomical comparatives, and they do not cover every negative head,
idiom or clause attachment. Check `absence`, `same ... as`, superlatives and
modified connectives during editorial review. A parser pass never accepts a
candidate automatically.
Short procedural sentences are eligible; a large slot count or a longer frame
does not make one more useful. For six or more slots, record a concrete reusable
purpose in the use note; reject a long frame without one. Keep negation and
uncertainty outside the slots.
Reject a comparison whose fixed `than` is separated from a comparative hidden
inside a noun slot. Check agreement in relative clauses and omitted repeated
verbs as well as the main subject. Name the affected slot in its use note, and
add a number constraint when the required number is unambiguous. Reject unclear
modifier attachment; a use note cannot repair the fixed syntax.
Review negative findings and limitations as such even when a sentence also
starts with a contrast or observation cue.

Set `review.status` to `accepted` only after review. Identify a person or AI in
`review.method`; put the decision and use restrictions in `review.notes`.
Bind saved decisions to the exact source-sentence and template hashes. Exclude
already accepted source sentences and unchanged rejected candidates. Record a
new decision when changed extraction makes a past rejection worth reconsidering.
Remove exact duplicates and minor framework variants from the count, including
slot names, case, punctuation, a/an, was/were, is/are, has/have and incidental
then/also/further. Retain useful, independently sourced singular/plural variants
as separate options, but count them as one underlying framework. Never create
a variant by editing a fixed verb. This normalization is for counting and
deduplication only; stored fixed text always remains exact. Retain each batch's
extractor and input hashes in
`data/provenance.json`, including prior batches when the bank grows.

For an expansion, independently audit a reproducible 10% random sample of new
accepts plus every new limitation and every frame with fixed negative wording,
regardless of its family label. Include negative-evidence frames as well.
Correct every
identified defect; if more than 5% of the random sample is defective, reopen
the full batch for review. A larger count never overrides the review criteria.
Then verify the accepted bank against its sources:

```bash
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl audit-bank --corpus-root /path/to/corpus
```

## Local MCP retrieval

The local [ampdot-io writing-scaffold server](https://github.com/ampdot-io/writing-scaffold)
is a retrieval interface. `scaffolds.py apply` and `check` still perform the
required rendering and final validation. The pinned upstream server lists frames
in random order and has no intent query. Use the ranked local `list --query`
command for selection; the MCP exposes the same bank for browsing and retrieval.
Generate its data from the canonical bank:

```bash
uv run --no-project scripts/scaffolds.py --bank data/scaffolds.jsonl export-mcp --output academic-bank.jsonl
```

The server loads that export with `--data`. Never edit the export independently.
Re-export after bank changes and restart the Codex or Claude MCP connection to
load it. Use the canonical frame ID embedded in the exported text; the server's
numeric ID and `copypastatext` storage label are not academic source identifiers.

Do not use the server's paid `detemplatize` tool for exact frames. The public
hosted server logs request bodies, so keep unpublished text out of it. A local
retrieval server does not change where the writing model processes the text.
Optional style-profile scores and synthetic teaching examples in the skill's
scored loop cannot satisfy this source-frame pass.
