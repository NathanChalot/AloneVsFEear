# Repo tour and roadmap

- Date: 2026-10-27
- Session ID: dc85721c-ddf1-41c7-ae09-e5db77429b86
- Branch / PR: `docs/readme-roadmap` / not committed yet
- Transcript: [transcripts/202610271900-repo-tour-and-roadmap.txt](transcripts/202610271900-repo-tour-and-roadmap.txt)

## Goal

Tour the repository, assess the rules extraction, and set the project up for future sessions with Claude.

## Done

- Audited the extraction of `gameRules/extractor/output.md` into split files: content coverage is complete (only credits, page headers and back cover dropped). Character sheet, town map and pregenerated characters are images in the PDF and were never captured by OCR.
- Found structural OCR damage in ~15 rolling tables (missing/misplaced roll numbers, flattened nested tables, swapped columns, merged rows, body text parsed as headings). Listed in Readme Milestone 2.
- Found `.tool-versions` pins Python 3.14.5, which is not installed (3.14.2 is).
- Read the core rules (how the game works, game overview, encumbrance, main rules, combat, monsters).
- Rewrote the Readme: description, MVP goal, decisions, issue-sized roadmap (D1–D8 decisions, Milestones 1–4, E1–E13 engine tasks), working-with-Claude section.
- Created `NextSession.md` (plan for upcoming sessions) and `claude-logs/` with `transcripts/`.

## Decisions

- **Python** — strongest ecosystem for planned genAI features (local LLMs, image/video generation); already used by the extractor; ports reasonably to Ruby/DragonRuby. TypeScript (browser reuse) and Elixir (small ML ecosystem) considered.
- **Terminal CLI first** — fastest MVP; engine stays UI-agnostic.
- **Architecture choices are roadmap items, not up-front decisions** — content format (YAML was first proposed, then questioned: most entries mix data with unique rules), validation, tooling, saves, map layout, MVP scope, portability, genAI are D1–D8, settled when they block work, D1 via a spike.
- **CLAUDE.md written later** — only established facts at first, extended as decisions are made, so it does not steer sessions toward undecided choices.
- **MVP = one complete mission**; campaign play comes after.
- **Work in small planned sessions** — one worktree, branch and PR per session; this session acts as planner.
- **Session logs in `claude-logs/`** — short summaries for later reflection; the Readme stays the source of truth.
- **Next sessions plan in `NextSession.md`**, kept out of the Readme.
- **Full transcripts in `claude-logs/transcripts/`**, exported with `/export`, same name as the log; raw JSONL found via the session ID.
- **No commit or push without explicit permission**; worktrees are fine.

## Open questions

- Should spending XP on Skills be part of the MVP (rules allow spending mid-mission)?
- After GitHub issues exist, is the Readme or the issue tracker the source of truth?

## Next

Session 1 — Project setup (see [NextSession.md](../NextSession.md)).
