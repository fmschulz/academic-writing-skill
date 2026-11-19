#!/usr/bin/env python3
"""Optional CBORG rewrite backend for academic-writing. Standard library only.

Routes the editor step through an OpenAI-compatible CBORG endpoint so Gemini can
produce a candidate rewrite. The result is never trusted blindly: re-score it
with stylometry.py and run the meaning-fidelity check before using it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib import error, request

DEFAULT_BASE_URL = "https://api.cborg.lbl.gov"
DEFAULT_SECRETS = Path.home() / ".secrets" / "apis.txt"

SYSTEM = (
    "Rewrite one passage of academic prose. Hard rules, in priority order: "
    "(1) Preserve every number, unit, threshold, citation, equation, quoted term, "
    "source label, and named entity from the source exactly; if unsure, keep the "
    "original clause. (2) Invent nothing: no new facts, numbers, labels, or citations. "
    "(3) Remove empty praise and filler. Review flagged words and grammatical "
    "constructions in context: keep literal terms, useful transitions, and "
    "clauses that carry meaning. Preserve links between sentences and paragraphs, "
    "use one term for each concept, and keep short sentences that state findings "
    "or changes in the argument. These take priority over style metrics. "
    "(4) Use a restrained academic register, "
    "vary sentence length, keep calibrated uncertainty, and preserve section "
    "conventions. If the brief specifies FS-writing flavor, borrow the requested "
    "cadence and sentence jobs without copying corpus phrasing or claiming exact "
    "author voice. (5) Stay within the requested length range. Output only the "
    "rewritten passage as continuous prose: no preamble, commentary, or change list."
)


def resolve_api_key(secrets_file: Path) -> str:
    key = os.environ.get("CBORG_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    if secrets_file.exists():
        for line in secrets_file.read_text().splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                name, val = s.split("=", 1)
                if name.strip() in ("CBORG_API_KEY", "OPENAI_API_KEY"):
                    return val.strip().strip("\"'")
    sys.exit("error: CBORG_API_KEY not in environment or ~/.secrets/apis.txt")


def resolve_base_url() -> str:
    return (os.environ.get("CBORG_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
            or DEFAULT_BASE_URL).rstrip("/")


def _request(url: str, key: str, timeout: int, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = request.Request(
        url, data=data, method="POST" if payload is not None else "GET",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        sys.exit(f"error: CBORG {exc.code}: {body}")
    except (error.URLError, TimeoutError, OSError) as exc:
        sys.exit(f"error: CBORG unreachable ({exc}). Rewrite inline instead.")


def list_models(args: argparse.Namespace) -> None:
    key, base = resolve_api_key(Path(args.secrets)), resolve_base_url()
    data = _request(f"{base}/v1/models", key, args.timeout)
    ids = sorted(m.get("id", "") for m in data.get("data", []))
    if args.filter:
        ids = [i for i in ids if args.filter.lower() in i.lower()]
    print("\n".join(i for i in ids if i))


def rewrite(args: argparse.Namespace) -> None:
    model = args.model.lower()
    if any(x in model for x in ("claude", "opus", "sonnet", "haiku")):
        sys.exit(f"error: '{args.model}' is a Claude model. Use scripts/claude_rewrite.sh.")
    if not model.startswith("gemini"):
        sys.exit(f"error: '{args.model}' is not a Gemini model. Run list-models --filter gemini.")
    brief = sys.stdin.read() if args.prompt_file == "-" else Path(args.prompt_file).read_text()
    if not brief.strip():
        sys.exit("error: empty prompt/brief")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": brief}]
    payload = {"model": args.model, "messages": messages,
               "temperature": args.temperature, "max_tokens": args.max_tokens}
    if args.dry_run:
        json.dump({"base_url": resolve_base_url(), "payload": payload}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return
    key, base = resolve_api_key(Path(args.secrets)), resolve_base_url()
    raw = _request(f"{base}/v1/chat/completions", key, args.timeout, payload)
    try:
        choice = raw["choices"][0]
        content = choice["message"].get("content")
    except (KeyError, IndexError, TypeError):
        sys.exit(f"error: unexpected CBORG response: {json.dumps(raw)[:300]}")
    if isinstance(content, list):
        content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
    text = (content or "").strip()
    if not text:
        sys.exit(f"error: CBORG returned empty content (finish_reason="
                 f"{choice.get('finish_reason')}, usage={raw.get('usage', {})}). "
                 "Raise --max-tokens and retry.")
    sys.stdout.write(text + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Optional CBORG rewrite backend for academic-writing")
    ap.add_argument("--secrets", default=str(DEFAULT_SECRETS))
    ap.add_argument("--timeout", type=int, default=300)
    sub = ap.add_subparsers(dest="cmd", required=True)

    lm = sub.add_parser("list-models", help="list CBORG model IDs")
    lm.add_argument("--filter", default="", help="substring filter, e.g. gemini")
    lm.set_defaults(func=list_models)

    rw = sub.add_parser("rewrite", help="rewrite a passage via CBORG")
    rw.add_argument("--model", default="gemini-3.1-pro",
                    help="Gemini model id on CBORG; confirm with list-models")
    rw.add_argument("--prompt-file", required=True, help="filled rewrite brief, or - for stdin")
    rw.add_argument("--temperature", type=float, default=0.7)
    rw.add_argument("--max-tokens", type=int, default=8000)
    rw.add_argument("--dry-run", action="store_true", help="print the request, do not call")
    rw.set_defaults(func=rewrite)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
