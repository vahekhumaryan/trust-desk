# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

This repo is the workspace for **Hack-Nation's 6th Global AI Hackathon** (MIT Sloan AI Club), July 18–19, 2026, competed from the Yerevan hub.

- **Team: solo** (Vahe). Claude Code is the de-facto co-founder — bias toward doing, not asking.
- **Hard deadline: Sunday, July 19, 5:00 PM Yerevan time (9:00 AM ET).** ~21-hour build window from Saturday 8:15 PM.
- Challenge is sponsor-defined and revealed Saturday ~8:05 PM Yerevan; once known, it will be documented in `docs/challenge.md` — read that first.
- Deliverable that wins: a **working end-to-end demo + demo video** and a clear pitch. 200+ judges review 400+ submissions; polish and a sharp narrative matter as much as the tech. Top 3 per challenge give a 3-min pitch on July 25.

## Working principles (hackathon mode)

- **Time is the scarcest resource.** Prefer the fastest path to a working vertical slice, then iterate. No speculative abstractions, no test suites beyond smoke tests unless something keeps breaking.
- **Demo-first prioritization.** Every hour spent must be visible in the demo or the pitch. Cut anything that isn't.
- Ship checkpoints: commit early and often to `main`; no branching ceremony needed solo.
- When a sponsor API is part of the challenge (past editions: ElevenLabs, AkashX), using it prominently is likely scored — integrate it visibly.
- Keep a running `docs/pitch.md` with the story: problem → solution → why it's advanced/novel → demo script. Update it as features land.
- Record demo-video material as features complete (ffmpeg is available for screen-capture post-processing) — don't leave the video for the last hour.

## Layout

- `docs/` — challenge brief, pitch notes, submission requirements
- `assets/` — logos, screenshots, demo video clips
- Project code lives at the repo root or in a subdirectory named after the project (created once the challenge is known)

## Environment

- macOS, Node v24 + npm 11, git + `gh` (authed as `vahekhumaryan`), Docker, ffmpeg 8
- Python is the system 3.9 — **do not use it for the project**; if Python is needed, install `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`) and pin 3.12+ via `uv python install 3.12`
- No package manager lockfile conventions yet — established once the stack is chosen; update this file with build/run commands at that point

## Build & run commands

_To be filled in as soon as the stack is chosen after challenge reveal. Keep this section current — it is the first thing a fresh session reads._
