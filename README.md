<!-- Banner -->
<h1 align="center">HESO</h1>
<p align="center"><strong>Hermes · Sisyphus · Orchestrator</strong></p>
<p align="center">An autonomous AI system that reviews, fixes, and evolves your codebase around the clock —<br>one mind that thinks and judges, one worker that builds, looping forever while you just read a short message.</p>

<p align="center">
  <img alt="status" src="https://img.shields.io/badge/status-alpha-orange">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
  <img alt="stack" src="https://img.shields.io/badge/stack-SQLite%20%2B%20tmux%20%2B%20cron-555">
</p>

---

## Overview

Most "AI code review" loops fail the same way: you ask a worker agent to review its own work, and it always says *"looks fine."* It also tends to **report** problems endlessly instead of **fixing** them.

HESO fixes this with a strict separation of duties:

- **Hermes** — the *mind*. One identity playing three roles: Project Manager, Product Owner, and QA/Reviewer. Hermes does **all** the thinking, judging, reviewing, committing, and idea generation.
- **Sisyphus** — the *hands*. A worker agent that **only executes** the single, clear task Hermes hands it, then reports back a summary.

The worker never reviews itself, never sets priorities, and never decides what to do. That separation is the whole trick.

Designed to run **800–1000 cycles a day on a single machine**, HESO is deliberately lightweight: **no vector database, no embeddings, no GPU tax** — just SQLite, tmux, and cron.

---

## Features

- **Self-healing loop** — finds issues, fixes them, commits, and moves on. No human in the inner loop.
- **Never sleeps** — driven by cron; progress compounds while you do anything else.
- **Generates its own ideas** — built-in brainstorming proposes features, safety and performance work, not just bug fixes.
- **Three memory layers** — user intention, product analysis, and a free-association keyword pool.
- **You only read Telegram** — each cycle ends with one short, plain-language report.
- **Featherweight** — plain SQLite + tmux + cron. Runs anywhere, no special hardware.
- **Injection-safe by design** — cron prompts are pure text with zero embedded code, so they pass agent safety filters.

---

## How It Works

Every cron cycle, Hermes runs a fixed sequence:

1. **Intention gate** *(first run only)* — if there's no `user-intention.md`, Hermes asks you (via Telegram) for the project's direction and boundaries, then writes it down. It never asks again unless you say so.
2. **Observe** — read the worker's last output, the TODO board, and the actual code.
3. **Verify** — did the last fix really land and make sense? Mark it `complete`, or send it back to `pending`.
4. **Review** — if nothing is pending, hunt for new issues; log ideas, UX notes, and pain points.
5. **Brainstorm** — pull 5 random keywords, free-associate 50 new ones (deliberately off-topic), feed them back into the pool.
6. **Commit / push** — Hermes commits verified work itself, directly in the terminal (the worker's session can die mid-commit).
7. **Dispatch** — pick the top-priority task, attach 3 random keywords as "other thoughts," and hand it to Sisyphus.
8. **Notify** — send you one short Telegram report.

Then the loop repeats. *One must imagine Sisyphus happy — and now, productive.*

---

## Architecture

```
                ┌─────────────────────────────────────────┐
   ⏰ cron ───▶ │  HERMES  (PM + Product Owner + QA)        │
                │  observe → verify → review → brainstorm   │
                │  → commit → dispatch → notify             │
                └───────────┬───────────────────▲───────────┘
                            │ set-buffer + ULW   │ DONE #id + summary
                            ▼                    │
                ┌───────────────────────────────┴───────────┐
                │  SISYPHUS  (worker — fix only)             │
                └───────────────────────────────────────────┘

   Memory (single SQLite file, no vector):
     todo · idea · user_experience · painpoint · concept · keyword_pool
   Plus one plain file: user-intention.md  (changed only after asking you)
```

### Three memory layers

| Layer | What it holds | Governance |
|---|---|---|
| **User Intention** | Your direction & boundaries (`user-intention.md`) | Set once; changed **only after asking you** |
| **Product Analysis** | Ideas, UX observations, pain points (DB tables) | Grown by Hermes every cycle |
| **Free-Association Pool** | A growing keyword pool, capped at 1000 | Deliberately unconstrained, off-topic by design |

---

## Quick Start

> **Prerequisites:** a worker agent running in a `tmux` session (e.g. OpenCode), `python3`, `sqlite3`, `cron`, and a Telegram bot token + chat id.

### 1. One-time setup *(not via cron — avoids safety filters)*

Have your orchestrator agent write two files into a **fixed folder** it will remember, e.g. `~/.heso/`:

- `~/.heso/progress.db` — created from the schema (see [`SPEC.md`](SPEC.md))
- `~/.heso/loop_routine.py` — the keyword-pool + DB helper routine

Seed the brainstorm pool with 20 general keywords:

```bash
python3 ~/.heso/loop_routine.py init
```

### 2. Define the cron prompt

Drop the **plain-text** Hermes prompt (see [`SPEC.md`](SPEC.md)) into your scheduler. It contains **no code** — it only references the routine in the fixed folder, so it passes agent injection filters.

### 3. Schedule it

Point your cron job at the prompt on whatever interval you like (e.g. every few minutes). On first run, Hermes will ask you — once — for the project's intention. After that, it runs on its own.

> Full database schema, the Python routine, the Hermes cron prompt, and the Sisyphus task format all live in **[`SPEC.md`](SPEC.md)**.

---

## Roadmap

### Near-term · v1.x — *Solid & visible*
- **Risk / approval gates** — high-risk changes (schema, auth) need a one-tap Telegram approval before dispatch.
- **Web dashboard** — one screen for all jobs, the TODO board, and commit history.
- **Cost & GPU telemetry** — track resource use per cycle to keep loops cheap.

### Mid-term · v2 — *Scale & adapt*
- **Multi-worker** — one Hermes directing many Sisyphus workers across projects and modules.
- **Pluggable workers** — swap in Claude Code, Aider, or any agent behind the same interface.
- **Self-evolving prompts** — Hermes tunes how it dispatches based on what gets the best results.

### Long-term — *Cross-pollinate*
- **Cross-project idea transfer** — a concept sparked in one project can inspire another.
- **Optional vector recall** — opt-in semantic memory for those with GPU headroom (off by default).

---

## Design Principles

- **Separation of duties** — the reviewer is never the worker.
- **Boring on purpose** — no vector DB, no embeddings; lightweight enough for 1000 loops/day.
- **Plain-text prompts** — zero embedded code in scheduled prompts, to stay injection-safe.
- **Human stays in command** — intention is yours; the system asks before changing direction.
- **Fix, don't nag** — the loop resolves issues rather than re-reporting them.

---

## Contributing

Issues and pull requests are welcome. If you're proposing a larger change, open an issue first to discuss the direction. Please keep the core lightweight and the scheduled prompts code-free.

---

## License

MIT — see [`LICENSE`](LICENSE).

---

<p align="center"><sub>HESO — one mind, one worker, endless progress.</sub></p>
