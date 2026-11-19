---
name: academic-writing
description: Revise academic prose for clarity, as a focused edit or an optional scored rewrite loop with local stylometry. Use for manuscript prose, abstracts, grants, response letters, scientific reports and research pages.
---

# Academic Writing

Revise stiff, generic, unclear or AI-shaped prose into clear academic writing
without locking it to a field. The skill uses clarity checks, source-derived
sentence frames, local stylometry and meaning checks. A frame supplies fixed
syntax, never the source article's facts or an author's voice. `stop-slop` owns
sentence clarity and AI patterns for all prose; for scientific text, apply it
together with this skill. Use a lighter edit for casual writing, code comments,
changelogs and mechanical formatting.

## Priorities

Resolve every conflict in this order: **meaning** (facts, numbers, citations
and the strength of each claim stay as the source has them), **clarity** (a
reader in the field understands each sentence on one reading), **genre** (the
section follows its conventions and the venue's rules), **naturalness**
(rhythm, variety and the local scores). A lower priority never overrides a
higher one. Do not trade a clear sentence for a better score, and do not change
a claim to make a sentence clearer.

## Focused edit

This is the default. Audit the baseline, review the candidate, then resolve
findings and review any revision. Without a coverage request, a clean draft
needs no further edits.
The scaffold pass requires independent review, including in this default mode.
Other focused edits may use identified self-review unless the task requires more.
Apply the
[stop-slop cold-read conditions](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md#cold-read-check)
for standalone deliverables when the harness can start a fresh subagent. Do not
require a profile, style card, scorecard, six review lanes or a whole-manuscript
rewrite.

1. Read the passage and enough surrounding text to know its job, its audience
   and the terms the document already defines. For project files, technical
   checking or source integration, read
   [manuscript safeguards](references/council-loop.md#manuscript-safeguards).
2. Lock the facts: every number, unit, threshold, citation, equation, quoted
   term, source label, named entity and explicit limitation. This list holds
   for every edit, scored or not. Before editing, record located findings and
   evidence gaps against the original source in task notes, using the [claim checks](references/ai-tells.md#claim-and-proposal-checks).
3. Run the three checks in [clarity.md](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md) on
   each sentence, with its [scientific prose](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md#scientific-prose)
   section. The studied object, its measure or `we` is the subject and the
   finding is the main verb; the studied object is never the agent of an
   observed difference. Every term, reference and number resolves for a reader
   in the field, with no working label, noun stack, bare `This` or comparison
   without a baseline. The result is in the main clause. Take a missing actor,
   definition or quantity from the manuscript and its evidence; never from a
   donor article.
   Identify the relationships the sentence needs: ranked objects and ranking
   criterion; compared objects, measure and baseline; or the object undergoing
   a method and the operation performed. Make a builder or other actor explicit
   when the manuscript names it and its relation to those objects is unclear. Use the
   surrounding text where it already resolves a relation; do not make every
   sentence repeat the context. Record located findings, not an empty checklist
   for every sentence. A longer sentence is preferable when it states these
   relationships clearly. Preserve necessary technical repetition and effective
   sentences. Every added actor, criterion, measure, baseline or other relation
   needs support in the manuscript or its evidence. If that support is missing,
   retain the affected claim and report the gap; never guess. Meet a supplied
   word limit by cutting dispensable material, following
   [clarity over brevity](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md#clarity-and-brevity),
   without making a necessary relationship implicit.
4. Review the cues in [AI tells](references/ai-tells.md), including its
   [scholarly exposition](references/ai-tells.md#scholarly-exposition) patterns
   and contribution, citation, aggregation and proposal checks.
5. Check the result against the locked facts and the strength of each claim.
   Flag visible technical errors.
6. For sentences the AI creates or rewrites at the clause level (predicate,
   clause order or sentence structure), edits that add or change a scientific
   relationship even within a phrase, or every paragraph in an
   explicit coverage request regardless of authorship, run the required
   [scaffold pass](references/skeleton-injection.md). Select compatible frames
   from `data/scaffolds.jsonl` or a verified task-local bank with ranked
   `list --query` searches for the
   intended predicate, hedge or relation. Search across families before
   narrowing; try supported alternative predicates when the first search is
   unhelpful. Let identified sentence relationships guide retrieval; topical
   similarity alone is insufficient. Fill only their named slots, and render them with
   `scripts/scaffolds.py`. Use alternatives with the same rhetorical function;
   use a frame when it improves readability or precision, or supplies requested
   structural variety while preserving meaning and clear paragraph flow. Without
   a requested coverage target, the plain draft is the default and zero frames
   is valid. A requested number per paragraph instead uses the
   [coverage contract](references/skeleton-injection.md#requested-paragraph-coverage);
   a few examples do not complete a manuscript-wide request.
   Keep fixed frame spans locked during later edits. Missing tools or data make
   this pass incomplete, not a synthetic fallback.
7. Review the exact final text for meaning, readability, flow and style, using
   the [independent scaffold review](references/skeleton-injection.md#independent-editorial-review)
   when step 6 applies. Resolve
   findings, revise where useful and review again after the last change. Try up
   to three candidates per passage by default; then retain the original
   baseline or clearest reviewed candidate and review it too. An explicit
   coverage target requires continued retrieval under the coverage contract.
   Never substitute synthetic profile or example content. Always disclose
   unresolved source gaps.
   The scored loop uses its own four-round total budget, not a nested loop.
   When step 6 applies, run the final file check last, after review, with the
   required review record. Zero replacements completes only a pass without a
   coverage target; a target also requires the coverage table with qualifying
   structural changes judged against the original manuscript.
   Track clarity findings separately from scaffold counts: meeting a paragraph's
   replacement target never closes an unresolved clarity finding. Resolve every
   finding or disclose the source gap that prevents a supported repair.

Keep the purpose, audience, voice, structure, document class, bibliography and
notation unless the task changes them. Invent no length limits, sections or
extra deliverables. Methods, legal, statistical and procedure sections follow
their genre first: allow natural passive voice and keep exact terms, and limit the clarity
pass to undefined terms, unclear referents and actions hidden in nouns. Stop
when the requested passages are clear and checked, with unresolved gaps named.
If a coverage target remains unmet, report the pass as incomplete even when
the prose and exact rendering checks pass. Coverage never overrides meaning
or clarity, and a coverage request alone does not start the scored loop.

## Scientific research pages

Use this workflow for scientific reports, results summaries and project research
pages. It takes precedence over the scored loop and the output contract. A
routine operational status update needs a proportionate edit, not the source-frame
review cycle. A scientific correction that changes a relationship follows the
focused edit and its review requirements.

Default to a reviewable static page in the project's existing site, in its
source format, at an approved destination and access model. An
explicit format or hosting choice wins; this default authorizes no deployment.

1. Read this skill and [stop-slop](https://github.com/fmschulz/stop-slop-skill/blob/main/SKILL.md) before drafting. Apply
   stop-slop to the source, then the focused edit, then stop-slop again on the
   finished prose. Keep selected frame text fixed through this last pass and
   review and validate the final artifact after it.
2. Write concise prose. State the result or question directly, name the subject
   in headings, and order methods, results, interpretation and proposed work.
   Use only the sections the content needs. Cut sales language, slogan headings,
   decorative number displays, repeated caveats and commentary on the writing.
3. Keep limitations beside the results they qualify, and completed analyses
   apart from proposals. Cut repetition without turning missing annotations into
   missing genes, association into mechanism, or planned work into results.
4. Name both skills and the concise-scientific-prose requirement in every
   delegated drafting or rewriting task, for example: "Read and apply stop-slop
   and academic-writing. Write concise, well-structured scientific prose;
   preserve facts and uncertainty." Check returned prose against the evidence.
   The lead owns the final edit.
5. New or substantially rewritten results and interpretation need an
   independent editorial review by a fresh reviewer, ideally from another model
   family, with a prose review prompt. Give it the text and this rubric: quote each sentence you read twice;
   label the fault (hidden actor or action, vague wording, buried point); give a
   rewrite that keeps the claim; flag any change in meaning. Verify factual
   suggestions before applying them. Read the final rendered page.
6. Before first publication or a substantive update, record use of both skills,
   the review, resolved findings and the source and render checks in the
   project's methods or task record. Report an incomplete review or check as
   incomplete. This gate grants no permission to publish.

A phrase scan or style score cannot show that prose is clear, accurate or
natural; scoring is optional here. Deliver the page with a short completion
note. Keep scorecards, agent discussion and review records in `tasks/`.

## Scored loop

Use [council-loop.md](references/council-loop.md) only for an explicit scored
revision, or when a substantial revision benefits from it. It adds a style
profile, an optional style card, six review lanes, a rewrite brief and a
scorecard. The scores are revision aids: the draft's purpose and claims outrank
them, a passing score is not editorial approval, and no score measures clarity
(the reader-clarity lane does).

## Writing review

For a writing review of a finished manuscript (review modes, figures and
legends, term and number consistency, citation tracing), read
[manuscript-review.md](references/manuscript-review.md). It does not judge the
science; use `nelli-paper-review` for peer review.

## Boundaries

- **The task supplies the content.** Import no facts, examples or claims from
  a source article. Use its accepted sentence framework only when every fixed
  predicate, hedge and relation fits the draft's supported claim. Field-specific
  verbs may remain fixed in a suitable frame; they must not add a method or
  mechanism the task does not support. Optional teaching shapes live in
  `references/academic-style/`.
- **Integrity comes first.** If a sentence cannot improve without changing the
  claim, keep the original clause and report the residual issue. A requested
  substantive correction is separate from polishing: verify it, and make it
  explicit.
- **Protect effective prose.** Keep one term per concept, short sentences that
  state findings, and the links between sentences. These outrank a style card
  or vocabulary metric.
- **Plain prose is never a defect.** Reading grade, passive ratio, transition
  density and hedge density are ceilings only.
- **Naturalness is a band, and scores are proxies.** A signal is a human
  envelope, never a quantity to push to an edge: predictable text and text
  randomized past sense both read as unnatural. Use real writing quality only,
  never invisible Unicode, homoglyphs or injected typos. Do not claim a draft
  will pass GPTZero, Turnitin or any detector, or that output evades detection.
- **Source frames require exact rendering.** Use only accepted bank entries and
  keep every fixed character. Change only declared slots. Synthetic teaching
  examples and profile-corpus exemplars are not approved frames. The validator
  proves fixed-text fidelity for checked files, not meaning, grammar, authorship
  or that an agent followed the skill. A style card never overrides the writer's
  voice and logic ([scaffold pass](references/skeleton-injection.md)).
- **The author owns the claims.** If any input was AI-drafted, the author follows
  the venue's disclosure policy.

## Resources

| Path | Read when |
|---|---|
| `references/ai-tells.md`, stop-slop's [`references/clarity.md`](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md) | Steps 3 and 4 of the focused edit. |
| `references/council-loop.md` | Manuscript safeguards; the scored loop, its stop criteria and output. |
| `references/skeleton-injection.md` | Required source-frame pass for AI-created or clause-level rewritten sentences, changed scientific relationships, and all paragraphs in an explicit coverage request. |
| `references/reviewer-roles.md`, `rewrite-backends.md`, `templates/` | Scored loop: lanes, optional rewrite backends (Gemini via CBORG, Claude via `claude -p`), brief, scorecard. |
| `references/academic-style/` | Scored loop or a new draft: `metrics_targets.md`, `style-guide.md`, `checklist.md`. |
| `scripts/stylometry.py` | `score`, `tells`, `sample` (style card), `selftest`. |
| `scripts/profile_corpus.py` | Build optional style profiles and shape examples: `--fallback`, `--flavor`, `--corpus`, `--roles`. These do not satisfy the source-frame pass. |
| `data/scaffolds.jsonl`, `scripts/scaffolds.py` | Required source-frame selection, rendering, final-file and review-record validation, and generated MCP export. |
| `scripts/build_scaffolds.py` | Extract review candidates from verified original article text; never accepts frames automatically. |
| `scripts/cborg_rewrite.py`, `claude_rewrite.sh` | Optional candidate generators; re-score and fact-check their output. |

## Output contract

For a focused edit, return the requested passage or edited files and a brief
note only for unresolved material issues or substantive corrections. Add no
scorecards, extra sections or routine editing report. Keep the source format.
For a scored revision, follow the
[output contract of the loop](references/council-loop.md#output).
