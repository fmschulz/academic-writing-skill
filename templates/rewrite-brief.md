# Rewrite Brief

You are rewriting one passage of academic prose so it is clearer, more specific,
and less generic while preserving every fact.

This template supports the scored loop. Omit score, style-card and review-lane
fields when unused; a focused edit does not need this template. Preserve source
formatting and the requested scope.

## Manuscript Passage

<paste the passage to edit>

SUPPORTING MANUSCRIPT EVIDENCE: <adjacent context and passages that support any
added actor, criterion, measure, baseline, definition or quantity; donor articles
supply syntax only>

## Context

SECTION TYPE: <abstract|introduction|results|discussion|literature review|grant aim|response letter|cover letter|other>
TARGET VENUE OR AUDIENCE: <known constraints, or "general academic">
LENGTH TARGET: <user-supplied word count or range, or "preserve scope">
FLAVOR: <neutral|fs-writing|user-supplied profile>

## Preserve Exactly

<list every number, unit, threshold, citation, equation, quoted term, source label, named entity, and explicit limitation>

RECURRING TERMS: <one label for each concept; retain distinctions between concepts>
PROTECTED SENTENCES: <short source sentences that state findings or changes in the argument>

## Style Card (optional)

<paste the JSON from `stylometry.py sample --section <type>`: seed, rhythm
setpoint, opener mix, punctuation lean, macro order>

Use the card only where it improves the prose. Preserve authorial voice and
logical sequence; sampled section order does not authorize restructuring.
Drop any sampled move the manuscript and its evidence do not support. If `flavor` is `fs-writing`,
borrow cadence and sentence jobs only; do not copy a corpus sentence.

## Score Summary

ROUND: <0|1|2|3|4>
TOP SCORE GAPS: <paste top_fixes>
AI TELLS: <paste hard and soft tells>
NATURALNESS: <paste formulaicity, pp_burstiness, aperiodicity, concreteness>

## Lane Findings

LANE A - AI tells:
LANE B - stylometry:
LANE C - structure/citations:
LANE D - meaning fidelity:
LANE E - integrity/audience:
LANE F - reader clarity:

## Source Frames

<record approved bank IDs, rhetorical functions, exact replacement spans and slot values; retrieve by the relationships that need clarification, preserve all fixed text, and give a concise no-fit/rejection summary per passage; zero frames is valid only without a requested coverage target>

<record the initial audit, located clarity findings and dispositions separately from coverage, and the independent final review of meaning, explicit relationships, readability, flow and style; link its artifact and exact reviewed hashes, including after revision; self-review may supply the initial audit>

<record receipt.json, review.json and the exact output file; check with --review after the last edit, even with zero replacements; disclose source gaps>

## Rewrite Instructions

Produce one revised passage as continuous prose. Fix the reader-clarity
findings first: name the studied object, its measure, or `we` as the subject, put the finding
or action in the main verb, define or replace each term the reader could not
resolve, and put the result in the main clause. Take every definition, actor,
criterion, measure, baseline and quantity from the manuscript and its evidence,
never from a donor article; if that evidence does not supply one, keep the
clause and report the gap. Then remove generic AI phrasing and
use helpful style-card suggestions if supplied: vary sentence length without a
mechanical short/long cadence, let dense sentences and plain ones alternate
where the content allows, without framing sentences that carry no information,
and use punctuation for clarity. Raise concreteness
only from facts in the manuscript passage or its supporting evidence; never invent numbers, names, or detail
to make the prose look specific. Keep
calibrated uncertainty and preserve section conventions. Do not add facts beyond
the manuscript passage or its supporting evidence, new citations, or unsupported
field terms. Meet a supplied length target by cutting
dispensable material, without making a necessary relationship implicit. If a source clause
cannot be improved without changing the claim, keep that clause.

Resolve soft tell candidates in context. Keep useful transitions, literal terms,
and grammatical constructions that carry meaning. Preserve the links between
sentences and paragraphs after cuts. Keep the recurring terms and protected
sentences above even if they move a vocabulary or rhythm metric away from its
target. Explain a justified exception instead of forcing a passing score.

If FS-writing flavor is active, prefer a context -> gap -> `Here, we` pivot ->
evidence -> synthesis shape where the manuscript and its evidence support it, use
first-person plural for claims supported by that evidence, and keep process/procedure sentences
comfortably passive. Do not import field vocabulary or exact FS phrasing.

Aim for the naturalness bands, not their edges: prose randomized past the point
of sense is as unnatural as prose that is uniformly predictable.
