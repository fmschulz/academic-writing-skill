# Metric Targets

These are neutral defaults for academic prose. A supplied local profile may
override them.

| Metric | Default target | Notes |
|---|---:|---|
| Mean sentence length | 14-30 words | Split overloaded sentences. Combine short ones only when they repeat a point. |
| Median sentence length | 12-28 words | Median should not be far below the mean. |
| 90th percentile sentence length | 32-52 words | A controlled long tail is fine. |
| Maximum sentence length | 45-120 words | Very long sentences need a clear structure. |
| Burstiness (length) | >=0.35 | Sentence-length variation. Scored as a floor: real prose often exceeds 0.85, so there is no upper penalty. |
| Per-sentence burstiness | >=0.16 | Variation in per-sentence function-word density, a model-free stand-in for the variance of per-sentence predictability. Human prose alternates dense-content and connective sentences. Do not add framing sentences to raise it. |
| Aperiodicity | >=0.30 | 1 minus the strongest short-lag autocorrelation of sentence lengths. Low values mark a mechanical short/long/short cadence that fakes variation. Meaningful only alongside adequate burstiness. |
| Formulaicity | 0.20-0.62 (two-sided) | Composite naturalness signal. Runs high for predictable, repetitive, low-information prose; too low signals wording strained for variety. Natural writing sits mid-band. |
| Concreteness | report/raise | Density of numbers and capitalized names. Hyphenated compounds do not count, so a coined compound cannot raise it. Raise it only from source facts, never by inventing detail. |
| Flesch-Kincaid grade | <=18 | Ceiling only. Plain words and short sentences are not a defect. |
| Passive ratio | <=0.45 | Ceiling only. Passive is fine when the actor is irrelevant or unknown; active prose is never penalized. |
| Hedge density | <=8 per 1,000 words | Ceiling only. Hedges come from the evidence, not from a quota; remove stacked hedges. |
| Booster density | 0-2 per 1,000 words | Use sparingly and only when earned. |
| Transition density | <=8 per 1,000 words | Ceiling only. Prefer logical transitions over list markers; do not add a connective where the link is clear. |
| Long-dash density | <=1 per 1,000 words | Avoid dash-heavy rhythm. |
| Semicolon density | <=5 per 1,000 words | Semicolons should clarify relation, not add polish. |

## Interpretation

No metric here measures clarity. A passage can sit inside every band and still
hide its actors, leave terms undefined, or bury its result. Check clarity with
the [clarity guide](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md) first.

Metrics do not decide quality alone. A short paragraph may skip several scored
metrics, and some genres naturally sit outside these bands. Use the score to
find likely revision targets, then apply judgment against the source and venue.

## Naturalness signals are two-sided

The naturalness signals (per-sentence burstiness, aperiodicity, formulaicity)
target a human band, not an extreme. The scorer applies formulaicity as a
two-sided band and the other two as floors, but none of them improves without
limit. Prose that is too even and predictable reads as machine-shaped; prose
that is randomized past the point of sense reads as unnatural in the other
direction. Aim for the band, never the edge. These are
heuristic readability diagnostics computed locally; they are not a probability of
AI authorship and not a GPTZero, Turnitin, or other commercial-detector verdict.

## Optional style cards

Do not steer every draft to the exact center of these bands. Within a scored
loop, optionally draw a style card (`stylometry.py sample`) for suggestions on
rhythm, openers and punctuation. Use only suggestions that improve the prose.
Ignore sampled section order unless restructuring is authorized and improves
the argument. Source content, authorial voice and genre decide the final shape.
