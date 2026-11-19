# Neutral Academic Style Guide

Voice, sentence shapes, transitions, abstract shape and worked examples for
topic-neutral academic prose. Every example is synthetic: replace each
placeholder with the user's source-supported content, and never copy an example
as text. Word lists to avoid are in
[stop-slop phrases](https://github.com/fmschulz/stop-slop-skill/blob/main/references/phrases.md#scholarly-word-tells).

## Voice

The target voice is restrained, specific and evidence-led. It does not sound
like a named person, a field or a template.

- **Clarity:** each sentence names who or what acts, puts the action in the
  verb, uses terms the reader can resolve, and states its result in the main
  clause.
- **Specificity:** claims name the object, evidence, scope and limitation.
- **Restraint:** verbs match the strength of the evidence.
- **Continuity:** transitions show reasoning rather than stacking points.
- **Density with control:** terms, citations and qualifications stay when they
  carry meaning.
- **No sales tone:** the prose does not praise itself.

It is not conversational filler, motivational language, author imitation or a
license to add unsupported detail.

## Macro-Structure

- **Abstracts and summaries:** context, gap, pivot, evidence, implication.
- **Introductions:** establish the problem, position prior work, name the gap,
  state the contribution, preview the evidence or structure.
- **Discussions:** restate the main finding without overclaiming, explain how
  it changes the interpretation, compare with relevant sources, name
  limitations, close with the bounded implication.

## Sentence Shapes

These shapes describe the logic of a claim, so they work across fields.

| Shape | Pattern |
|---|---|
| Context frame | `[Object of analysis] matters for [larger question] because [specific relation].` |
| Gap | `Although [prior work/source] establishes [known point], [specific question] remains unresolved.` |
| Pivot | `Here, we [analyze/estimate/compare/test] [evidence] to assess [claim].` |
| Evidence | `[Measure] in [studied object] [increased/decreased] from [value A] to [value B] under [condition].` Or: `[Measure] in [studied object] stayed at [value] across [conditions].` |
| Interpretation | `This pattern suggests [bounded inference], rather than [stronger or competing claim].` |
| Limitation | `Because [constraint] limits [interpretation], the conclusion applies to [scope].` |
| Synthesis | `Together, these results clarify [argument] while leaving [remaining question] open.` |

**Subjects.** A result sentence names the studied object, its measure, or `we`
as its subject and puts the finding in the main verb. Do not make the studied
object the agent of an observed difference: a group that had a lower value did
not lower it. An evidence subject (`The results`, `This pattern`, `These
findings`) moves the finding into a subordinate clause. Use it only when the
sentence is about the evidence itself: its strength, what it supports, or what
it cannot show. The interpretation and synthesis shapes are such sentences; the
evidence shape is not. See the
[clarity guide](https://github.com/fmschulz/stop-slop-skill/blob/main/references/clarity.md#scientific-prose).

**Paragraphs.** A strong paragraph usually has a topic sentence that states its
job, one to three evidence sentences, and a final sentence that interprets the
evidence or prepares the next step. Alternate source-led, evidence-led and
claim-led openings.

**Punctuation.** Parentheses for citations, definitions or brief
qualifications. Semicolons only for two parallel, tightly linked clauses. Long
dashes rarely; if several appear on one page, revise the sentence structure.

## Transitions And Claim Verbs

A transition tells the reader how the next sentence relates to the prior one.

| Opener | Use |
|---|---|
| `Here, we ...` | Pivot from context to the work performed. |
| `By contrast, ...` | Mark a real comparison. |
| `Consistent with this interpretation, ...` | Add supporting evidence. |
| `However, ...` | Mark a limitation or conflict. |
| `Although ...` | Concede a condition before the main claim. |
| `Together, ...` / `Overall, ...` | Synthesize results; close a section without overclaiming. |
| `This pattern suggests ...` | Interpret evidence with restraint. |

Sentence-internal moves: `..., indicating that ...` (an inference from the
prior clause), `..., whereas ...` (a strict comparison), `..., but ...` (a
limitation), `..., particularly when ...` (a condition).

Verbs for what the work does: analyzes, estimates, compares, tests, evaluates,
describes, examines, models, reports, traces, clarifies. Verbs for evidence:
shows, suggests, supports, qualifies, limits, challenges, extends, constrains,
differs from. Use `proves`, `demonstrates`, `establishes`, `confirms`,
`reveals` and `solves` only when the evidence is strong enough, and avoid
`transforms`, `revolutionizes` and `guarantees`.

## Abstract Shape

Five sentences:

1. `[Object/question] matters because [specific relation to larger issue].`
2. `Although [prior work/source] establishes [known point], [gap] remains unresolved.`
3. `Here, we [analyze/estimate/compare/test] [evidence] across [scope] to assess [claim].`
4. `[Measure] in [studied object] [increased/decreased] from [value A] to [value B] under [condition].`
5. `Together, these findings [bounded implication] while leaving [limitation] open.`

Use seven or eight sentences when the source has several results: context, gap,
pivot, evidence, interpretation, limitation, synthesis. The order is a set, not
one sequence. Context usually opens and a synthesis or bounded implication
usually closes. The middle moves can be reordered or dropped to fit the source,
for example context, pivot, evidence, interpretation, gap as motivation,
synthesis. `stylometry.py sample --section abstract` can suggest a starting
shape for a new draft. A sampled order does not authorize restructuring an
existing abstract.

Checks: the first sentence names the actual object or question; the pivot says
what was done; each result sentence carries a source-supported detail; the last
sentence states a bounded implication, not a slogan; no sentence exists only
because the template has a slot.

## Worked Examples

**Generic opening.** Weak: "This study provides crucial insights into a complex
and rapidly evolving landscape. By leveraging a comprehensive framework, it
sheds light on a pivotal issue with far-reaching implications." Revision: "This
study tests whether [condition] changes [outcome] across [scope]. Using
[evidence], we compare [group A] with [group B] and estimate the size of the
difference under [constraint]." The revision names the research action, the
comparison, the evidence and the scope, and drops the empty implication.

**Result sentence.** Weak: "The results clearly demonstrate the importance of
this approach and highlight its broader relevance." Revision: "[Measure]
increases from [value A] to [value B] when [condition] is present." The measure
is the subject, the change is the main verb, the booster is gone, and the claim
stays bound to the stated condition.

**Limitation.** Weak: "Future work is needed to explore the many complex
dimensions of this issue." Revision: "Because the analysis uses [source type],
it cannot determine whether [excluded explanation] also contributes to
[outcome]." The revision names what the current evidence cannot show.

**Synthesis.** Weak: "In conclusion, these findings open new avenues and
provide a foundation for continued exploration." Revision: "Together, the
findings support [bounded claim] and narrow the next comparison to [remaining
factor]." The next step stays tied to the evidence.

**Hidden actions and a working label.** Weak: "An assessment of the effect of
[condition] on [outcome] was performed using set B, and a reduction was
observed. This suggests an influence of [factor]." Revision: "We assessed how
[condition] affects [outcome] in [the group that defines set B]. [Outcome] fell
by [amount] relative to [baseline]. This reduction suggests that [factor]
contributes." The revision turns `assessment`, `effect`, `reduction` and
`influence` back into verbs, replaces `set B` with what defines the group, gives
the reduction its amount and baseline (both from the source), and gives `This`
a noun.
