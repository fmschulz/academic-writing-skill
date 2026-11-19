# academic-writing-skill

An agent skill that revises academic prose for clarity without changing its
claims. It works as a focused edit by default, with optional source-derived
sentence frames, local stylometry and a scored rewrite loop. The skill follows
the `SKILL.md` format of Claude Code and Codex.

## What it does

- **Focused edit.** Locks every number, citation and claim, then fixes unclear
  actors, undefined terms and buried points, sentence by sentence.
- **Sentence frames.** `data/scaffolds.jsonl` holds 1,305 sentence frames taken
  from open-access articles; an agent fills only their named slots, and
  `scripts/scaffolds.py` checks that every fixed word survived.
- **AI-tell and style checks.** `scripts/stylometry.py` reports phrase-level tells
  and style metrics as ceilings, not targets.
- **Research pages.** A workflow for scientific reports and results summaries:
  concise prose, limits beside the results they qualify, independent review.

## Install

Clone it into your agent's skills folder, next to its companion
[stop-slop-skill](https://github.com/fmschulz/stop-slop-skill), which owns the
sentence-clarity rules this skill links to:

```bash
git clone https://github.com/fmschulz/academic-writing-skill ~/.claude/skills/academic-writing
git clone https://github.com/fmschulz/stop-slop-skill ~/.claude/skills/stop-slop
```

Then ask the agent to "use the academic-writing skill" on a passage or file.

## Run the scripts

The scripts need [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer.

```bash
uv run --no-project python scripts/stylometry.py tells draft.md            # AI tells and counts
uv run --no-project python scripts/scaffolds.py --bank data/scaffolds.jsonl \
  list --query suggest --limit 5                                           # find frames
uv run --no-project python scripts/stylometry.py selftest                  # self-checks
```

## Contents

| Path | Content |
|---|---|
| `SKILL.md` | the skill: priorities, focused edit, research pages, scored loop |
| `references/` | AI tells, the scaffold pass, the scored loop, reviewer roles, style guide |
| `scripts/` | `scaffolds.py` (frames), `stylometry.py` (tells, metrics), `profile_corpus.py` (style profiles), `build_scaffolds.py` (frame extraction), optional rewrite backends |
| `templates/` | rewrite brief and scorecard of the scored loop |
| `data/` | the frame bank and its provenance |
| `tests/` | unit tests |

## Tests

```bash
uv run --no-project --with pytest --with "spacy==3.8.18" \
  --with "en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" \
  python -m pytest -q tests
```

## Data sources

The frames come from 482 open-access articles in PubMed Central: 1,257 frames
from articles under CC BY 4.0 and 48 under CC0. Each record in
`data/scaffolds.jsonl` names its source article (DOI, authors, title, year) and
its licence; `data/provenance.json` records the collection and review. The bank
can be exported to the format of the
[writing-scaffold](https://github.com/ampdot-io/writing-scaffold) MCP server
(`scaffolds.py export-mcp`).
