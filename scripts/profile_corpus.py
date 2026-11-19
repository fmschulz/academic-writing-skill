#!/usr/bin/env python3
"""Build an academic-writing profile and skeleton bank. Standard library only.

Usage:
  python profile_corpus.py --corpus PATH [--out DIR] [--max-skeletons 40]
  python profile_corpus.py --fallback [--flavor neutral|fs-writing]
  python profile_corpus.py --corpus PATH --flavor fs-writing --out DIR [--roles R]
  python profile_corpus.py --selftest

Outputs:
  fingerprint.json  target metric bands, medians, sample sizes, and tolerance
  skeletons.json    sentence-shape exemplars and transition pools
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stylometry as st  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.normpath(os.path.join(HERE, "..", "cache"))
MIN_DOC_WORDS = 150
MIN_DOCS_FOR_BANDS = 8
FS_DEFAULT_ROLES = frozenset({"first", "second", "last"})
METRIC_KEYS = list(st.DEFAULT_BANDS.keys())

FS_FLAVOR_BANDS = {
    **st.DEFAULT_BANDS,
    "mean_sent_len": [23, 27],
    "median_sent_len": [20, 25],
    "p90_sent_len": [38, 45],
    "max_sent_len": [55, 120],
    "burstiness": [0.45, 1.0],
    "fk_grade": [15, 18],
    "mean_word_len": [5.4, 5.9],
    "syll_per_word": [1.9, 2.05],
    "we_per_1k": [4, 8],
    "passive_ratio": [0.33, 0.47],
    "hedge_per_1k": [3, 6],
    "booster_per_1k": [0.5, 1.5],
    "transition_per_1k": [2, 6],
    "semicolon_per_1k": [0, 4],
    "emdash_per_1k": [0, 1],
    "paren_per_1k": [20, 45],
    "colon_per_1k": [3, 12],
    "numbers_per_1k": [40, 90],
}

SHAPE_TESTS = [
    ("context_frame", re.compile(r"^[A-Z][\w-]+(\s+\w+){0,8}\s+(is|are|has|have|shapes|affects|raises)\b")),
    ("gap", re.compile(
        r"^(despite|although|while|yet)\b.*\b(remain|remains|unclear|unresolved|"
        r"underexamined|contested|limited)\b", re.I)),
    ("pivot", re.compile(
        r"\b(here,?\s+we|in this (article|study|analysis|paper)|we\s+"
        r"(analy[sz]e|estimate|compare|test|argue|show|report|present|evaluate))\b", re.I)),
    ("evidence", re.compile(
        r"\b(results?|findings?|analysis|evidence|model|estimate|comparison)\b.*\b"
        r"(show|shows|indicate|indicates|suggest|suggests|support|supports|reveal|reveals)\b", re.I)),
    ("interpretation", re.compile(
        r",\s+(indicating|suggesting|implying|consistent with)\b|\bis consistent with\b", re.I)),
    ("synthesis", re.compile(
        r"^(together|overall|collectively|in sum)\b|\b(this (finding|analysis|result|argument))"
        r"\b.*\b(clarifies|supports|limits|extends|challenges|reframes)\b", re.I)),
]
COMPOUND = re.compile(r"\b[a-z]+-[a-z]+(?:-[a-z]+)?\b")
TRANSITION_OPENERS = re.compile(
    r"^(here|together|consistent|notably|conversely|therefore|importantly|despite|"
    r"although|thus|in contrast|by contrast|overall|collectively)\b", re.I)


def read_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            if not shutil.which("pdftotext"):
                return ""
            return subprocess.run(["pdftotext", "-q", path, "-"],
                                  capture_output=True, text=True, timeout=120).stdout
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except (OSError, subprocess.SubprocessError):
        return ""
    if ext == ".xml":
        return clean_xml(raw)
    if ext in (".md", ".markdown"):
        return clean_md(raw)
    if ext == ".json":
        return clean_json(raw)
    return raw


def clean_xml(raw: str) -> str:
    raw = re.sub(r"<ref-list\b.*?</ref-list>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<(table-wrap|fig|disp-formula)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    body = re.findall(r"<(?:abstract|body)\b.*?</(?:abstract|body)>", raw, flags=re.S | re.I)
    text = " ".join(body) if body else raw
    text = re.sub(r"<xref\b.*?</xref>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_md(raw: str) -> str:
    raw = re.sub(r"```.*?```", " ", raw, flags=re.S)
    raw = re.sub(r"^\s{0,3}#.*$", " ", raw, flags=re.M)
    raw = re.sub(r"^\s*[-*+]\s+", " ", raw, flags=re.M)
    raw = re.sub(r"[`*_>#|]", " ", raw)
    raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    return re.sub(r"[ \t]+", " ", raw).strip()


def clean_json(raw: str) -> str:
    try:
        d = json.loads(raw)
    except ValueError:
        return ""
    if isinstance(d.get("text"), str):
        return re.sub(r"\s+", " ", d["text"]).strip()
    text = d.get("text") if isinstance(d.get("text"), dict) else d
    parts = []
    if isinstance(text, dict):
        if isinstance(text.get("abstract"), str):
            parts.append(text["abstract"])
        for sec in text.get("sections") or []:
            if isinstance(sec, dict):
                parts.extend(p for p in (sec.get("paragraphs") or []) if isinstance(p, str))
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def read_role(path: str) -> str | None:
    """Return the lowercase authorship role of a corpus JSON paper.

    A JSON paper without a role gives an empty string, so a role filter drops it.
    Other file types have no role concept and give None, so a filter keeps them.
    """
    file = Path(path)
    if file.suffix.lower() != ".json":
        return None
    try:
        with file.open(encoding="utf-8", errors="replace") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict):
        return ""
    return str(doc.get("role") or "").strip().lower()


def select_roles(value: str | None, flavor: str) -> set[str] | None:
    """Return the author roles to profile, or None to profile every paper.

    ``value`` is the ``--roles`` text: a comma list, or ``all``. When it is None,
    the FS flavor keeps the FS-led roles and excludes middle-author control
    papers. Any other flavor keeps every paper.
    """
    if value is None:
        return set(FS_DEFAULT_ROLES) if flavor == "fs-writing" else None
    if value.strip().lower() in ("", "all"):
        return None
    return {role.strip().lower() for role in value.split(",") if role.strip()}


def filter_by_role(paths: list[str], roles: set[str] | None) -> tuple[list[str], int]:
    """Drop corpus papers whose author role is not in ``roles``.

    Returns the kept paths and the number dropped. A ``roles`` of None keeps every
    path, and so does a file type that has no role concept.
    """
    if not roles:
        return paths, 0
    kept = []
    for path in paths:
        role = read_role(path)
        if role is None or role in roles:
            kept.append(path)
    return kept, len(paths) - len(kept)


def classify(sentence: str) -> str | None:
    for name, rx in SHAPE_TESTS:
        if rx.search(sentence):
            return name
    return None


def gather(paths: list[str], max_sk: int) -> tuple[list[dict], dict, dict]:
    vectors: list[dict] = []
    shapes: dict[str, list[str]] = {n: [] for n, _ in SHAPE_TESTS}
    openers: list[str] = []
    compounds: dict[str, int] = {}
    counts = {"profiled": 0, "skipped_short": 0, "empty": 0}
    for path in paths:
        text = read_text(path)
        if not text:
            counts["empty"] += 1
            continue
        m = st.measure(text)
        if "error" in m or m["n_words"] < MIN_DOC_WORDS:
            counts["skipped_short"] += 1
            continue
        pred = st.predictability(text)
        if "formulaicity" in pred:
            m["formulaicity"] = pred["formulaicity"]
        vectors.append(m)
        counts["profiled"] += 1
        for s in st.sentences(text):
            wc = len(s.split())
            if 6 <= wc <= 60:
                shape = classify(s)
                if shape and len(shapes[shape]) < max_sk:
                    shapes[shape].append(re.sub(r"\s+", " ", s).strip())
                if TRANSITION_OPENERS.match(s):
                    openers.append(s.split(",")[0][:40])
            for c in COMPOUND.findall(s.lower()):
                if not c[0].isdigit():
                    compounds[c] = compounds.get(c, 0) + 1
    top_compounds = [c for c, _ in sorted(compounds.items(), key=lambda kv: -kv[1])[:60]]
    bank = {
        "_note": "Exemplars are shape references, not reusable content. Replace all "
                 "content with source-supported material.",
        "shapes": shapes,
        "transition_openers": _top_unique(openers, 25),
        "hyphenated_terms": top_compounds,
    }
    return vectors, bank, counts


def _top_unique(items: list[str], n: int) -> list[str]:
    seen: dict[str, int] = {}
    for it in items:
        key = it.strip().lower()
        seen[key] = seen.get(key, 0) + 1
    return [k for k, _ in sorted(seen.items(), key=lambda kv: -kv[1])[:n]]


def neutral_skeleton_bank(max_sk: int) -> dict:
    shapes = {
        "context_frame": [
            "[Object of analysis] matters for [larger question] because [specific relation].",
            "[Question] remains central to [debate] because [condition] changes [interpretation].",
        ],
        "gap": [
            "Although [prior source] establishes [known point], [specific question] remains unresolved.",
            "Despite [available evidence], [scope condition] still limits [claim].",
        ],
        "pivot": [
            "Here, we compare [evidence A] with [evidence B] to assess [claim].",
            "In this analysis, we estimate [measure] across [scope] under [condition].",
        ],
        "evidence": [
            (
                "[Measure] in [studied object] [increased/decreased] from "
                "[value A] to [value B] under [condition]."
            ),
            (
                "[Measure] in [group A] was [higher than/equal to/lower than] in "
                "[group B] when [condition] was held constant."
            ),
        ],
        "interpretation": [
            "This pattern suggests [bounded inference], rather than [stronger claim].",
            "The result is consistent with [interpretation], but not sufficient to establish [excluded claim].",
        ],
        "synthesis": [
            "Together, these findings clarify [argument] while leaving [remaining question] open.",
            "Overall, the evidence supports [claim] within [scope].",
        ],
    }
    return {
        "_note": "Synthetic fallback skeletons. Replace every placeholder with source-supported content.",
        "flavor": "neutral",
        "shapes": {k: v[:max_sk] for k, v in shapes.items()},
        "transition_openers": [
            "here", "by contrast", "consistent with this interpretation", "however",
            "although", "together", "overall", "this pattern suggests",
        ],
        "hyphenated_terms": [
            "source-supported", "evidence-led", "claim-level", "section-specific",
            "context-dependent", "reader-facing",
        ],
    }


def fs_writing_skeleton_bank(max_sk: int) -> dict:
    shapes = {
        "context_frame": [
            "[System or object] shapes [larger process], with consequences for [specific question].",
            "[Field] increasingly relies on [approach], yet [specific relation] remains unevenly resolved.",
        ],
        "gap": [
            "Despite [known advance], [specific scope or mechanism] remains poorly understood.",
            "Although [prior evidence] has clarified [known point], [boundary condition] remains unresolved.",
        ],
        "pivot": [
            "Here, we use [approach] to investigate [object] across [scope].",
            "Here, we combine [evidence A] with [evidence B] to test [bounded claim].",
        ],
        "evidence": [
            "We identify [result] across [scope], including [source-supported qualifier].",
            "We show that [finding] varies with [condition], consistent with [bounded interpretation].",
        ],
        "interpretation": [
            "[Observation] is consistent with [interpretation], suggesting [bounded implication].",
            "Together, these results indicate [claim] while leaving [limitation] unresolved.",
        ],
        "synthesis": [
            "Together, our findings highlight [object] as [role] and provide [broader contribution].",
            "Our study establishes [bounded claim] and provides a framework for [next question].",
        ],
    }
    return {
        "_note": (
            "Synthetic FS-writing flavor skeletons. Use the cadence only; "
            "replace every placeholder with source-supported content. "
            "The voice data are not part of the public repository."
        ),
        "flavor": "fs-writing",
        "shapes": {k: v[:max_sk] for k, v in shapes.items()},
        "transition_openers": [
            "here",
            "together",
            "consistent with this",
            "despite",
            "although",
            "in contrast",
            "notably",
            "thus",
            "overall",
        ],
        "hyphenated_terms": [
            "source-supported",
            "field-scale",
            "evidence-rich",
            "hypothesis-driven",
            "context-dependent",
            "system-level",
            "section-specific",
            "claim-level",
        ],
    }


def default_skeleton_bank(max_sk: int, flavor: str) -> dict:
    if flavor == "fs-writing":
        return fs_writing_skeleton_bank(max_sk)
    return neutral_skeleton_bank(max_sk)


def fallback_bands(flavor: str) -> dict:
    return FS_FLAVOR_BANDS if flavor == "fs-writing" else st.DEFAULT_BANDS


def fallback_label(flavor: str) -> str:
    return flavor if flavor in ("neutral", "fs-writing") else "neutral"


def fingerprint(vectors: list[dict], source: str, trust_empirical: bool,
                flavor: str = "neutral") -> dict:
    use_empirical = trust_empirical and len(vectors) >= MIN_DOCS_FOR_BANDS
    bands, medians = {}, {}
    defaults = fallback_bands(flavor)
    for key in METRIC_KEYS:
        vals = [v[key] for v in vectors if key in v]
        if vals:
            medians[key] = round(st._pct(sorted(vals), 50), 3)
        if not (use_empirical and vals):
            bands[key] = defaults[key]
            continue
        lo = round(st._pct(sorted(vals), 10), 3)
        hi = round(st._pct(sorted(vals), 90), 3)
        bands[key] = defaults[key] if lo == hi else [lo, hi]
    default_label = fallback_label(flavor)
    return {
        "source": source,
        "flavor": flavor,
        "n_documents": len(vectors),
        "bands_source": "empirical_p10_p90" if use_empirical else "curated_default",
        "bands": bands,
        "medians": medians,
        "distance_tolerance": 4.0,
        "tell_tolerance": 0,
        "min_score_words": 80,
        "note": f"empirical bands need >= {MIN_DOCS_FOR_BANDS} prose documents; otherwise "
                f"curated {default_label} defaults are used.",
    }


def iter_corpus(corpus: str) -> list[str]:
    if os.path.isfile(corpus):
        return [corpus]
    out = []
    for root, _, files in os.walk(corpus):
        for f in files:
            if os.path.splitext(f)[1].lower() in (".txt", ".md", ".markdown", ".xml", ".pdf", ".json"):
                out.append(os.path.join(root, f))
    return sorted(out)


def _atomic_write_json(path: str, obj: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=True)
    os.replace(tmp, path)


def _write_role_docs(directory: str) -> tuple[list[str], str]:
    """Write test papers and return their paths.

    The JSON papers are a first-author paper, a middle-author paper and a paper
    with no role. The text file has no role concept.
    """
    paragraph = " ".join(
        [
            "We recover genomes from sediment samples collected at three depths.",
            "Samples from the deeper layer contained fewer taxa than the surface.",
            "This pattern suggests that oxygen limits richness in the deeper layer.",
            "We did not measure oxygen directly, so the explanation stays untested.",
            "Each genome passed the completeness and contamination thresholds we set.",
            "Together, these genomes narrow the next comparison to oxygen levels.",
        ]
        * 4
    )
    root = Path(directory)
    json_paths = []
    for name, role in (("first", "first"), ("middle", "middle"), ("unlabelled", "")):
        doc: dict = {"text": {"abstract": paragraph, "sections": []}}
        if role:
            doc["role"] = role
        path = root / f"{name}.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        json_paths.append(str(path))
    text_path = root / "plain.txt"
    text_path.write_text(paragraph, encoding="utf-8")
    return json_paths, str(text_path)


def selftest_run() -> bool:
    checks: list[tuple[str, bool, str]] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    neutral_fp = fingerprint([], "selftest:neutral", False, "neutral")
    fs_fp = fingerprint([], "selftest:fs-writing", False, "fs-writing")
    chk("neutral fallback uses neutral flavor",
        neutral_fp["flavor"] == "neutral"
        and neutral_fp["bands"]["mean_sent_len"] == st.DEFAULT_BANDS["mean_sent_len"])
    chk("fs-writing fallback uses fs bands",
        fs_fp["flavor"] == "fs-writing"
        and fs_fp["bands"]["mean_sent_len"] == [23, 27]
        and fs_fp["bands"]["passive_ratio"] == [0.33, 0.47])

    neutral_bank = default_skeleton_bank(40, "neutral")
    fs_bank = default_skeleton_bank(40, "fs-writing")
    chk("fallback skeleton banks carry flavor labels",
        neutral_bank["flavor"] == "neutral" and fs_bank["flavor"] == "fs-writing")
    chk("fs skeletons stay synthetic placeholders",
        all("[" in s and "]" in s
            for vals in fs_bank["shapes"].values() for s in vals),
        "expected placeholder brackets in every FS skeleton")

    same = {key: st.DEFAULT_BANDS[key][0] for key in METRIC_KEYS}
    degenerate = fingerprint([same] * MIN_DOCS_FOR_BANDS, "selftest:flat", True,
                             "fs-writing")
    chk("degenerate empirical bands fall back to selected flavor",
        degenerate["bands"]["mean_sent_len"] == [23, 27])

    with tempfile.TemporaryDirectory() as tmp:
        json_paths, text_path = _write_role_docs(tmp)
        by_default = filter_by_role(json_paths, select_roles(None, "fs-writing"))
        with_all = filter_by_role(json_paths, select_roles("all", "fs-writing"))
        neutral = filter_by_role(json_paths, select_roles(None, "neutral"))
        plain = filter_by_role([text_path], select_roles(None, "fs-writing"))
        profiled_by_default = gather(by_default[0], 40)[2]["profiled"]
    chk(
        "fs-writing corpus profiles only FS-led papers by default",
        profiled_by_default == 1 and by_default[1] == 2,
        f"profiled {profiled_by_default}, excluded {by_default[1]}",
    )
    chk(
        "roles all keeps every paper",
        len(with_all[0]) == 3 and with_all[1] == 0,
        str(with_all),
    )
    chk(
        "neutral corpus builds keep every paper",
        len(neutral[0]) == 3 and neutral[1] == 0,
        str(neutral),
    )
    chk(
        "role filter keeps files that have no role concept",
        len(plain[0]) == 1 and plain[1] == 0,
        str(plain),
    )

    ok_all = all(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        line = f"[{'PASS' if ok else 'FAIL'}] {name}"
        if detail and not ok:
            line += f"  ({detail})"
        print(line)
    print(f"\n{sum(ok for _, ok, _ in checks)}/{len(checks)} checks passed")
    return ok_all


def main() -> None:
    ap = argparse.ArgumentParser(description="Build an academic-writing profile and skeleton bank")
    ap.add_argument("--corpus", help="file or directory of academic prose")
    ap.add_argument("--fallback", action="store_true",
                    help="seed from bundled defaults")
    ap.add_argument(
        "--flavor",
        choices=("neutral", "fs-writing"),
        default="neutral",
        help="style flavor; neutral is the default",
    )
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--max-skeletons", type=int, default=40)
    ap.add_argument(
        "--roles",
        help="author roles to profile from corpus JSON papers (first,second,middle,"
        "last) or 'all'. The fs-writing flavor defaults to first,second,last, which "
        "excludes middle-author control papers; other flavors default to all",
    )
    ap.add_argument("--selftest", action="store_true", help="run bundled self-checks")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(0 if selftest_run() else 1)
    if args.roles is not None and not args.corpus:
        ap.error("--roles applies only with --corpus")
    if (
        args.flavor != "neutral"
        and Path(args.out).resolve() == Path(DEFAULT_OUT).resolve()
    ):
        ap.error("non-neutral flavors must use --out, e.g. --out cache/fs-writing")

    trust_empirical = False
    fallback_mode = False
    if args.corpus:
        paths = iter_corpus(args.corpus)
        source = f"corpus:{os.path.abspath(args.corpus)}"
        trust_empirical = True
        flavor = args.flavor if args.flavor != "neutral" else "user-supplied"
    elif args.fallback:
        paths = []
        flavor = args.flavor
        source = f"fallback:curated {flavor} defaults"
        fallback_mode = True
    else:
        ap.error("give --corpus PATH or --fallback")

    if not fallback_mode and not paths:
        ap.error(f"no readable files found for source {source}")
    if fallback_mode:
        vectors = []
        bank = default_skeleton_bank(args.max_skeletons, flavor)
        counts = {"profiled": 0, "skipped_role": 0, "skipped_short": 0, "empty": 0}
    else:
        roles = select_roles(args.roles, args.flavor)
        kept_paths, role_excluded = filter_by_role(paths, roles)
        vectors, bank, counts = gather(kept_paths, args.max_skeletons)
        counts["skipped_role"] = role_excluded
    if not vectors and not fallback_mode:
        print(f"WARNING: no document reached {MIN_DOC_WORDS} words; using default bands.",
              file=sys.stderr)
    fp = fingerprint(vectors, source, trust_empirical, flavor)
    if args.corpus:
        fp["roles_included"] = sorted(roles) if roles else "all"
    n_sk = sum(len(v) for v in bank["shapes"].values())

    os.makedirs(args.out, exist_ok=True)
    _atomic_write_json(os.path.join(args.out, "fingerprint.json"), fp)
    _atomic_write_json(os.path.join(args.out, "skeletons.json"), bank)

    print(f"source: {source}")
    print(f"flavor: {flavor}")
    if args.corpus:
        print(f"roles included: {fp['roles_included']}")
    print(
        f"documents profiled: {counts['profiled']}  (files seen: {len(paths)}; "
        f"role-excluded: {counts['skipped_role']}; "
        f"too-short: {counts['skipped_short']}; empty: {counts['empty']})"
    )
    print(f"skeleton exemplars: {n_sk}  across {sum(1 for v in bank['shapes'].values() if v)} shapes")
    print(f"hyphenated terms: {len(bank['hyphenated_terms'])}")
    print(f"wrote {os.path.join(args.out, 'fingerprint.json')}")
    print(f"wrote {os.path.join(args.out, 'skeletons.json')}")


if __name__ == "__main__":
    main()
