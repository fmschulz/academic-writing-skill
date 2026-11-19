# Rewrite Backends

External rewrite backends are optional candidate generators. They do not replace
the local score and fidelity checks.

## Hard Rule

Every external output is a candidate, not the final answer. Re-score it with
`scripts/stylometry.py`, run Lane D meaning fidelity, and keep it only when it
improves the draft without changing facts.

## Gemini Through CBORG

```bash
cd /path/to/academic-writing-skill
uv run --no-project scripts/cborg_rewrite.py list-models --filter gemini
uv run --no-project scripts/cborg_rewrite.py rewrite --prompt-file /abs/path/rewrite-brief.md --model gemini-3.1-pro
```

Use `--dry-run` to inspect the request without making a network call.

Gemini reasoning models may return empty content if `--max-tokens` is too low.
Use a generous budget for paragraph-scale rewrites.

## Claude Through Native CLI

```bash
cd /path/to/academic-writing-skill
scripts/claude_rewrite.sh /abs/path/rewrite-brief.md
scripts/claude_rewrite.sh /abs/path/rewrite-brief.md opus
```

Claude models should go through `claude -p`, not CBORG.

## Candidate Selection

For each candidate, record:

- scorer output;
- fact-preservation check;
- length change;
- remaining hard tells;
- reason selected or rejected.

Prefer the candidate that preserves meaning and reduces the most severe issues,
not the one with the lowest score at the cost of precision.
