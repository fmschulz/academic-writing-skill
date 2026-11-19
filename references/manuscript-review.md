# Manuscript Writing Review

Rules for a writing review of a finished manuscript or section. A writing
review changes delivery, not science: flag a claim that looks wrong, and do not
rewrite it. For peer review of the science, use `nelli-paper-review`.

## Modes

| Mode | Trigger | Scope |
|---|---|---|
| `full-review` | "review my manuscript", "writing review"; default when unclear | whole document |
| `section-review` | "review the Introduction" | one section |
| `targeted` | "fix passive voice", "strip the clutter" | only the named check |
| `interactive` | "walk me through improving this" | one paragraph at a time: original, revision, reason; wait for confirmation |

Each finding gives the location, the original text, a concrete revision, the
check that found it, and a severity. "Consider tightening" is not a finding.

- **Critical:** misleads the reader, such as a wrong number or a term change
  that implies another variable.
- **Major:** impairs clarity or breaks a rule below.
- **Minor:** worth fixing, does not impede understanding.

Fix critical and major findings first. Leave a clear sentence alone even when
it breaks a rule.

## Figures and legends

Review each figure with its legend.

- No title inside the plot. The legend opens with a short title that names
  what is shown, not the result.
- The legend states what is plotted: panels, axes and units, what colors,
  shapes and lines encode, n per group, what error bars or intervals show, and
  the statistical test. The finding belongs in the Results text.
- Plot style follows `beautiful-data-viz`: greyscale first, color only to
  encode information, colorblind-safe, never the only encoding.
- Prefer direct labels and panel labels to a large legend.
- Flag 3D effects, pie charts, dual y-axes, heavy grids, decorative gradients
  and overloaded multi-series plots.
- Suggest a sentence or table when a figure shows one or two values, small
  multiples for many series, and a slopegraph for a before and after contrast.

## Terms and numbers (Banana Rule)

- Keep a defined term fixed. If Methods defines "obese group", Results must not
  say "heavier group": a synonym makes the reader ask whether a new category
  exists.
- List the key terms in Methods (groups, variables, techniques,
  abbreviations). Check that each recurs unchanged in Results, Discussion,
  tables and legends.
- Define each abbreviation at first use in the Abstract, the main text and
  each legend. Reject an abbreviation coined for the authors' convenience.
- N, percentages and significant figures agree across Abstract, text, tables
  and figures.
- Results hold no implementation detail (script names, file formats, internal
  flags). Methods hold what a reader needs to reproduce the work.
- An unchecked cause is not an explanation. Say the cause is unknown, or name
  the analysis that would test it.

## Citations

Trace a statistic that the text states as fact but cites only through a review
or textbook back to the primary study. A review range such as "15 to 62%" often
pools studies of different scope. Check DOIs and titles with `crossref-lookup`.
