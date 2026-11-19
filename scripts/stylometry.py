#!/usr/bin/env python3
"""Stylometry and AI-tell scorer for the academic-writing skill.

Subcommands:

  measure   FILE|-                         metric vector for one passage
  tells     FILE|-                         located AI-tell hits
  score     --draft FILE --profile P.json  draft vs academic profile
  sample    [--seed N] [--section S]       one per-run style card (variation)
  selftest                                  run bundled fixtures and self-checks

The metrics are revision signals, not authorship judgments. They make the
rewrite loop objective and repeatable while preserving the source claims. The
naturalness signals are heuristic readability diagnostics; they are not a
calibrated probability of AI authorship and not a commercial-detector verdict.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics
import sys
import zlib
from collections import Counter

WORD = re.compile(r"[A-Za-z][A-Za-z\-']*")
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'])")
VOWELS = re.compile(r"[aeiouy]+")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT.split(text.strip()) if len(s.strip()) > 5]


def words(text: str) -> list[str]:
    return WORD.findall(text)


def syllables(word: str) -> int:
    w = word.lower()
    n = len(VOWELS.findall(w))
    if w.endswith("e") and not w.endswith(("le", "ie", "ee")):
        n -= 1
    return max(1, n)


TELL_WORDS_HARD = {
    "delve",
    "delving",
    "unlock",
    "unlocking",
    "unleash",
    "revolutionize",
    "revolutionary",
    "groundbreaking",
    "effortlessly",
    "empower",
    "empowering",
    "supercharge",
    "plethora",
    "myriad",
    "vibrant",
}
TELL_WORDS_SOFT = {
    "crucial",
    "pivotal",
    "vital",
    "leverage",
    "comprehensive",
    "facilitate",
    "intricate",
    "meticulous",
    "robust",
    "holistic",
    "harness",
    "harnessing",
    "seamless",
    "seamlessly",
    "paradigm",
    "tapestry",
    "realm",
    "mosaic",
    "synergize",
    "synergistic",
    "showcase",
    "underscore",
    "testament",
    "landscape",
}
TELL_PHRASES = [
    "delve into", "dive into", "deep dive", "state-of-the-art", "cutting-edge",
    "paradigm shift", "in today's world", "in the modern world", "treasure trove",
    "it is important to note", "it should be noted", "it is worth noting",
    "needless to say", "as we know", "in recent years",
    "with the rapid advancement", "rich tapestry", "plays a crucial role",
    "paves the way", "open new avenues", "at its core", "the rapidly evolving",
    "ever-changing",
]
TELL_OPENERS = [
    "furthermore", "moreover", "additionally", "in conclusion", "in summary",
    "in essence", "ultimately", "notably enough", "needless to say",
    "it is important to note", "it should be noted", "it is worth noting",
    "as mentioned", "in recent years", "with the rapid advancement",
    "this paper presents", "the purpose of this study",
]
TELL_CLOSERS = [
    "open new avenues", "paves the way", "profound implications",
    "further research is needed", "significant step forward",
    "far-reaching implications", "we hope that our findings",
]
COPULA_DODGE = re.compile(
    r"\b(serves as|stands as|boasts|represents|underscores|encompasses)\b", re.I
)
ING_PAD = re.compile(
    r",\s+(showcasing|highlighting|reflecting|symbolizing|underscoring|ensuring|"
    r"emphasizing|demonstrating|illustrating|signifying)\b", re.I
)
NEG_PARALLEL = re.compile(r"\bnot only\b.*?\bbut\b|\bnot just\b.*?\b(it'?s|but)\b", re.I)
HEDGES = {"may", "might", "could", "likely", "suggests", "suggest", "appears",
          "seems", "possibly", "potentially", "perhaps", "presumably"}
BOOSTERS = {"notably", "strikingly", "importantly", "remarkably", "clearly",
            "markedly", "substantially", "considerably", "strongly"}
TRANSITIONS = {"here", "together", "consistent", "notably", "conversely",
               "therefore", "importantly", "despite", "although", "however",
               "moreover", "furthermore", "additionally", "thus", "hence"}
PASSIVE_RE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:[a-z]+ly\s+)?"
    r"([a-z]+(?:ed|en)|found|known|shown|made|done|seen|given|taken|built|kept|held|"
    r"sent|set|led|drawn|grown|lost|met|spread|run|put|left|told)\b", re.I)
PASSIVE_STOP = {"often", "oxygen", "women", "men", "children", "red", "green",
                "golden", "wooden", "sudden", "hidden", "garden", "kitchen", "dozen",
                "citizen", "based", "related", "interested", "involved", "intended",
                "limited", "located", "situated", "open"}

# Closed-class filler words. Long uninterrupted runs of these mark low-information
# stretches that read as machine-shaped padding.
FUNCTION_WORDS = {
    "a", "an", "the", "and", "but", "or", "nor", "so", "yet", "for",
    "of", "in", "on", "at", "to", "from", "by", "with", "about", "as",
    "into", "over", "under", "between", "among", "through", "during",
    "without", "within", "upon", "against", "toward", "across", "than",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their", "this",
    "that", "these", "those", "which", "who", "whom", "whose", "what",
    "is", "am", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "shall", "should",
    "can", "could", "may", "might", "must", "not", "no", "if", "then",
    "when", "while", "where", "because", "since", "although", "though",
    "whether", "both", "either", "neither", "such", "very", "more", "most",
    "any", "some", "all", "each", "there", "here",
}
# Predictable filler frames, distinct from TELL_PHRASES. Low weight: a soft
# signal of formulaic phrasing, not a blocklist.
FORMULAIC_NGRAMS = [
    "a wide range of", "a growing body of", "plays a role in", "play a role in",
    "due to the fact that", "it has been shown that", "shed light on",
    "when it comes to", "one of the most", "a variety of",
]
# Rhetorical moves per section, used by `sample` to draw a valid ordering rather
# than one fixed canonical order.
MACRO_MOVES = {
    "abstract": ["context", "gap", "pivot", "evidence", "interpretation",
                 "limitation", "synthesis"],
    "intro": ["problem", "prior_work", "gap", "contribution", "preview"],
    "discussion": ["restate_finding", "reinterpret", "compare", "limitation",
                   "implication"],
    "generic": ["frame", "development", "evidence", "qualification", "close"],
}
MACRO_ANCHOR = {"abstract": "context", "intro": "problem",
                "discussion": "restate_finding", "generic": "frame"}
PUNCTUATION_LEANS = ["semicolon", "parenthetical", "colon-led", "plain"]
DEFAULT_OPENER_POOL = [
    "Here,", "By contrast,", "Consistent with this,", "However,", "Although",
    "Together,", "Overall,", "This pattern suggests", "In this analysis,",
    "Notably,", "Taken together,", "In contrast,",
]


def is_passive(sentence: str) -> bool:
    return any(m.group(1).lower() not in PASSIVE_STOP for m in PASSIVE_RE.finditer(sentence))


def _per_1k(count: int, n_words: int) -> float:
    return round(1000.0 * count / n_words, 2) if n_words else 0.0


def _pct(data: list[int], p: float) -> float:
    d = sorted(data)
    if not d:
        return 0.0
    k = (len(d) - 1) * p / 100.0
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return float(d[int(k)])
    return d[lo] * (hi - k) + d[hi] * (k - lo)


def _compress_ratio(text: str) -> float:
    """zlib compressed/original byte ratio. Lower ratio = more predictable text.

    Model-free entropy surrogate (compression-as-entropy). Guarded on short
    strings, where zlib's fixed header dominates and the ratio is meaningless.
    """
    raw = text.encode("utf-8")
    if len(raw) < 80:
        return 0.0
    return len(zlib.compress(raw, 9)) / len(raw)


def _autocorr(seq: list[int], lag: int) -> float:
    n = len(seq)
    if n <= lag:
        return 0.0
    mean = statistics.mean(seq)
    var = sum((x - mean) ** 2 for x in seq)
    if var == 0:
        return 0.0
    cov = sum((seq[i] - mean) * (seq[i + lag] - mean) for i in range(n - lag))
    return cov / var


def _aperiodicity(lens: list[int]) -> float:
    """1 - strongest short-lag autocorrelation of the sentence-length sequence.

    Near 0 means a mechanical short/long/short cadence (which fakes high length
    variance); near 1 means irregular, human-like variation. Meaningful only
    alongside adequate burstiness, which separately catches uniform length.
    """
    if len(lens) < 3:
        return 0.0
    ac1 = abs(_autocorr(lens, 1))
    ac2 = abs(_autocorr(lens, 2)) if len(lens) >= 4 else 0.0
    return round(max(0.0, min(1.0, 1.0 - max(ac1, ac2))), 3)


def _persent_predictability(sents: list[str]) -> list[float]:
    """Per-sentence function-word density: a model-free stand-in for how
    predictable each sentence is. Connective and framing sentences run
    function-word-dense (predictable); sentences carrying specific content run
    content-word-dense (less predictable). The variance of this across sentences
    is the naturalness analog of GPTZero-style burstiness (variance of
    per-sentence perplexity) -- human prose alternates the two, machine-shaped
    prose holds an even middle. Robust on short passages, unlike a unigram
    surprisal model that degenerates when almost every word is unique.
    """
    out = []
    for s in sents:
        w = [x.lower() for x in WORD.findall(s)]
        if w:
            out.append(sum(1 for x in w if x in FUNCTION_WORDS) / len(w))
    return out


def _longest_function_run(lower: list[str]) -> int:
    best = cur = 0
    for w in lower:
        if w in FUNCTION_WORDS:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _high_info_tokens(text: str) -> int:
    """Count numbers and mid-sentence capitalized tokens (named entities).

    A density heuristic, not a parser. Hyphenated compounds do not count: a
    pattern cannot tell an established term from a coined one, and counting
    both rewards coined compounds. Concreteness is raised from source facts
    during rewriting, never invented; this only measures what the draft
    already contains.
    """
    n = len(re.findall(r"\d[\d.,]*", text))
    for s in sentences(text):
        toks = WORD.findall(s)
        n += sum(1 for i, t in enumerate(toks) if i > 0 and t[:1].isupper())
    return n


def measure(text: str) -> dict:
    sents = sentences(text)
    ws = words(text)
    n_w = len(ws)
    n_s = len(sents)
    if n_w == 0 or n_s == 0:
        reason = "empty text" if n_w == 0 else "no sentence over 5 characters detected"
        return {"error": reason, "n_words": n_w, "n_sentences": n_s}
    lens = [len(s.split()) for s in sents]
    lower = [w.lower() for w in ws]
    syl = sum(syllables(w) for w in ws)
    freqs = Counter(lower)
    hapax = sum(1 for _, c in freqs.items() if c == 1)
    passive_sents = sum(1 for s in sents if is_passive(s))
    mean_len = statistics.mean(lens)
    burst = round(statistics.pstdev(lens) / mean_len, 3) if mean_len else 0.0
    ppv = _persent_predictability(sents)
    if len(ppv) >= 2 and statistics.mean(ppv):
        pp_burst = round(statistics.pstdev(ppv) / statistics.mean(ppv), 3)
    else:
        pp_burst = 0.0
    fk = 0.39 * mean_len + 11.8 * (syl / n_w) - 15.59
    return {
        "n_words": n_w,
        "n_sentences": n_s,
        "mean_sent_len": round(mean_len, 1),
        "median_sent_len": round(statistics.median(lens), 1),
        "p10_sent_len": round(_pct(lens, 10), 1),
        "p90_sent_len": round(_pct(lens, 90), 1),
        "max_sent_len": max(lens),
        "burstiness": burst,
        "pp_burstiness": pp_burst,
        "aperiodicity": _aperiodicity(lens),
        "mean_word_len": round(statistics.mean(len(w) for w in ws), 2),
        "syll_per_word": round(syl / n_w, 2),
        "fk_grade": round(fk, 1),
        "ttr": round(len(freqs) / n_w, 3),
        "hapax_ratio": round(hapax / n_w, 3),
        "we_per_1k": _per_1k(sum(lower.count(w) for w in ("we", "our", "us")), n_w),
        "passive_ratio": round(passive_sents / n_s, 2),
        "hedge_per_1k": _per_1k(sum(1 for w in lower if w in HEDGES), n_w),
        "booster_per_1k": _per_1k(sum(1 for w in lower if w in BOOSTERS), n_w),
        "transition_per_1k": _per_1k(
            sum(1 for s in sents if s.split() and s.split()[0].lower().strip(",")
                in TRANSITIONS), n_w),
        "semicolon_per_1k": _per_1k(text.count(";"), n_w),
        "emdash_per_1k": _per_1k(text.count(chr(0x2014)) + text.count("--"), n_w),
        "paren_per_1k": _per_1k(text.count("("), n_w),
        "colon_per_1k": _per_1k(text.count(":"), n_w),
        "numbers_per_1k": _per_1k(len(re.findall(r"\d[\d.,]*", text)), n_w),
    }


def tells(text: str) -> dict:
    low = text.lower()
    sents = sentences(text)
    n_w = len(words(text)) or 1
    found_hard = sorted({w for w in TELL_WORDS_HARD if re.search(rf"\b{re.escape(w)}\b", low)})
    found_soft = sorted({w for w in TELL_WORDS_SOFT if re.search(rf"\b{re.escape(w)}\b", low)})
    found_phrases = [p for p in TELL_PHRASES if p in low]
    found_closers = [p for p in TELL_CLOSERS if p in low]
    opener_hits = []
    for s in sents:
        sl = s.lower().lstrip("\"'(")
        for op in TELL_OPENERS:
            if sl.startswith(op):
                opener_hits.append(s[:80])
                break
    triads = re.findall(r"\w+,\s+\w+[\w\s]*,\s+and\s+\w+", text)
    dash_count = text.count(chr(0x2014)) + text.count("--")
    dash_budget = max(1, round(n_w / 1000))
    dash_excess = max(0, dash_count - dash_budget)
    hard = {
        "tell_words": found_hard,
        "tell_phrases": found_phrases,
        "closing_cliches": found_closers,
    }
    if dash_excess:
        hard["dash_excess"] = [f"{dash_excess} long dash(es) over budget"]
    # Grammar and individual terms need context; a match is not an editing verdict.
    soft = {
        "rule_of_three": triads,
        "ambiguous_words": found_soft,
        "sentence_openers": opener_hits,
        "copula_phrases": [m.group(0) for m in COPULA_DODGE.finditer(text)],
        "participle_clauses": [m.group(0).strip() for m in ING_PAD.finditer(text)],
        "negative_parallelism": [m.group(0)[:80] for m in NEG_PARALLEL.finditer(text)],
    }
    hard_count = sum(len(v) for v in hard.values())
    soft_count = sum(len(v) for v in soft.values())
    soft["rule_of_three"] = triads[:8]
    return {
        "tell_count": hard_count,
        "soft_count": soft_count,
        "emdash_count": dash_count,
        "tell_density_per_1k": _per_1k(hard_count, n_w),
        "hard_tells": {k: v for k, v in hard.items() if v},
        "soft_tells": {k: v for k, v in soft.items() if v},
    }


def predictability(text: str) -> dict:
    """Heuristic naturalness diagnostic, stdlib only.

    Each sub-signal approximates a real readability property. The composite
    `formulaicity` runs high for predictable, repetitive, low-information prose
    and low for specific, varied prose. Natural human writing sits in a middle
    band: both extremes read as unnatural, so the score is targeted two-sided,
    never minimized. It is a revision aid, not a probability of AI authorship.
    """
    ws = words(text)
    n_w = len(ws)
    if n_w == 0:
        return {"error": "empty text"}
    sents = sentences(text)
    n_s = len(sents) or 1
    lower = [w.lower() for w in ws]
    low = text.lower()

    ratio = _compress_ratio(text)
    compressibility = round(1.0 - ratio, 3) if ratio else 0.0
    tri = [tuple(lower[i:i + 3]) for i in range(len(lower) - 2)]
    novel_ngram_rate = round(len(set(tri)) / len(tri), 3) if tri else 1.0
    concreteness = round(_high_info_tokens(text) / n_w, 3)
    conc_norm = min(1.0, concreteness / 0.15)
    run = _longest_function_run(lower)
    run_norm = min(1.0, run / 6.0)
    fh = (sum(1 for p in TELL_PHRASES if p in low)
          + sum(1 for g in FORMULAIC_NGRAMS if g in low))
    fh_norm = min(1.0, fh / max(1.0, n_s / 4.0))

    formulaicity = round(max(0.0, min(1.0,
        0.28 * compressibility
        + 0.24 * (1.0 - novel_ngram_rate)
        + 0.20 * run_norm
        + 0.16 * (1.0 - conc_norm)
        + 0.12 * fh_norm)), 3)
    return {
        "compressibility": compressibility,
        "novel_ngram_rate": novel_ngram_rate,
        "concreteness": concreteness,
        "function_word_run": run,
        "formulaic_hits": fh,
        "formulaicity": formulaicity,
        "note": "higher formulaicity = more predictable/machine-shaped; natural "
                "prose sits mid-band; heuristic, not a detector verdict",
    }


DEFAULT_BANDS = {
    "mean_sent_len": [14, 30],
    "median_sent_len": [12, 28],
    "p90_sent_len": [32, 52],
    "max_sent_len": [45, 120],
    "burstiness": [0.35, 0.85],
    "fk_grade": [12, 18],
    "pp_burstiness": [0.16, 1.0],
    "aperiodicity": [0.30, 1.0],
    "formulaicity": [0.20, 0.62],
    "mean_word_len": [4.8, 6.2],
    "syll_per_word": [1.55, 2.10],
    "we_per_1k": [0, 10],
    "passive_ratio": [0.15, 0.45],
    "hedge_per_1k": [2, 8],
    "booster_per_1k": [0, 2],
    "transition_per_1k": [1, 8],
    "semicolon_per_1k": [0, 5],
    "emdash_per_1k": [0, 1],
    "paren_per_1k": [5, 45],
    "colon_per_1k": [1, 12],
    "numbers_per_1k": [0, 120],
}
ADVICE = {
    "mean_sent_len": (
        "combine short sentences that repeat a point",
        "split or tighten long sentences",
    ),
    "burstiness": ("vary sentence length with real analytical contrast", ""),
    "pp_burstiness": (
        (
            "let dense sentences and plain ones alternate where the content "
            "allows; do not add framing sentences that carry no information"
        ),
        "",
    ),
    "aperiodicity": (
        "vary sentence length irregularly, not in a fixed short/long/short cadence",
        "",
    ),
    "formulaicity": (
        (
            "let the prose settle into normal phrasing; wording varied to "
            "the point of strain reads as unnatural"
        ),
        (
            "add specific, source-supported detail and cut filler frames "
            "and repeated phrasing"
        ),
    ),
    "fk_grade": ("", "simplify overloaded subjects and stacked modifiers"),
    "passive_ratio": ("", "make claim sentences active where the actor matters"),
    "transition_per_1k": ("", "remove decorative transitions"),
    "hedge_per_1k": ("", "collapse hedge stacks"),
    "emdash_per_1k": ("", "replace extra long dashes with commas, periods, or clauses"),
    "semicolon_per_1k": ("", "use semicolons only for tightly linked clauses"),
}
SCORE_SPEC = {
    "mean_sent_len": {"dir": "band", "min_words": 80, "min_sents": 4, "weight": 1.0},
    "burstiness": {"dir": "floor", "min_words": 80, "min_sents": 6, "weight": 1.0},
    "pp_burstiness": {"dir": "floor", "min_words": 80, "min_sents": 6, "weight": 0.8},
    "aperiodicity": {"dir": "floor", "min_words": 80, "min_sents": 6, "weight": 0.5},
    "formulaicity": {"dir": "band", "min_words": 80, "min_sents": 5, "weight": 0.6},
    "fk_grade": {"dir": "ceil", "min_words": 120, "min_sents": 5, "weight": 0.5},
    "passive_ratio": {"dir": "ceil", "min_words": 120, "min_sents": 10, "weight": 0.8},
    "transition_per_1k": {
        "dir": "ceil",
        "min_words": 300,
        "min_sents": 0,
        "weight": 0.3,
    },
    "hedge_per_1k": {"dir": "ceil", "min_words": 300, "min_sents": 0, "weight": 0.3},
    "emdash_per_1k": {"dir": "ceil", "min_words": 250, "min_sents": 0, "weight": 1.0},
    "semicolon_per_1k": {
        "dir": "ceil",
        "min_words": 300,
        "min_sents": 0,
        "weight": 0.3,
    },
}


def _valid_band(band) -> bool:
    return (isinstance(band, (list, tuple)) and len(band) == 2
            and all(isinstance(x, (int, float)) and math.isfinite(x) for x in band)
            and band[0] <= band[1])


def _safe_band(bands: dict, key: str) -> list:
    """A validated [lo, hi] for `key`, falling back to the curated default when
    the supplied profile band is missing or malformed."""
    band = bands.get(key)
    return [band[0], band[1]] if _valid_band(band) else list(DEFAULT_BANDS[key])


def _target_repr(direction: str, lo: float, hi: float):
    """Direction-aware target for display: floor and ceiling metrics are
    one-sided, so showing a two-ended band would misrepresent the gate."""
    if direction == "floor":
        return f">={lo}"
    if direction == "ceil":
        return f"<={hi}"
    return [lo, hi]


def score(draft_text: str, profile: dict) -> dict:
    m = measure(draft_text)
    if "error" in m:
        return m
    t = tells(draft_text)
    pred = predictability(draft_text)
    flavor = str(profile.get("flavor") or "neutral")
    if "formulaicity" in pred:
        m["formulaicity"] = pred["formulaicity"]
    bands = {**DEFAULT_BANDS, **(profile.get("bands") or {})}
    n_w, n_s = m["n_words"], m["n_sentences"]
    rows, skipped, invalid_bands = [], [], []
    distance = 0.0
    for key, spec in SCORE_SPEC.items():
        if key not in m or key not in bands:
            continue
        band = bands[key]
        if not _valid_band(band):
            invalid_bands.append(key)
            continue
        if n_w < spec["min_words"] or n_s < spec.get("min_sents", 0):
            skipped.append(key)
            continue
        lo, hi = band
        target = _target_repr(spec["dir"], lo, hi)
        val = m[key]
        status, raw = "ok", 0.0
        if spec["dir"] in ("band", "floor") and val < lo:
            status, raw = "low", lo - val
        elif spec["dir"] in ("band", "ceil") and val > hi:
            status, raw = "high", val - hi
        if status == "ok":
            rows.append({"metric": key, "value": val, "target": target, "status": "ok"})
            continue
        span = (hi - lo) or abs(hi) or 1.0
        norm = min(2.0, round(raw / span, 2))
        wgap = round(norm * spec["weight"], 2)
        distance += wgap
        tip = ADVICE.get(key, ("adjust toward target", "adjust toward target"))[
            0 if status == "low" else 1]
        rows.append({"metric": key, "value": val, "target": target,
                     "status": status, "weighted_gap": wgap, "advice": tip})
    off = [r for r in rows if r["status"] != "ok"]
    distance = round(distance, 2)
    coverage_ok = n_w >= profile.get("min_score_words", 80) and len(rows) >= 2
    score_note = "" if coverage_ok else (
        "short passage: not enough scored metrics to certify style_distance")
    return {
        "flavor": flavor,
        "ai_tell_count": t["tell_count"],
        "ai_tell_density_per_1k": t["tell_density_per_1k"],
        "hard_tells": t["hard_tells"],
        "soft_tells": t["soft_tells"],
        "richness_watch": {
            "ttr": m["ttr"],
            "hapax_ratio": m["hapax_ratio"],
            "booster_per_1k": m["booster_per_1k"],
            "note": "review ttr and hapax changes; preserve recurring technical terms",
        },
        "naturalness": pred,
        "pp_burstiness": m.get("pp_burstiness"),
        "aperiodicity": m.get("aperiodicity"),
        "style_distance": distance,
        "n_metrics_off": len(off),
        "scored_coverage_ok": coverage_ok,
        "score_note": score_note,
        "invalid_profile_bands": invalid_bands,
        "metrics_scored": rows,
        "metrics_skipped_short_passage": skipped,
        "top_fixes": [
            f"{r['metric']}={r['value']} (target {r['target']}): {r['advice']}"
            for r in sorted(off, key=lambda r: -r.get("weighted_gap", 0))
            if r.get("advice")
        ][:6],
        "pass": (
            coverage_ok
            and not invalid_bands
            and t["tell_count"] <= profile.get("tell_tolerance", 0)
            and distance <= profile.get("distance_tolerance", 4.0)
        ),
    }


def _sample_macro_order(rng: random.Random, moves: list[str], anchor: str | None) -> list[str]:
    """A valid ordering/subset of the section's rhetorical moves: keep the anchor
    move at the front and a closing move at the end, drop at most one optional
    middle move, and lightly reorder the rest."""
    moves = list(moves)
    if len(moves) > 4 and rng.random() < 0.5:
        droppable = moves[1:-1]
        if droppable:
            moves.remove(rng.choice(droppable))
    if anchor in moves:
        moves.remove(anchor)
        head = [anchor]
    else:
        head = [moves.pop(0)]
    tail = [moves.pop()] if moves else []
    rng.shuffle(moves)
    return head + moves + tail


def sample_style(seed: int | None = None, profile: dict | None = None,
                 section: str = "generic", skeletons: dict | None = None) -> dict:
    """Draw one per-run style card within the human envelope.

    Deliberately off-center so repeated runs vary instead of collapsing to one
    machine-like set-point. Random by default; reproducible when `seed` is given.
    The card is a target for the rewrite, not a rule.
    """
    if seed is None:
        seed = random.SystemRandom().randrange(1, 2 ** 31 - 1)
    rng = random.Random(seed)
    profile = profile or {}
    skeletons = skeletons or {}
    bands = {**DEFAULT_BANDS, **(profile.get("bands") or {})}
    profile_flavor = str(profile.get("flavor") or "neutral")
    skeleton_flavor = str(skeletons.get("flavor") or profile_flavor)
    flavor = profile_flavor
    flavor_warning = ""
    if skeleton_flavor != profile_flavor:
        flavor_warning = (
            f"profile flavor {profile_flavor} differs from skeleton flavor "
            f"{skeleton_flavor}; profile flavor is reported")
    if section not in MACRO_MOVES:
        section = "generic"

    msl_lo, msl_hi = _safe_band(bands, "mean_sent_len")
    mean_target = round(rng.uniform(msl_lo, msl_hi), 1)
    b_lo, b_hi = _safe_band(bands, "burstiness")
    burst_target = round(rng.uniform((b_lo + b_hi) / 2, b_hi), 3)

    pool = []
    if isinstance(skeletons.get("transition_openers"), list):
        pool = [str(o).strip() for o in skeletons["transition_openers"] if str(o).strip()]
    if not pool:
        pool = list(DEFAULT_OPENER_POOL)
    k = max(1, min(len(pool), rng.randint(3, 5)))
    opener_mix = rng.sample(pool, k)

    return {
        "seed": seed,
        "flavor": flavor,
        "section": section,
        "rhythm_setpoint": {"mean_sent_len": mean_target,
                            "burstiness_target": burst_target},
        "opener_mix": opener_mix,
        "punctuation_lean": rng.choice(PUNCTUATION_LEANS),
        "macro_order": _sample_macro_order(rng, MACRO_MOVES[section],
                                           MACRO_ANCHOR.get(section)),
        "flavor_warning": flavor_warning,
        "note": "one sampled style for this run; draws within the selected "
                "profile bands so repeated runs vary; a target, not a rule",
    }


_SELFTEST_AI = (
    "In today's world, the study of this topic plays a crucial role in many areas. "
    "It is important to note that a wide range of factors can influence the outcome. "
    "Researchers have shown that the results are robust and comprehensive across settings. "
    "Furthermore, the analysis provides valuable insights into the underlying process. "
    "Moreover, the findings shed light on the importance of the overall framework. "
    "The approach is powerful and offers a seamless way to address the problem. "
    "Additionally, the work paves the way for a variety of future directions. "
    "In conclusion, this represents a significant step forward for the whole field."
)
_SELFTEST_HUMAN = (
    "We sequenced 48 isolates. "
    "Coverage ranged from 12x to 210x, and three samples fell below the 20x "
    "threshold we set for variant calling, so we resequenced them on a second flow cell. "
    "The dominant lineage, B.1, accounted for 61 percent of assemblies. "
    "Two genomes carried a 4.2 kb deletion spanning the spike locus; both came "
    "from the same clinic in March. "
    "This deletion was absent from the 2019 reference panel. "
    "Growth assays showed a modest fitness cost, roughly 8 percent per generation, "
    "though the confidence interval was wide. "
    "Whether the deletion persists under selection remains unclear. "
    "We flag it as a candidate for tracking, not an established variant of concern."
)
_SELFTEST_MID = (
    "We measured ten samples in the first sequencing batch and compared them with controls. "
    "Coverage varied across the run, but three samples failed the cutoff used for variant calling. "
    "The second assay recovered two of those samples after resequencing on a separate flow cell. "
    "One isolate carried a small deletion in the target locus, which was absent from controls. "
    "This pattern matched the archived clinical panel from March and did not appear later. "
    "We therefore report the deletion as a candidate signal, while keeping the claim provisional."
)
_SELFTEST_DENSE_SENTENCE = (
    "However, the samples were collected and it may possibly be seen that the "
    "values could perhaps differ."
)
_SELFTEST_PLAIN = (
    "We collected water from twelve lakes in the spring of each year. "
    "Each team filtered one liter of water on site and froze the filter within "
    "an hour. "
    "We counted cells under the microscope and wrote each count into a shared table. "
    "Two people counted every tenth filter, and their counts differed by less than "
    "five percent. "
    "The lakes in the north held fewer cells than the lakes in the south in all "
    "three years. "
    "Cell counts rose after heavy rain and fell again within ten days. "
    "We saw the same rise in lakes with farms close to the shore and in lakes "
    "with forest. "
    "Farm lakes started from a higher count, so the rise there ended at a "
    "higher level. "
    "We then asked whether the size of the lake changed the result. "
    "Small lakes gained cells faster than large lakes, but the gain did not last "
    "as long. "
    "Depth did not change the count once we took lake size into account. "
    "We tested this with a second set of samples from the next year. "
    "The second set gave the same order of lakes and the same effect of rain. "
    "One lake did not fit the trend in any year, and we do not know why. "
    "Its water stayed clear after rain, and its counts stayed low. "
    "We kept this lake in the table and marked it so that readers can leave it out. "
    "All counts, dates and field notes sit in the public archive under one record "
    "number. "
    "The code that draws each figure reads the table from that archive and needs "
    "no other input. "
    "A reader can run the code on a laptop in less than a minute. "
    "We give the commands for each step in the first section of the manual. "
    "The manual also lists the two filters that broke in the field and the dates "
    "of the heavy rain."
)


def selftest_run() -> bool:
    checks: list[tuple[str, bool, str]] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    ai, hu = predictability(_SELFTEST_AI), predictability(_SELFTEST_HUMAN)
    chk("formulaicity separates AI-shaped from human-shaped",
        ai["formulaicity"] > hu["formulaicity"] + 0.05,
        f"ai={ai['formulaicity']} human={hu['formulaicity']}")

    m_ai, m_hu = measure(_SELFTEST_AI), measure(_SELFTEST_HUMAN)
    chk("length burstiness higher for human-shaped",
        m_hu["burstiness"] > m_ai["burstiness"],
        f"ai={m_ai['burstiness']} human={m_hu['burstiness']}")
    chk("per-sentence burstiness higher for human-shaped",
        m_hu["pp_burstiness"] > m_ai["pp_burstiness"],
        f"ai={m_ai['pp_burstiness']} human={m_hu['pp_burstiness']}")
    chk("AI-shaped fixture carries more hard tells",
        tells(_SELFTEST_AI)["tell_count"] > tells(_SELFTEST_HUMAN)["tell_count"],
        f"ai={tells(_SELFTEST_AI)['tell_count']} human={tells(_SELFTEST_HUMAN)['tell_count']}")

    transitions = tells(
        "The estimate was stable across groups. "
        "Additionally, it was unchanged after incomplete records were excluded. "
        "Furthermore, both estimators agreed. Moreover, neither interval widened."
    )
    chk(
        "academic transitions remain reviewable without hard flags",
        transitions["tell_count"] == 0 and transitions["soft_count"] == 3,
    )
    representation = tells("The model represents each sample as a vector.")
    chk(
        "mathematical representation is a review candidate, not a hard tell",
        representation["tell_count"] == 0 and representation["soft_count"] == 1,
    )
    technical = tells("Mosaic genomes contain segments with distinct histories.")
    chk(
        "literal technical terms remain visible without hard flags",
        technical["tell_count"] == 0 and technical["soft_count"] == 1,
    )
    syntax = tells(
        "We repeated the assay, demonstrating agreement between runs. "
        "The assay detects not only substitutions but also deletions."
    )
    chk(
        "meaningful grammatical constructions are review candidates",
        syntax["tell_count"] == 0 and syntax["soft_count"] == 2,
    )
    filler = tells(
        "It is important to note that this groundbreaking study paves the way."
    )
    chk(
        "clear filler and promotional wording retain hard flags",
        filler["tell_count"] > 0,
    )
    triads = tells("We measured size, mass, and volume. " * 10)
    chk(
        "soft count includes matches beyond the displayed examples",
        triads["soft_count"] == 10 and len(triads["soft_tells"]["rule_of_three"]) == 8,
    )

    a1 = sample_style(seed=7, section="abstract")
    a2 = sample_style(seed=7, section="abstract")
    chk("sampler is deterministic under a fixed seed", a1 == a2)
    b1 = sample_style(seed=1, section="abstract")
    b2 = sample_style(seed=2, section="abstract")
    diverse = (b1["rhythm_setpoint"], b1["opener_mix"], b1["macro_order"],
               b1["punctuation_lean"]) != (
               b2["rhythm_setpoint"], b2["opener_mix"], b2["macro_order"],
               b2["punctuation_lean"])
    chk("sampler is diverse across seeds", diverse)
    chk("omitted seed is drawn and returned",
        isinstance(sample_style(section="generic")["seed"], int))
    fs_card = sample_style(
        seed=3,
        profile={"flavor": "fs-writing",
                 "bands": {"mean_sent_len": [23, 27], "burstiness": [0.45, 1.0]}},
        skeletons={"flavor": "fs-writing", "transition_openers": ["here", "together"]},
        section="abstract",
    )
    chk("sampler carries selected flavor",
        fs_card["flavor"] == "fs-writing"
        and set(fs_card["opener_mix"]).issubset({"here", "together"}))

    short = score("This is one short sentence.", {"bands": DEFAULT_BANDS})
    chk("short passage does not certify (coverage guard holds)",
        short.get("scored_coverage_ok") is False and short.get("pass") is False
        and bool(short.get("score_note")))
    flavored_score = score(_SELFTEST_MID, {"flavor": "fs-writing",
                                           "bands": DEFAULT_BANDS,
                                           "tell_tolerance": 99,
                                           "distance_tolerance": 99})
    chk("score carries selected flavor", flavored_score["flavor"] == "fs-writing")

    chk("formulaicity advice is oriented correctly (high=cut filler, low=settle)",
        "filler" in ADVICE["formulaicity"][1] and "settle" in ADVICE["formulaicity"][0])

    mid = score(_SELFTEST_MID, {"bands": DEFAULT_BANDS,
                                "tell_tolerance": 99, "distance_tolerance": 99})
    chk("formulaicity is scored once coverage is met (>=80 words)",
        "formulaicity" not in mid["metrics_skipped_short_passage"]
        and any(r["metric"] == "formulaicity" for r in mid["metrics_scored"]),
        f"words={mid.get('scored_coverage_ok')}")

    try:
        bad = sample_style(seed=1, profile={"bands": {"mean_sent_len": [],
                                                      "burstiness": ["x", 3]}})
        tol_ok = isinstance(bad, dict) and "rhythm_setpoint" in bad
    except Exception:
        tol_ok = False
    chk("sampler tolerates malformed profile bands without crashing", tol_ok)

    bad_band = score(_SELFTEST_MID, {"bands": {"mean_sent_len": ["x", 3]}})
    chk("malformed band is reported even when otherwise scorable",
        "mean_sent_len" in bad_band.get("invalid_profile_bands", [])
        and bad_band.get("pass") is False)

    plain = score(
        _SELFTEST_PLAIN,
        {"bands": DEFAULT_BANDS, "tell_tolerance": 99, "distance_tolerance": 99},
    )
    plain_status = {row["metric"]: row["status"] for row in plain["metrics_scored"]}
    clarity_metrics = (
        "mean_sent_len",
        "fk_grade",
        "passive_ratio",
        "transition_per_1k",
        "hedge_per_1k",
    )
    chk(
        "plain active prose is not pushed toward longer sentences, a higher "
        "reading grade, more passive voice, more transitions or more hedges",
        all(plain_status.get(metric) == "ok" for metric in clarity_metrics),
        f"status={plain_status}",
    )
    coined = predictability(
        "the warm-regime gap needs a lab-check of the evict-first hint"
    )
    chk(
        "hyphenated compounds do not count as concrete detail",
        coined["concreteness"] == 0.0,
        f"concreteness={coined['concreteness']}",
    )
    named = predictability("We sampled 48 sites near Lake Tahoe in 2019.")
    chk(
        "numbers and named entities count as concrete detail",
        named["concreteness"] > 0.0,
        f"concreteness={named['concreteness']}",
    )
    dense = score(
        " ".join([_SELFTEST_DENSE_SENTENCE] * 25),
        {
            "bands": {**DEFAULT_BANDS, "fk_grade": [0, 2]},
            "tell_tolerance": 99,
            "distance_tolerance": 99,
        },
    )
    dense_status = {row["metric"]: row["status"] for row in dense["metrics_scored"]}
    ceiling_metrics = ("fk_grade", "passive_ratio", "transition_per_1k", "hedge_per_1k")
    chk(
        "ceilings still flag passive, hedged, transition-heavy prose and a "
        "reading grade above the band",
        all(dense_status.get(metric) == "high" for metric in ceiling_metrics),
        f"status={dense_status}",
    )

    ok_all = all(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        line = f"[{'PASS' if ok else 'FAIL'}] {name}"
        if detail and not ok:
            line += f"  ({detail})"
        print(line)
    print(f"\n{sum(ok for _, ok, _ in checks)}/{len(checks)} checks passed")
    return ok_all


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError as e:
        sys.exit(f"error: cannot read {path}: {e}")


def _load_json_obj(path: str, what: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
    except OSError as e:
        sys.exit(f"error: cannot read {what} {path}: {e}")
    except json.JSONDecodeError as e:
        sys.exit(f"error: {what} {path} is not valid JSON: {e}")
    if not isinstance(obj, dict):
        sys.exit(f"error: {what} {path} must be a JSON object")
    return obj


def main() -> None:
    ap = argparse.ArgumentParser(description="academic-writing stylometry + AI-tell scorer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("measure", "tells"):
        p = sub.add_parser(name)
        p.add_argument("file", help="text file, or - for stdin")
    sp = sub.add_parser("score")
    sp.add_argument("--draft", required=True)
    sp.add_argument("--profile", required=True, help="fingerprint.json from profile_corpus.py")
    smp = sub.add_parser("sample", help="draw one per-run style card")
    smp.add_argument("--seed", type=int, default=None, help="omit to draw (and print) a random seed")
    smp.add_argument("--profile", default=None, help="optional fingerprint.json for local bands")
    smp.add_argument("--skeletons", default=None, help="optional skeletons.json for the opener pool")
    smp.add_argument("--section", default="generic",
                     choices=sorted(MACRO_MOVES.keys()))
    sub.add_parser("selftest", help="run bundled fixtures and self-checks")
    args = ap.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest_run() else 1)

    if args.cmd == "measure":
        out = measure(_read(args.file))
    elif args.cmd == "tells":
        out = tells(_read(args.file))
    elif args.cmd == "sample":
        profile = _load_json_obj(args.profile, "profile") if args.profile else None
        skeletons = _load_json_obj(args.skeletons, "skeletons") if args.skeletons else None
        out = sample_style(seed=args.seed, profile=profile, section=args.section,
                           skeletons=skeletons)
    else:
        profile = _load_json_obj(args.profile, "profile")
        out = score(_read(args.draft), profile)
    json.dump(out, sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
