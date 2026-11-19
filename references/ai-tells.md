# AI-Tell Taxonomy

Use this file to locate patterns that often make academic prose sound generic,
inflated, or machine-shaped. Treat the taxonomy as a revision guide, not as
proof of authorship.

These patterns are a separate check from clarity. Prose can carry none of them
and still hide its actors, leave terms undefined, or bury its result. Run the
[clarity checks](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md) first.

## Word Tells

The hard and soft word lists, with the better wording for each, are in
[stop-slop phrases](https://github.com/fmschulz/stop-slop-skill/blob/main/references/phrases.md#scholarly-word-tells).
The scorer reports sentence openers, copula phrases, participle clauses and
negative parallelism as soft candidates too. Decide whether each adds meaning,
marks a real logical relation, or repeats or inflates the claim. A single
`Additionally` or a mathematical use of `represents` is not a defect. Repeated
empty transitions and promotional uses need editing. Soft candidates do not
block the automatic score; the editor must resolve them before finishing.

## Structural Tells

The general structure patterns are in
[stop-slop structures](https://github.com/fmschulz/stop-slop-skill/blob/main/references/structures.md). These cues
matter most in academic prose:

- **Uniform sentence length.** A page of same-length sentences feels generated.
  Vary rhythm where it helps. Keep short sentences that state a finding or turn
  in the argument; do not merge them to meet a length target.
- **Rule-of-three everywhere.** Lists of three abstract nouns are often filler.
  Keep lists when the items are concrete and necessary.
- **Negative parallelism.** Recast `not only ... but also ...` unless the
  contrast is doing real analytical work.
- **Copula avoidance.** Prefer `is`, `are`, or `has` over `serves as`,
  `stands as`, `boasts`, or `represents` when no real distinction is intended.
- **Participle padding.** Trim tails such as `, showcasing`, `, highlighting`,
  and `, demonstrating` when they repeat the main clause.
- **Decorative punctuation.** Extra long dashes and semicolons often hide weak
  sentence structure. Use them sparingly.

## Scholarly Exposition

Use the shared [scholarly pattern guide](https://github.com/fmschulz/stop-slop-skill/blob/main/references/structures.md#scholarly-exposition)
for exposition-specific cues and their contextual safeguards.

## Local Signal For Formulaic Phrasing

`stylometry.py` reports a `formulaicity` composite and a per-sentence burstiness
signal that flag several patterns above at once: predictable filler frames, low
information density, long function-word runs, and even per-sentence rhythm. Use
them to locate stretches worth revising, not as proof of authorship. The signal
is two-sided: prose can also be over-randomized, so treat the band, not the
floor, as the goal.

## False-Positive Guardrails

- Do not strip technical terms, formal register, citations, or calibrated
  hedges merely because the prose is dense.
- Do not make academic prose conversational to avoid AI tells. Contractions,
  jokes, and chatty asides are usually wrong for formal work.
- Do not reduce precision. A plain accurate sentence is better than a fluent
  sentence that weakens the claim.
- Preserve qualifiers that carry magnitude, frequency, scope, or uncertainty.
  Remove an adverb only when its removal leaves that information intact.

## Claim and proposal checks

- Each contribution states a specific supported result or deliverable, rather
  than repeating an abstract claim of novelty or effort.
- Assign grouped citations roles only when supplied text or verified references
  support the role of each key. Otherwise preserve the group and flag the gap;
  invent no attribution. Preserve every key; do not prune to shorten a list.
- Audit empirical claims against supplied numbers, figures, tables or citations.
  Add a pointer only when verified. Flag missing support or a conflict between
  claim and evidence; a style-only edit does not authorize silently changing the
  claim or its strength.
- Keep each magnitude linked to its method, metric and comparison. Preserve the
  supplied definition of a mean or range, including weights and aggregation
  level. Never infer equal weighting or replace a reported mean with a range.
- In proposals, preserve supported ambition and check each promised outcome
  against the supplied means and feasibility evidence. Flag real dependencies
  between aims and missing fallbacks; wording cannot make dependent aims
  independent. Invent no preliminary results, partners or evidence.

These checks adapt the relevant advice from
[AIScientists-Dev/academic-humanizer, pinned revision](https://github.com/AIScientists-Dev/academic-humanizer/blob/94b88b23703bed7df507acae7d6d5876209a0cdf/SKILL.md)
(MIT). Existing meaning locks take precedence over upstream advice to soften
claims or shorten citation lists.
