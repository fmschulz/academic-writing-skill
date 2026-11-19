# Academic-Writing Scorecard

section: <section type>
profile: <fallback|local profile path>
flavor: <neutral|fs-writing|user-supplied profile>
seed: <style-card seed if used; otherwise omit this field>
rounds: <0..N>

| Metric | Round 0 | Final | Change | Target |
|---|---:|---:|---:|---|
| unclear_sentences | | | | 0 flagged by the reader-clarity lane |
| ai_tell_count | | | | 0 hard tells |
| style_distance | | | | <= tolerance |
| mean_sent_len | | | | profile band |
| burstiness | | | | floor (>= band low) |
| pp_burstiness | | | | floor (>= band low) |
| aperiodicity | | | | floor (>= band low) |
| formulaicity | | | | two-sided band |
| concreteness | | | | raised from source only |
| passive_ratio | | | | ceiling (<= band high) |
| hedge_per_1k | | | | ceiling (<= band high) |
| transition_per_1k | | | | ceiling (<= band high) |
| ttr | | | | review; allow required term repetition |
| hapax_ratio | | | | review; allow required term repetition |

preserved:
<numbers, citations, equations, quoted terms, source labels, named entities, limitations, recurring terms, short claim sentences>

editorial review:
<soft candidates resolved in context; paragraph links checked; justified metric exceptions>

major changes:
- <change 1>
- <change 2>
- <change 3>

residual risk:
<remaining issue, or "None found">

caveat:
Local scores are heuristic revision aids, not a commercial detector verdict.
