"""Apply exact, source-derived sentence frames and verify their text receipts.

Checks prove text integrity against bank metadata, not meaning or grammar.
Slot inputs use lexical bounds and a heuristic common-clause guard.
Offsets count Unicode code points; hashes cover exact UTF-8 file bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from typing import cast
from urllib.parse import quote, urlsplit

LOGGER = logging.getLogger(__name__)
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
CLAUSE = re.compile(
    r"\b(?:because|whereas|although|which|while|but)\b|"
    r"\bthat\s+(?:increased|decreased|caused|supports?|indicates?)\b|"
    r"\b(?:we|they|he|she|it|you|there)\b|"
    r"\b(?:are|was|were|has|have|had|does|did|can|could|will|would|"
    r"should|must|shall|found|showed|observed|demonstrated|suggests|suggested)\b",
    re.IGNORECASE,
)
SEARCH_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "by",
        "from",
        "and",
        "or",
        "we",
        "it",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
    ]
)
# Finite forms and selected derivations: related actions are not interchangeable.
SEARCH_VARIANTS = {
    "find": "finds found finding findings",
    "identify": "identifies identified identifying identification",
    "obtain": "obtains obtained obtaining",
    "extract": "extracts extracted extracting extraction",
    "collect": "collects collected collecting collection",
    "run": "runs ran running",
    "test": "tests tested testing",
    "examine": "examines examined examining examination",
    "evaluate": "evaluates evaluated evaluating evaluation",
    "show": "shows showed shown showing",
    "suggest": "suggests suggested suggesting",
    "indicate": "indicates indicated indicating indication",
    "confirm": "confirms confirmed confirming confirmation",
    "validate": "validates validated validating validation",
    "repeat": "repeats repeated repeating repetition",
    "incubate": "incubates incubated incubating incubation",
    "compare": "compares compared comparing comparison comparisons",
    "detect": "detects detected detecting detection detections",
    "exclude": "excludes excluded excluding exclusion exclusions",
    "treat": "treats treated treating treatment treatments",
    "expose": "exposes exposed exposing exposure exposures",
    "subject": "subjects subjected subjecting",
    "differ": "differs differed differing difference differences",
    "observe": "observes observed observing observation observations",
    "assess": "assesses assessed assessing",
    "remove": "removes removed removing",
    "simulate": "simulates simulated simulating",
    "erode": "erodes eroded eroding",
    "calibrate": "calibrates calibrated calibrating",
    "disable": "disables disabled disabling",
    "rerun": "reruns reran rerunning",
    "measure": "measures measured measuring",
    "calculate": "calculates calculated calculating",
    "estimate": "estimates estimated estimating",
    "determine": "determines determined determining",
    "use": "uses used using",
    "perform": "performs performed performing",
    "generate": "generates generated generating",
    "establish": "establishes established establishing",
    "resolve": "resolves resolved resolving",
    "distinguish": "distinguishes distinguished distinguishing",
    "analyse": (
        "analyses analysed analysing analysis analyze analyzes analyzed analyzing"
    ),
    "characterise": (
        "characterises characterised characterising characterize characterizes "
        "characterized characterizing"
    ),
    "group": "groups",
    "sample": "samples",
    "limit": "limits limited limiting limitation limitations",
}
SEARCH_NORMALIZATION = {
    variant: base
    for base, variants in SEARCH_VARIANTS.items()
    for variant in variants.split()
}


@dataclass(frozen=True)
class Slot:
    """Lexical limits; number agreement still needs editorial review."""

    kind: str
    max_words: int
    number: str


@dataclass(frozen=True)
class Scaffold:
    """A validated frame and the source metadata retained in receipts."""

    identifier: str
    family: str
    section: str
    template: str
    slots: dict[str, Slot]
    source: dict[str, object]
    usage_notes: str


@dataclass(frozen=True)
class Bank:
    """Accepted frames tied to the exact bank bytes."""

    records: dict[str, Scaffold]
    sha256: str


@dataclass(frozen=True)
class SearchHit:
    """Lexical evidence, not a judgement of semantic fit."""

    record: Scaffold
    fields: dict[str, list[str]]
    score: tuple[int, int, int]


def load_bank(path: Path) -> Bank:
    """Reject invalid records, duplicate IDs, and empty banks."""
    raw = path.read_bytes()
    records: dict[str, Scaffold] = {}
    for line_number, line in enumerate(raw.decode("utf-8").split("\n"), 1):
        if not line.strip():
            continue
        record = parse_scaffold(as_object(json.loads(line)))
        if record.identifier in records:
            raise ValueError(f"duplicate ID at line {line_number}: {record.identifier}")
        records[record.identifier] = record
    if not records:
        raise ValueError("bank contains no accepted scaffolds")
    return Bank(records, digest(raw))


def parse_scaffold(record: dict[str, object]) -> Scaffold:
    """Validate metadata and exact reconstruction before accepting a frame."""
    if EMAIL.search(json.dumps(record, ensure_ascii=False)):
        raise ValueError("email addresses are forbidden in bank records")
    review = as_object(record["review"])
    if review["status"] != "accepted":
        raise ValueError("bank records must have review.status=accepted")
    require_text(review, "method")
    usage_notes = require_text(review, "notes", allow_empty=True)
    source = as_object(record["source"])
    validate_source_metadata(source)
    slots = {
        name: parse_slot(value) for name, value in as_object(record["slots"]).items()
    }
    template = require_text(record, "template")
    fields = template_fields(template)
    if not fields or fields != set(slots):
        raise ValueError("template fields must match declared slots exactly")
    scaffold = Scaffold(
        require_text(record, "id"),
        require_text(record, "family"),
        require_text(record, "section"),
        template,
        slots,
        source,
        usage_notes,
    )
    originals = as_object(record["original_slots"])
    if set(originals) != fields or not all(
        isinstance(v, str) for v in originals.values()
    ):
        raise ValueError("original_slots must contain exactly the string slot values")
    if template.format_map(originals) != source["sentence"]:
        raise ValueError(f"source reconstruction failed for {scaffold.identifier}")
    render(scaffold, originals)
    return scaffold


def render(scaffold: Scaffold, values: dict[str, object]) -> str:
    """Render with exact literals after conservative lexical slot checks."""
    if set(values) != set(scaffold.slots):
        raise ValueError(f"missing or extra slots for {scaffold.identifier}")
    for name, specification in scaffold.slots.items():
        validate_value(name, values[name], specification)
    return scaffold.template.format_map(values)


def apply_requests(
    draft: str, requests: object, bank: Bank
) -> tuple[str, dict[str, object]]:
    """Replace verified nonoverlapping input spans and retain final offsets."""
    if not isinstance(requests, list):
        raise TypeError("requests must be a JSON array")
    ordered = sorted(
        (as_object(request) for request in requests), key=lambda r: integer(r, "start")
    )
    pieces: list[str] = []
    replacements: list[dict[str, object]] = []
    cursor = 0
    output_length = 0
    for request in ordered:
        start, end = validate_span(request, draft)
        if start < cursor:
            raise ValueError("replacement spans overlap")
        identifier = require_text(request, "id")
        scaffold = lookup_scaffold(bank, identifier)
        slots = as_object(request["slots"])
        replacement = render(scaffold, slots)
        prefix = draft[cursor:start]
        output_length += len(prefix)
        replacements.append(
            {
                "start": output_length,
                "end": output_length + len(replacement),
                "input_start": start,
                "input_end": end,
                "original": request["original"],
                "id": identifier,
                "slots": slots,
                "source": scaffold.source,
            }
        )
        pieces.extend((prefix, replacement))
        output_length += len(replacement)
        cursor = end
    pieces.append(draft[cursor:])
    output = "".join(pieces)
    return output, {
        "version": 1,
        "bank_sha256": bank.sha256,
        "input_sha256": digest(draft.encode("utf-8")),
        "output_sha256": digest(output.encode("utf-8")),
        "replacements": replacements,
    }


def check_receipt(
    draft: str, receipt: dict[str, object], bank: Bank
) -> dict[str, object]:
    """Reconstruct the input and verify each rendered span against the bank."""
    if receipt["version"] != 1 or receipt["bank_sha256"] != bank.sha256:
        raise ValueError("receipt version or bank hash mismatch")
    if receipt["output_sha256"] != digest(draft.encode("utf-8")):
        raise ValueError("output file hash mismatch")
    replacements = receipt["replacements"]
    if not isinstance(replacements, list):
        raise TypeError("receipt replacements must be a JSON array")
    pieces: list[str] = []
    cursor = 0
    input_length = 0
    for value in replacements:
        replacement = as_object(value)
        scaffold = lookup_scaffold(bank, require_text(replacement, "id"))
        expected = render(scaffold, as_object(replacement["slots"]))
        start, end = integer(replacement, "start"), integer(replacement, "end")
        if not cursor <= start < end <= len(draft) or draft[start:end] != expected:
            raise ValueError(
                "receipt spans overlap, are out of bounds, or differ from template"
            )
        if replacement["source"] != scaffold.source:
            raise ValueError("receipt source provenance differs from bank")
        prefix = draft[cursor:start]
        original = require_text(replacement, "original")
        input_length += len(prefix)
        if (replacement["input_start"], replacement["input_end"]) != (
            input_length,
            input_length + len(original),
        ):
            raise ValueError("receipt input offsets mismatch")
        pieces.extend((prefix, original))
        input_length += len(original)
        cursor = end
    pieces.append(draft[cursor:])
    if receipt["input_sha256"] != digest("".join(pieces).encode("utf-8")):
        raise ValueError("reconstructed input hash mismatch")
    return {
        "ok": True,
        "replacements_checked": len(replacements),
        "bank_sha256": bank.sha256,
        "scope": "exact text and bank provenance; source files not read; not semantics",
    }


def check_review(
    review: dict[str, object], receipt: dict[str, object]
) -> dict[str, object]:
    """Validate review records, without certifying review or prose quality."""
    if integer(review, "version") != 1:
        raise ValueError("review version must be 1")
    residual_count = 0
    for phase, hash_key in (("initial", "input_sha256"), ("final", "output_sha256")):
        audit = as_object(review[phase])
        if require_text(audit, "sha256") != receipt[hash_key]:
            raise ValueError(f"{phase} review hash mismatch")
        require_text(audit, "reviewer")
        allowed = {"rejected", "residual"}
        if phase == "initial":
            allowed |= {"open", "fixed"}
        count = check_findings(audit["findings"], allowed)
        if phase == "final":
            residual_count = count
            notes = as_object(audit["notes"])
            for topic in ("meaning", "readability", "flow", "style"):
                require_text(notes, topic)
    return {
        "review_record_checked": True,
        "residual_findings": residual_count,
        "review_scope": (
            "records and hash consistency only; not proof of review, "
            "independence, semantics or quality"
        ),
    }


def check_findings(value: object, allowed: set[str]) -> int:
    """Require explicit findings and count declared source gaps."""
    if not isinstance(value, list):
        raise TypeError("review findings must be a JSON array")
    residual_count = 0
    for item in value:
        finding = as_object(item)
        for field in ("quote", "issue", "reason"):
            require_text(finding, field)
        disposition = require_text(finding, "disposition")
        if disposition not in allowed:
            raise ValueError(f"invalid review finding disposition: {disposition}")
        residual_count += disposition == "residual"
    return residual_count


def verify_sources(bank: Bank, corpus_root: Path) -> None:
    """Check full-text hashes and Unicode offsets within an explicit corpus root."""
    root = corpus_root.resolve()
    cached: dict[Path, tuple[str, str]] = {}
    for scaffold in bank.records.values():
        source = scaffold.source
        path = (root / require_text(source, "path")).resolve()
        if not path.is_relative_to(root):
            raise ValueError("source path escapes corpus root")
        if path not in cached:
            raw = path.read_bytes()
            cached[path] = (raw.decode("utf-8"), digest(raw))
        text, sha256 = cached[path]
        if sha256 != source["text_sha256"]:
            raise ValueError(f"source file hash mismatch: {path}")
        start, end = integer(source, "start"), integer(source, "end")
        if text[start:end] != source["sentence"]:
            raise ValueError(f"source offsets mismatch: {scaffold.identifier}")


def export_mcp(bank: Bank) -> str:
    """Emit deterministic upstream original-format records without editing them."""
    exported = []
    for number, identifier in enumerate(sorted(bank.records), 1):
        scaffold = bank.records[identifier]
        instructions = "; ".join(
            f"{name}: {slot.kind}, <= {slot.max_words} words, number={slot.number}"
            for name, slot in scaffold.slots.items()
        )
        exported.append(
            json.dumps(
                {
                    "id": number,
                    "type": "post",
                    "title": f"{scaffold.family}: {identifier}",
                    "url": "https://doi.org/"
                    + quote(require_text(scaffold.source, "doi"), safe="/"),
                    "text": (
                        f"{scaffold.template}\nFrame-ID: {scaffold.identifier}\n"
                        f"Use: {scaffold.usage_notes}\nSlots: {instructions}\n"
                        f"{source_attribution(scaffold)}"
                    ),
                    "copy_blocks": [],
                    "nsfw": False,
                    "canonical_id": identifier,
                    "bank_sha256": bank.sha256,
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(exported) + "\n"


def source_attribution(scaffold: Scaffold) -> str:
    """Require source attribution when generating a portable export."""
    source = scaffold.source
    authors = source.get("authors")
    if (
        not isinstance(authors, list)
        or not authors
        or not all(isinstance(author, str) and author.strip() for author in authors)
    ):
        raise ValueError(f"export requires source.authors for {scaffold.identifier}")
    author_names = "; ".join(cast("list[str]", authors))
    license_url = require_text(source, "license_url")
    return (
        f"Source: {author_names}. {source['title']} ({source['year']}). "
        f"DOI: {source['doi']}. License: {source['license']} ({license_url}). "
        "Adaptation: source sentence with declared phrase slots."
    )


def lookup_scaffold(bank: Bank, identifier: str) -> Scaffold:
    """Resolve a canonical ID with an actionable error."""
    try:
        return bank.records[identifier]
    except KeyError as error:
        raise ValueError(f"unknown scaffold ID: {identifier}") from error


def as_object(value: object) -> dict[str, object]:
    """Reject non-object JSON at the file boundary."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("expected a JSON object with string keys")
    return cast("dict[str, object]", value)


def require_text(
    record: dict[str, object], key: str, *, allow_empty: bool = False
) -> str:
    """Require an explicit string field without coercion."""
    value = record[key]
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"{key} must be a string")
    return value


def integer(record: dict[str, object], key: str) -> int:
    """Require a JSON integer, excluding booleans."""
    value = record[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer")
    return value


def digest(raw: bytes) -> str:
    """Hash exact bytes with SHA-256."""
    return hashlib.sha256(raw).hexdigest()


def template_fields(template: str) -> set[str]:
    """Allow simple named slots only, without format expressions or escaped braces."""
    fields = set()
    has_literal_words = False
    for literal, field, specification, conversion in Formatter().parse(template):
        has_literal_words |= re.search(r"[^\W\d_]{2,}", literal) is not None
        if "{" in literal or "}" in literal:
            raise ValueError("escaped template braces are not supported")
        if field is None:
            continue
        if not re.fullmatch(r"[a-z][a-z0-9_]*", field) or specification or conversion:
            raise ValueError("only plain {slot_name} placeholders are allowed")
        fields.add(field)
    if not has_literal_words:
        raise ValueError("template must retain fixed literal words")
    return fields


def parse_slot(value: object) -> Slot:
    """Validate slot labels and bounds; URL references have a dedicated guard."""
    specification = as_object(value)
    kind = require_text(specification, "type")
    maximum = integer(specification, "max_words")
    number = specification.get("number", "any")
    if kind not in {"noun_phrase", "number", "unit", "reference"} or maximum < 1:
        raise ValueError("slot type or max_words is invalid")
    if number not in {"singular", "plural", "any"}:
        raise ValueError("slot number must be singular, plural, or any")
    return Slot(kind, maximum, cast("str", number))


def validate_value(name: str, value: object, slot: Slot) -> None:
    """Apply lexical limits and a heuristic guard for common clause escapes."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"slot {name} must be a nonempty trimmed string")
    if any(
        unicodedata.category(char).startswith("C")
        or unicodedata.category(char) in {"Zl", "Zp"}
        for char in value
    ):
        raise ValueError(f"slot {name} contains a control or format character")
    if slot.kind == "reference" and value.startswith(("http://", "https://")):
        address = urlsplit(value)
        if (
            not address.hostname
            or address.username is not None
            or address.password is not None
            or re.search(r"[\s{}<>\"`\\]", value)
            or value[-1] in ".,;:!?"
            or (
                not address.netloc.startswith("[")
                and not re.fullmatch(
                    r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", address.hostname
                )
            )
        ):
            raise ValueError(f"slot {name} requires a single URL without credentials")
        # Accessing port also validates its numeric syntax and range.
        _ = address.port
        return
    if len(value.split()) > slot.max_words or re.search(r"[{};!?:]", value):
        raise ValueError(f"slot {name} exceeds phrase limits")
    if slot.kind == "number":
        if not re.fullmatch(
            r"[+\-\u2212]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][+\-\u2212]?\d+)?%?",
            value,
        ):
            raise ValueError(f"slot {name} requires a numeric string")
        return
    if has_common_clause(value):
        raise ValueError(f"slot {name} contains a possible clause or sentence")
    first_word = value.split()[0].lower()
    incompatible = {
        "singular": {"these", "those", "many", "several", "both"},
        "plural": {"a", "an", "this", "that", "each", "every"},
        "any": set(),
    }
    if first_word in incompatible[slot.number]:
        raise ValueError(f"slot {name} has an incompatible number determiner")


def has_common_clause(value: str) -> bool:
    """Allow common scientific abbreviations without claiming a grammar parse."""
    without_abbreviations = re.sub(r"\b(?:[A-Za-z]|Fig|Figs|al|sp|nov|cf)\.", "", value)
    # Uppercase IS denotes insertion sequences; Roman I denotes types or complexes.
    return bool(
        CLAUSE.search(value)
        or re.search(r"\bis\b", value)
        or re.search(r"\.(?:\s|$)", without_abbreviations)
    )


def validate_source_metadata(source: dict[str, object]) -> None:
    """Require source identity, hashes and code-point offsets."""
    for key in ("paper_id", "doi", "title", "license", "path", "sentence"):
        require_text(source, key)
    if not 1000 <= integer(source, "year") <= 9999:
        raise ValueError("source year must have four digits")
    for key in ("sentence_sha256", "text_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", require_text(source, key)):
            raise ValueError(f"{key} must be a lowercase SHA-256 digest")
    sentence = require_text(source, "sentence")
    if digest(sentence.encode("utf-8")) != source["sentence_sha256"]:
        raise ValueError("source sentence hash mismatch")
    start, end = integer(source, "start"), integer(source, "end")
    if start < 0 or end - start != len(sentence):
        raise ValueError("source offsets do not match sentence length")


def validate_span(request: dict[str, object], draft: str) -> tuple[int, int]:
    """Require an exact, nonempty original draft span."""
    start, end = integer(request, "start"), integer(request, "end")
    if not 0 <= start < end <= len(draft):
        raise ValueError("replacement offsets are out of bounds")
    if draft[start:end] != require_text(request, "original"):
        raise ValueError("original draft span changed")
    return start, end


def read_json(path: Path) -> object:
    """Read a UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def list_records(args: argparse.Namespace, bank: Bank) -> dict[str, object]:
    """Return one bounded page after filters, with usable slot constraints."""
    if args.limit < 1 or args.offset < 0:
        raise ValueError("limit must be positive and offset must be nonnegative")
    if any(
        value is not None and value < 1
        for value in (args.max_slots, args.max_template_words)
    ):
        raise ValueError("max-slots and max-template-words must be positive")
    matching = [
        record
        for record in bank.records.values()
        if (not args.family or record.family == args.family)
        and (not args.section or record.section == args.section)
        and record.identifier not in args.exclude
        and (args.max_slots is None or len(record.slots) <= args.max_slots)
        and (
            args.max_template_words is None
            or len(record.template.split()) <= args.max_template_words
        )
    ]
    hits: dict[str, SearchHit] = {}
    if args.query is not None:
        ranked = search_records(matching, search_terms(args.query))
        matching = [hit.record for hit in ranked]
        hits = {hit.record.identifier: hit for hit in ranked}
    records = []
    for record in matching[args.offset : args.offset + args.limit]:
        summary: dict[str, object] = {
            "id": record.identifier,
            "family": record.family,
            "section": record.section,
            "template": record.template,
            "usage_notes": record.usage_notes,
            "slots": {
                name: {
                    "type": slot.kind,
                    "max_words": slot.max_words,
                    "number": slot.number,
                }
                for name, slot in record.slots.items()
            },
            "source": {key: record.source[key] for key in ("doi", "year", "paper_id")},
        }
        if record.identifier in hits:
            hit = hits[record.identifier]
            summary["search"] = {
                "score": hit.score,
                "matched_terms": sorted(
                    {term for terms in hit.fields.values() for term in terms}
                ),
                "matched_fields": hit.fields,
            }
        records.append(summary)
    page: dict[str, object] = {
        "total": len(matching),
        "limit": args.limit,
        "offset": args.offset,
        "records": records,
    }
    if args.query is not None:
        page["query_terms"] = sorted(search_terms(args.query))
    return page


def search_records(records: list[Scaffold], terms: set[str]) -> list[SearchHit]:
    """Rank fixed-text hits before notes and source, then simpler frames."""
    hits = []
    for record in records:
        fields = {
            "fixed": " ".join(
                literal for literal, _, _, _ in Formatter().parse(record.template)
            ),
            "notes": record.usage_notes,
            "source": require_text(record.source, "sentence"),
        }
        matched = {
            name: sorted(terms & search_terms(value))
            for name, value in fields.items()
            if terms & search_terms(value)
        }
        if not matched:
            continue
        score = (
            len(matched.get("fixed", [])),
            len(matched.get("notes", [])),
            len(matched.get("source", [])),
        )
        hits.append(SearchHit(record, matched, score))
    return sorted(
        hits,
        key=lambda hit: (
            *(-count for count in hit.score),
            len(hit.record.slots),
            len(hit.record.template.split()),
            hit.record.identifier,
        ),
    )


def search_terms(text: str) -> set[str]:
    """Extract literal Unicode words; never compile user text as a pattern."""
    return {
        SEARCH_NORMALIZATION.get(word, word)
        for word in re.findall(r"[^\W\d_]+", text.casefold())
        if word not in SEARCH_STOPWORDS
    }


def run_command(args: argparse.Namespace, bank: Bank) -> object:
    """Perform one command with validated bank records."""
    match args.command:
        case "list":
            return list_records(args, bank)
        case "render":
            return render(
                lookup_scaffold(bank, args.id), as_object(read_json(args.slots))
            )
        case "apply":
            output, receipt = apply_requests(
                args.draft.read_bytes().decode("utf-8"),
                read_json(args.requests),
                bank,
            )
            destinations = [args.output.resolve(), args.receipt.resolve()]
            inputs = {
                args.bank.resolve(),
                args.draft.resolve(),
                args.requests.resolve(),
            }
            if len(set(destinations)) != 2 or any(
                path in inputs for path in destinations
            ):
                raise ValueError(
                    "output and receipt must be distinct from each other and inputs"
                )
            args.output.write_bytes(output.encode("utf-8"))
            args.receipt.write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return {
                "ok": True,
                "output": str(args.output),
                "receipt": str(args.receipt),
            }
        case "check":
            receipt = as_object(read_json(args.receipt))
            checked = check_receipt(
                args.draft.read_bytes().decode("utf-8"), receipt, bank
            )
            checked.update(check_review(as_object(read_json(args.review)), receipt))
            return checked
        case "audit-bank":
            if args.corpus_root:
                verify_sources(bank, args.corpus_root)
            return {
                "ok": True,
                "records": len(bank.records),
                "bank_sha256": bank.sha256,
                "source_files_verified": args.corpus_root is not None,
            }
        case "export-mcp":
            if args.output.resolve() == args.bank.resolve():
                raise ValueError("export output must differ from the canonical bank")
            args.output.write_text(export_mcp(bank), encoding="utf-8")
            return {
                "ok": True,
                "records": len(bank.records),
                "output": str(args.output),
            }
    raise ValueError("unknown command")


def parse_args() -> argparse.Namespace:
    """Define the file-oriented scaffold interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bank", type=Path, required=True, help="Canonical accepted JSONL bank"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="Select alternate frames")
    listing.add_argument("--family", help="Exact rhetorical family")
    listing.add_argument("--section", help="Exact source section")
    listing.add_argument(
        "--query", help="OR lexical search across fixed text, notes and source"
    )
    listing.add_argument("--max-slots", type=int, help="Maximum number of named slots")
    listing.add_argument(
        "--max-template-words",
        type=int,
        help="Maximum whitespace-separated template words (each slot counts as one)",
    )
    listing.add_argument(
        "--limit", type=int, default=20, help="Maximum frames per page (default: 20)"
    )
    listing.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip this many matching frames (default: 0)",
    )
    listing.add_argument(
        "--exclude", action="append", default=[], help="Omit an ID; repeatable"
    )
    rendering = commands.add_parser("render", help="Render one frame to stdout")
    rendering.add_argument("--id", required=True, help="Canonical scaffold ID")
    rendering.add_argument(
        "--slots", type=Path, required=True, help="JSON object of string values"
    )
    applying = commands.add_parser("apply", help="Apply reviewed replacements")
    for name in ("draft", "requests", "output", "receipt"):
        applying.add_argument(
            f"--{name}", type=Path, required=True, help=f"{name} file path"
        )
    checking = commands.add_parser("check", help="Verify final draft and receipt")
    checking.add_argument(
        "--draft", type=Path, required=True, help="Final Markdown/plain-text file"
    )
    checking.add_argument(
        "--receipt", type=Path, required=True, help="Apply receipt JSON file"
    )
    checking.add_argument(
        "--review", type=Path, required=True, help="Initial and final review JSON file"
    )
    auditing = commands.add_parser(
        "audit-bank", help="Verify bank and optional source files"
    )
    auditing.add_argument(
        "--corpus-root", type=Path, help="Root containing source.path files"
    )
    exporting = commands.add_parser("export-mcp", help="Generate upstream MCP JSONL")
    exporting.add_argument(
        "--output", type=Path, required=True, help="Generated JSONL path"
    )
    return parser.parse_args()


def main() -> int:
    """Print evidence on stdout and validation errors on stderr."""
    logging.basicConfig(format="%(levelname)s: %(message)s")
    args = parse_args()
    try:
        bank = load_bank(args.bank)
        output = run_command(args, bank)
    except (OSError, ValueError, KeyError, TypeError) as error:
        LOGGER.error("%s", error)
        return 1
    print(output if isinstance(output, str) else json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
