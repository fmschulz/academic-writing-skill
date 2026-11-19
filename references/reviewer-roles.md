# Reviewer Roles

Keep roles separate. Each role returns concise, located findings and a severity
level. The Editor resolves conflicts in this order: meaning fidelity (Lane D),
reader clarity (Lane F), structure and genre (Lane C), then AI tells and
stylometry (Lanes A and B). Integrity (Lane E) is a gate, not a preference.

## Lane A: AI-Tell Detector

Input: source draft and `references/ai-tells.md`.

Return:

- hard tells with quoted snippets;
- soft tell clusters;
- structural tells;
- false positives that should remain unchanged.

## Lane B: Stylometry And Profile Distance

Run `scripts/stylometry.py score`. Return:

- `style_distance` and pass status;
- selected profile flavor (`neutral`, `fs-writing`, or user supplied);
- metrics outside target bands;
- naturalness signals: `formulaicity` (two-sided), `pp_burstiness`,
  `aperiodicity`, and `concreteness`, with whether each sits in its human band;
- `richness_watch` (ttr, hapax) versus round 0; distinguish needless repetition
  from the necessary reuse of technical terms;
- metrics skipped because the passage is too short;
- top fixes from the scorer.

Read the naturalness signals as a band, not a target to minimize. Both extremes
are wrong: uniformly predictable prose and prose over-varied past the point of
sense both leave the human band. These are heuristic revision aids, not a
detector verdict.

## Lane C: Structure And Citation Placement

Evaluate the paragraph or section shape:

- Does each paragraph have a clear job?
- Does the first sentence set the frame without overclaiming?
- Are citations placed near the claims they support?
- Are transitions logical rather than decorative?
- After editing, do sentences still connect through a shared referent or the
  intended addition, contrast, reason, or consequence? Repair a broken link
  without requiring an explicit connective in every sentence.
- Do paragraph openings retain the contrast or continuity the argument needs?
- Have short sentences that state findings or turns in the argument kept their
  force, rather than being merged to satisfy a metric?
- Are headings, bullets, and lists appropriate for the section type?

## Lane D: Meaning Fidelity

Extract the preserve list from the source:

- numbers and units;
- thresholds and ranges;
- equations and symbols;
- citations and quoted terms;
- named entities and source labels;
- the term used for each recurring concept, including distinctions between
  related concepts;
- explicit claims and limitations.

Verify that each item survives unchanged in the rewrite. Mark any changed,
deleted, or invented content. Keep one term for one concept; do not introduce
synonyms for variety or collapse distinct concepts into one label.

## Lane E: Integrity And Audience Fit

Check:

- no invented citations, claims, or details;
- no detector-evasion claims;
- no field-specific terms added by the editor;
- no FS-writing flavor unless the user explicitly requested it;
- if FS flavor is requested, no corpus sentence reused verbatim;
- source frames use accepted bank IDs, supported slot values and unchanged fixed
  spans and improve sentence and paragraph clarity or precision against the
  plain draft; the final file passes `scaffolds.py check --review review.json`
  after all style edits, including zero replacements;
- rendered-frame counts match the receipt; qualifying structural changes are
  judged against the unedited manuscript for any requested coverage target;
  no-fit and unavailable-tool cases are
  explicit, and exact text validation is not presented as semantic proof;
- initial audit and final review cover the exact input and output; final notes
  cover meaning, readability, flow and style; source gaps remain author-visible;
- the final scaffold reviewer did not write or select the candidate, and the
  task record contains the actual review artifact bound to the delivered text;
- disclosure caveat when the source was AI-drafted;
- tone matches the intended venue and audience.

## Lane F: Reader Clarity

Input: the draft and one line that names the intended reader. Do not give this
lane the source, the scores, or the other lanes' findings: it reads as a
reader in the field who has not seen the work. Use the three checks in the
[clarity guide](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md) and its scientific-prose
section. Apply the sentence-relationship checks in the focused edit: identify
ranked objects and criteria, compared objects and baselines, and the objects
and operations in methods. Flag unclear builder or evaluator relations. Judge
these in context; avoid demands to repeat an already clear referent. Accept
longer sentences and necessary technical repetition when they improve clarity.

Return:

- the main claim of the passage in one sentence, as the lane understood it;
- each sentence it read twice, quoted, with one label (`hidden actor or
  action`, `vague wording`, or `buried point`), a one-line reason, and a
  proposed rewrite that keeps the claim. When the lane cannot tell what the
  sentence means, it states what is unclear and proposes no rewrite;
- each term, abbreviation, working label, referent or number it cannot
  resolve, quoted;
- the number of flagged sentences out of the total, for the scorecard.

Do not flag field terms the audience uses, passive voice in methods where the
sample or step is the topic, or a calibrated hedge. A rewrite from this lane is
a proposal: the Editor checks it against the source before using it, because
this lane cannot see what the source supports.
