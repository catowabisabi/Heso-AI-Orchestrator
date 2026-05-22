# HESO Skill — Hermes Sisyphus Orchestrator

> An autonomous AI system that reviews, fixes, and evolves your codebase around the clock.

## Overview

HESO (Hermes · Sisyphus · Orchestrator) fixes the self-review problem by separating duties:
- **Hermes** — the mind (PM + Product Owner + QA/Reviewer). Does ALL thinking, judging, reviewing, committing.
- **Sisyphus** — the hands. Worker that only executes the single task Hermes dispatches.

## Quick Start

### Prerequisites
- Worker agent in tmux session (e.g. OpenCode)
- Python 3, sqlite3, cron
- Telegram bot token + chat id

### Setup

1. Create the autoloop folder:
```bash
mkdir -p ~/.hermes/autoloop/
```

2. Create `progress.db` with the schema:
```bash
sqlite3 ~/.hermes/autoloop/progress.db < schema.sql
```

3. Write `loop_routine.py` to `~/.hermes/autoloop/loop_routine.py`

4. Seed the keyword pool:
```bash
python3 ~/.hermes/autoloop/loop_routine.py init
```

### Cron Prompt

Schedule this pure-text prompt (no code embedded) to run on your interval:

```
你係 Hermes。你同時係呢三個身份，全部都係你：Project Manager + Product Owner + QA / Reviewer。
Sisyphus 係 session 入面嘅 Worker，淨係執行你派嘅任務...

[See full prompt in hermes-autoloop-spec.md]
```

## Architecture

```
cron ──▶ Hermes (PM + PO + QA)
              │ observe → verify → review → brainstorm
              │ → commit → dispatch → notify
              ▼
         Sisyphus (worker — fix only)
              │ DONE #id + summary
              ▼
         Telegram (user report)
```

## Database Schema

See `hermes-autoloop-spec.md` for full schema with tables:
- `todo` — new→pending→complete
- `idea` — feature/safety/performance
- `user_experience` — UX observations
- `painpoint` — pain point analysis
- `concept` — brainstorm concepts
- `keyword_pool` — keyword brainstorms (≤1000)

Plus one independent file: `user-intention.md`

## Files

- `hermes-autoloop-spec.md` — Complete specification v1
- `heso-overview.html` — Visual overview page
- `hermes-sisyphus-skill.html` — Skill prompt with flow diagrams
- `hermes-autoloop-flow.html` — Flow diagrams
- `loop_routine.py` — Keyword pool + DB helper routine
- `progress.db` — SQLite database

## Design Principles

- Separation of duties — the reviewer is never the worker
- Featherweight — SQLite + tmux + cron only
- Injection-safe — cron prompts are pure text, zero embedded code
- Human stays in command — intention is yours; system asks before changing direction
- Fix, don't nag — loop resolves issues rather than re-reporting them

## License

MIT