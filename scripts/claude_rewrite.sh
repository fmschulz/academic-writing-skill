#!/usr/bin/env bash
# Optional Claude rewrite backend for academic-writing, via native claude -p.
set -euo pipefail

brief_file="${1:?usage: claude_rewrite.sh BRIEF.txt [model]}"
model="${2:-}"

if [[ "$brief_file" == "-" ]]; then brief="$(cat)"; else brief="$(cat "$brief_file")"; fi
if [[ -z "${brief//[[:space:]]/}" ]]; then echo "error: empty brief" >&2; exit 1; fi

command -v claude >/dev/null 2>&1 || {
  echo "error: claude CLI not found; rewrite inline instead" >&2; exit 1; }

read -r -d '' SYS <<'EOS' || true
Rewrite one passage of academic prose. Hard rules, in priority order: (1) Preserve every number,
unit, threshold, citation, equation, quoted term, source label, and named entity from the source
exactly; if unsure, keep the original clause. (2) Invent nothing: no new facts, numbers, labels,
or citations. (3) Remove empty praise and filler. Review flagged words and grammatical
constructions in context: keep literal terms, useful transitions, and clauses that carry meaning.
Preserve links between sentences and paragraphs, use one term for each concept, and keep short
sentences that state findings or changes in the argument. These take priority over style metrics.
(4) Use a restrained academic register, vary sentence length, keep calibrated
uncertainty, and preserve section conventions. If the brief specifies FS-writing flavor, borrow
the requested cadence and sentence jobs without copying corpus phrasing or claiming exact author
voice. (5) Stay within the requested length range. Output only the rewritten passage as continuous
prose: no preamble, commentary, or change list.
EOS

args=(-p "$brief" --append-system-prompt "$SYS" --output-format text)
[[ -n "$model" ]] && args+=(--model "$model")

exec claude "${args[@]}"
