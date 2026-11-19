#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["spacy==3.8.18", "en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"]
# ///
"""Extract candidate rhetorical frames by masking exact source noun spans.

No candidate is accepted automatically. Run with one process and the small
English parser; sentence offsets index the unchanged canonical Unicode text.
Methods, negative findings and limitations admit shorter complete sentences.
Protected generic noun chunks remain fixed; topic-bearing chunks remain unsafe.
"""

import argparse
import hashlib
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

import spacy
from spacy.language import Language
from spacy.tokens import Span, Token

logger = logging.getLogger(__name__)
WORD = re.compile(r"\b[\w]+(?:[-\u2019'][\w]+)*\b")
ARTIFACT = re.compile(
    r"[<>\[\]{}()@]|https?://|\b(?:fig(?:ure)?s?\.?|tables?|doi|et al)\b|\d+\.\d+\.\d+",
    re.IGNORECASE,
)
SAFE_MODIFIERS = {
    "same",
    "different",
    "similar",
    "consistent",
    "possible",
    "likely",
    "unlikely",
    "clear",
    "unclear",
    "important",
    "significant",
    "available",
    "previous",
    "additional",
    "further",
    "small",
    "large",
    "high",
    "low",
    "greater",
    "lower",
    "higher",
    "better",
    "best",
    "first",
    "last",
    "other",
    "more",
    "most",
    "less",
    "least",
    "many",
    "few",
    "several",
    "both",
    "each",
    "challenging",
    "difficult",
    "necessary",
    "sufficient",
    "common",
    "able",
}
CUES = (
    (
        "negative_evidence",
        (
            r"\b(?:no evidence|did not (?:find|detect|observe)|failed to "
            r"(?:detect|find)|not supported|did not differ|"
            r"no (?:significant )?(?:differences?|effects?|associations?|"
            r"correlations?|changes?|support)|"
            r"(?:was|were) not (?:detected|observed|found|identified))\b"
        ),
    ),
    (
        "limitation",
        (
            r"\b(?:limited by|limitation|cannot rule out|could not exclude|should be "
            r"interpreted with caution|remains? (?:unclear|unknown|unresolved)|"
            r"we were unable to|could not (?:determine|distinguish|assess|establish)|"
            r"(?:cannot|could not) be (?:determined|excluded|assessed|resolved)|"
            r"not possible to determine)\b"
        ),
    ),
    (
        "purpose",
        (
            r"^(?:to (?:assess|test|determine|investigate|evaluate|identify|examine|"
            r"understand|compare|explore|quantify|characterize)|in order to)\b"
            r"|\b(?:we (?:aimed|sought) to|our (?:aim|objective) was to)\b"
        ),
    ),
    ("contrast", r"^(?:however|in contrast|although|whereas|nevertheless|despite)\b"),
    (
        "interpretation",
        (
            r"\b(?:suggest(?:s|ed)? that|indicat(?:e|es|ed) that|consistent with|may "
            r"reflect|could reflect|may be explained|suggest(?:s|ed)? "
            r"(?:a|an|the)|implies? that)\b|^Taken together,"
        ),
    ),
    (
        "observation",
        (
            r"\b(?:we (?:also |further |previously )?(?:found|observed|detected|"
            r"identified|show|showed|report|reported|demonstrate|demonstrated)|"
            r"(?:our|the) (?:analysis|analyses|results) (?:show|shows|showed|"
            r"reveal|reveals|revealed|demonstrate|demonstrates|demonstrated)|"
            r"was observed|were observed)\b"
        ),
    ),
    (
        "method",
        (
            r"\b(?:we (?:also |then |next |further )?(?:used|performed|calculated|"
            r"estimated|compared|measured|assessed|analyzed|analysed|evaluated|"
            r"tested|examined|quantified|computed|subjected|removed|disabled|"
            r"reran|repeated|calibrated|validated)|was "
            r"(?:calculated|estimated|measured)|were "
            r"(?:calculated|estimated|measured))\b"
        ),
    ),
    (
        "background",
        (
            r"\b(?:is known to|are known to|previous studies have|has been shown "
            r"to|have been shown to)\b"
        ),
    ),
    (
        "method",
        (
            r"\b(?:was|were) (?:also |then |subsequently )?"
            r"(?:used|performed|compared|analyzed|analysed|evaluated|tested|examined|"
            r"quantified|computed|treated|exposed|simulated|collected|selected|"
            r"prepared|obtained|determined|assessed|conducted|generated|"
            r"subjected|removed|disabled|run|rerun|repeated|calibrated|validated|"
            r"incubated|extracted|amplified|sequenced|aligned|filtered|normalized)\b"
        ),
    ),
)
SHORT_FAMILIES = {"method", "negative_evidence", "limitation"}
PROTECTED_GENERIC_HEADS = {
    "difference",
    "effect",
    "association",
    "correlation",
    "change",
    "support",
}
PROTECTED_MODIFIERS = {
    "only",
    "no",
    "not",
    "neither",
    "nor",
    "none",
    "few",
    "little",
    "lack",
    "possible",
    "potential",
    "putative",
    "probable",
    "presumed",
    "apparent",
    "unlikely",
    "likely",
}
FIXED_PHRASES = {
    "which",
    "who",
    "whom",
    "whose",
    "what",
    "that",
    "we",
    "it",
    "they",
    "this",
    "these",
    "those",
    "no evidence",
    "evidence",
    "these results",
    "our results",
    "the results",
    "this study",
    "our study",
    "previous studies",
    "a limitation",
    "the possibility",
    "the other hand",
    "the one hand",
}
FIXED_NOUNS = {
    "evidence",
    "result",
    "study",
    "possibility",
    "contrast",
    "order",
    "limitation",
    "hand",
}


def classify(sentence: str) -> str:
    """Return the first specific cue family, or empty for unclassified text."""
    for family, pattern in CUES:
        if re.search(pattern, sentence, re.IGNORECASE):
            return family
    return ""


def is_clean_sentence(sentence: str, *, minimum_words: int = 10) -> bool:
    """Exclude markup, citations, captions, fragments and awkward whitespace."""
    words = WORD.findall(sentence)
    return (
        minimum_words <= len(words) <= 45
        and sentence[0].isupper()
        and sentence.endswith(".")
        and not ARTIFACT.search(sentence)
        and "\n" not in sentence
        and "\t" not in sentence
        and sentence.count(chr(34)) % 2 == 0
        and sentence.count("\u201c") == sentence.count("\u201d")
        and not re.search(r"[,;:\-\u2013\u2014]\s*\.$", sentence)
        and not re.search(r"\b(?:by|in|from|to|of|and|or)\s*\.$", sentence)
        and not re.search(r"\s{2,}|\(\s*\d|\b(?:19|20)\d{2}\b|[A-Za-z]\d+", sentence)
    )


def mask_spans(
    sentence: str, spans: list[tuple[int, int, str]]
) -> tuple[str, dict[str, str]]:
    """Replace nonoverlapping Unicode spans while keeping every other byte of text."""
    fragments: list[str] = []
    originals: dict[str, str] = {}
    cursor = 0
    for index, (start, end, kind) in enumerate(sorted(spans), 1):
        if start < cursor or end <= start or end > len(sentence):
            raise ValueError("invalid or overlapping source spans")
        name = f"{'number' if kind == 'number' else 'phrase'}_{index}"
        fragments.extend((sentence[cursor:start], "{" + name + "}"))
        originals[name] = sentence[start:end]
        cursor = end
    fragments.append(sentence[cursor:])
    return "".join(fragments), originals


def extract_sentence(sentence: Span) -> dict[str, Any]:
    """Return a candidate frame or an empty mapping when parsing is unsafe."""
    text = sentence.text
    family = classify(text)
    minimum_words = 7 if family in SHORT_FAMILIES else 10
    if not family or not is_clean_sentence(text, minimum_words=minimum_words):
        return {}
    spans = _noun_spans(sentence)
    if not spans:
        return {}
    spans.extend(
        (
            token.idx - sentence.start_char,
            token.idx + len(token.text) - sentence.start_char,
            "number",
        )
        for token in sentence
        if token.like_num
        and any(character.isdecimal() for character in token.text)
        and not _covered(token.idx - sentence.start_char, spans)
    )
    if not 1 <= len(spans) <= 8 or not _safe_literals(sentence, spans):
        return {}
    template, originals = mask_spans(text, spans)
    if re.search(r"\}\s+\{", template):
        return {}
    fixed_words = len(WORD.findall(re.sub(r"\{[^}]+\}", "", template)))
    minimum_fixed = 9 if len(spans) == 1 else 6
    if family in SHORT_FAMILIES:
        minimum_fixed = 6 if len(spans) == 1 else 4
    if fixed_words < minimum_fixed or fixed_words / len(WORD.findall(text)) < 0.35:
        return {}
    slots = {
        name: _slot_constraints(sentence, start, end, kind)
        for name, (start, end, kind) in zip(originals, sorted(spans), strict=True)
    }
    return {
        "family": family,
        "template": template,
        "slots": slots,
        "original_slots": originals,
    }


def build_candidates(
    paper: dict[str, Any],
    corpus_root: Path,
    nlp: Language,
    *,
    counts: Counter[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract candidates with exact provenance from one verified source."""
    source_metadata = {
        key: paper[key]
        for key in (
            "paper_id",
            "doi",
            "year",
            "title",
            "license",
            "authors",
            "license_url",
            "xml_path",
            "xml_sha256",
            "extraction",
        )
    }
    if (
        not isinstance(source_metadata["authors"], list)
        or not source_metadata["authors"]
    ):
        raise ValueError("source authors must be a nonempty list")
    counts = counts if counts is not None else Counter()
    counts.update(
        dict.fromkeys(
            (
                "sentences_processed",
                "rejected_extraction",
                "rejected_section",
                "candidates",
            ),
            0,
        )
    )
    source_path = _source_path(corpus_root, paper["text_path"])
    raw = source_path.read_bytes()
    text = raw.decode("utf-8")
    text_hash = hashlib.sha256(raw).hexdigest()
    if text_hash != paper["text_sha256"]:
        raise ValueError(f"source hash mismatch: {source_path}")
    sections = _read_sections(paper, corpus_root)
    records = []
    paper_hash = hashlib.sha256(str(paper["paper_id"]).encode()).hexdigest()[:10]
    nlp.max_length = max(nlp.max_length, len(text) + 1)
    for sentence in nlp(text).sents:
        counts["sentences_processed"] += 1
        candidate = extract_sentence(sentence)
        if not candidate:
            counts["rejected_extraction"] += 1
            continue
        section = next(
            (
                item["heading"]
                for item in sections
                if item["start"] <= sentence.start_char
                and sentence.end_char <= item["end"]
            ),
            "",
        )
        if not section or re.search(
            r"\b(?:references?|bibliography|acknowledg(?:e)?ments?|funding|"
            r"supplement(?:ary)?|captions?|tables?|reviewers?|comments?|reply|"
            r"decision letter|peer review|elife digest|editorial summar(?:y|ies)|"
            r"author (?:reply|responses?|contributions?))\b|^responses?$",
            section,
            re.IGNORECASE,
        ):
            counts["rejected_section"] += 1
            continue
        counts["candidates"] += 1
        digest = hashlib.sha256(sentence.text.encode()).hexdigest()
        candidate.update(
            id=f"gv-{candidate['family']}-{paper_hash}-{digest[:12]}",
            section=section,
            source={
                **source_metadata,
                "path": str(source_path.relative_to(corpus_root.resolve())),
                "sentence": sentence.text,
                "sentence_sha256": digest,
                "text_sha256": text_hash,
                "start": sentence.start_char,
                "end": sentence.end_char,
            },
            review={
                "status": "candidate",
                "method": "spaCy 3.8.18/en_core_web_sm 3.8.0 exact noun-span "
                "masking; bounded rhetorical cues",
                "notes": "Requires editorial review by a person or agent for "
                "transferability, grammar, classification and reuse rights. "
                "Source number hints do not prove grammatical agreement. "
                "Capitalize a sentence-initial noun slot; check proper-name "
                "case and agreement with coordinated subjects editorially.",
            },
        )
        records.append(candidate)
    return records


def _slot_constraints(
    sentence: Span, start: int, end: int, kind: str
) -> dict[str, Any]:
    """Record number only for an unambiguous fixed agreement relation."""
    constraints: dict[str, Any] = {
        "type": kind,
        "max_words": 12 if kind == "noun_phrase" else 3,
    }
    chunk = sentence.doc.char_span(
        sentence.start_char + start, sentence.start_char + end
    )
    if kind != "noun_phrase" or chunk is None:
        return constraints
    verbs = [
        verb
        for head in _agreement_heads(chunk.root)
        for verb in [
            head,
            *[child for child in head.children if child.dep_ in {"aux", "auxpass"}],
        ]
    ]
    if any(token.tag_ == "MD" for token in verbs):
        return constraints
    agreement = set()
    for token in verbs:
        if token.lower_ in {"is", "was", "has", "does"} or token.tag_ == "VBZ":
            agreement.add("singular")
        elif token.lower_ in {"are", "were", "have", "do"} or token.tag_ == "VBP":
            agreement.add("plural")
    if len(agreement) == 1 and chunk.root.lower_ not in {"i", "you"}:
        constraints["number"] = agreement.pop()
    return constraints


def _agreement_heads(root: Token) -> list[Token]:
    """Find direct, existential and clear relative agreement, not pronoun guesses."""
    if root.dep_ == "conj" or any(child.dep_ == "conj" for child in root.children):
        return []
    heads = []
    subjects = [
        child for child in root.head.children if child.dep_ in {"nsubj", "nsubjpass"}
    ]
    if subjects == [root] or (
        root.dep_ == "attr"
        and any(child.dep_ == "expl" for child in root.head.children)
    ):
        heads.append(root.head)
    for child in root.children:
        if child.dep_ != "relcl" or root.dep_ not in {
            "nsubj",
            "nsubjpass",
            "dobj",
            "attr",
        }:
            continue
        relative_subjects = [
            token for token in child.children if token.dep_ in {"nsubj", "nsubjpass"}
        ]
        if (
            len(relative_subjects) == 1
            and relative_subjects[0].lower_ in {"who", "that"}
            and relative_subjects[0].i == root.i + 1
        ):
            heads.append(child)
    return heads


def _fixed_connective(chunk: Span) -> bool:
    """Recognize short rhetorical prepositional phrases in their local context."""
    previous = chunk.doc[chunk.start - 1].lower_ if chunk.start else ""
    following = chunk.doc[chunk.end].lower_ if chunk.end < len(chunk.doc) else ""
    phrase = chunk.text.lower()
    if phrase == "the fact" and following == "that":
        return True
    if previous == "with" and phrase == "the exception" and following == "of":
        return True
    if previous == "for":
        return phrase == "example"
    if previous == "by":
        return phrase == "contrast"
    if previous != "in":
        return False
    if phrase == "response":
        return following == "to"
    if phrase == "order":
        return chunk.end < len(chunk.doc) and chunk.doc[chunk.end].lower_ == "to"
    return phrase in {
        "contrast",
        "addition",
        "summary",
        "conclusion",
        "this case",
        "this context",
    }


def _noun_spans(sentence: Span) -> list[tuple[int, int, str]]:
    spans = []
    for chunk in sentence.noun_chunks:
        if (
            chunk.text.lower() in FIXED_PHRASES
            or _fixed_connective(chunk)
            or _fixed_protected_chunk(chunk)
        ):
            continue
        if (
            len(WORD.findall(chunk.text)) > 12
            or any(token.lower_ in PROTECTED_MODIFIERS for token in chunk)
            or re.search(r"[.,;:!?()\[\]{}]", chunk.text)
            or any(
                token.pos_ in {"VERB", "AUX", "SCONJ"}
                or token.tag_ in {"WDT", "WP", "WP$"}
                or token.dep_ in {"relcl", "ccomp", "advcl"}
                for token in chunk
            )
        ):
            return []
        spans.append(
            (
                chunk.start_char - sentence.start_char,
                chunk.end_char - sentence.start_char,
                "noun_phrase",
            )
        )
    return spans


def _fixed_protected_chunk(chunk: Span) -> bool:
    """Keep generic negated or hedged chunks without retaining topic modifiers."""
    return (
        chunk.root.lemma_.lower() in PROTECTED_GENERIC_HEADS
        and any(token.lower_ in PROTECTED_MODIFIERS for token in chunk)
        and all(
            token == chunk.root
            or token.lower_ in PROTECTED_MODIFIERS
            or token.pos_ == "DET"
            or (token.pos_ == "ADJ" and token.lower_ in SAFE_MODIFIERS)
            for token in chunk
        )
    )


def _covered(offset: int, spans: list[tuple[int, int, str]]) -> bool:
    return any(start <= offset < end for start, end, _ in spans)


def _safe_literals(sentence: Span, spans: list[tuple[int, int, str]]) -> bool:
    if not _safe_relations(sentence, spans):
        return False
    connective_tokens = {
        token.i
        for chunk in sentence.noun_chunks
        if _fixed_connective(chunk)
        or chunk.text.lower() in FIXED_PHRASES
        or _fixed_protected_chunk(chunk)
        for token in chunk
    }
    for token in sentence:
        if (
            token.i == sentence.start
            and token.lower_ in {"first", "second", "third"}
            and token.i + 1 < sentence.end
            and sentence.doc[token.i + 1].text == ","
        ):
            continue
        if token.i in connective_tokens or _covered(
            token.idx - sentence.start_char, spans
        ):
            continue
        if (
            token.pos_ in {"NOUN", "PROPN", "NUM"}
            and token.lemma_.lower() not in FIXED_NOUNS
        ):
            return False
        if token.pos_ == "ADJ" and token.lemma_.lower() not in SAFE_MODIFIERS:
            return False
        if token.tag_ == "VBG" and token.dep_ in {
            "pobj",
            "nsubj",
            "nsubjpass",
            "dobj",
            "attr",
        }:
            return False
        if token.ent_type_ or any(character.isdigit() for character in token.text):
            return False
    return True


def _safe_relations(sentence: Span, spans: list[tuple[int, int, str]]) -> bool:
    """Reject relational syntax whose required modifier or list is hidden."""
    fixed = [
        token
        for token in sentence
        if not _covered(token.idx - sentence.start_char, spans)
    ]
    fixed_words = {token.lower_ for token in fixed}
    if "respectively" in fixed_words and not fixed_words.intersection({"and", "or"}):
        return False
    if "than" in fixed_words and not any(
        token.tag_ in {"JJR", "RBR"} or token.lower_ in {"more", "less", "rather"}
        for token in fixed
    ):
        return False
    return not any(
        _covered(token.idx - sentence.start_char, spans)
        and (
            token.tag_ in {"JJR", "RBR"}
            or (token.lower_ in {"distinct", "different"} and "from" in fixed_words)
            or (token.lower_ == "similar" and "to" in fixed_words)
        )
        for token in sentence
    )


def _source_path(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"source escapes corpus root: {name}")
    return path


def _read_sections(paper: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    sections = json.loads(
        _source_path(root, paper["sections_path"]).read_text(encoding="utf-8")
    )
    if not isinstance(sections, list):
        raise TypeError(
            "sections_path must contain a list of heading/start/end records"
        )
    return sections


def main() -> int:
    """Read a verified manifest and write candidates, never accepted entries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-per-paper", type=int, default=10)
    parser.add_argument("--report", type=Path, help="Per-source processing counts")
    args = parser.parse_args()
    if args.max_per_paper < 1:
        parser.error("--max-per-paper must be positive")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    manifest_bytes = args.manifest.read_bytes()
    nlp = spacy.load("en_core_web_sm")
    papers = [
        json.loads(line)
        for line in manifest_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]
    selected = []
    reports = []
    seen: set[str] = set()
    for paper in papers:
        if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", json.dumps(paper)):
            raise ValueError("manifest contains an email address")
        extraction_counts: Counter[str] = Counter()
        candidates = build_candidates(
            paper, args.corpus_root, nlp, counts=extraction_counts
        )
        counts: Counter[str] = Counter()
        ranked = []
        for candidate in sorted(
            candidates, key=lambda item: (item["family"], item["id"])
        ):
            ranked.append((counts[candidate["family"]], candidate["id"], candidate))
            counts[candidate["family"]] += 1
        chosen = []
        for _, _, item in sorted(ranked, key=lambda row: (row[0], row[1])):
            if len(chosen) < args.max_per_paper and item["template"] not in seen:
                chosen.append(item)
                seen.add(item["template"])
        reports.append(
            {
                "paper_id": paper["paper_id"],
                **extraction_counts,
                "selected": len(chosen),
            }
        )
        selected.extend(chosen)
        logger.info(
            "%s: %d eligible, %d selected",
            paper["paper_id"],
            len(candidates),
            len(chosen),
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in selected),
        encoding="utf-8",
    )
    report_path = args.report or args.output.with_suffix(".report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                "papers": reports,
                "candidates_written": len(selected),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    logger.info("Wrote %d candidates; none are accepted", len(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
