# Next sessions

Planned work sessions with Claude, in order. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions.

## How a session works

1. Start from this file, the [Readme](Readme.md) and the latest log in [`claude-logs/`](claude-logs/).
2. Work in a dedicated worktree and branch; one PR per session. During the session, Claude never commits or pushes without explicit permission.
3. End by updating the Readme (checkboxes, decisions) and this file (remove the done session, adjust the plan).
4. Claude writes the session log in `claude-logs/YYYYMMDDHHmm-session-name.md`.
5. The user exports the transcript with `/export claude-logs/transcripts/YYYYMMDDHHmm-session-name.txt` (same name as the log).
6. Claude commits the session, pushes the branch, opens the PR, writes the PR link in the log and pushes again. This end-of-session commit and push is agreed once and for all, so the next session starts clean.

## Reminders

- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.

## Plan

1. **MVP scope** — which tables, creatures and events, and the fallback for the rest. Also decide the forest map of #41 (size, entering and leaving), left open by the [town map](design/town-map.md#open) design.
2. **Project setup** — Milestone 4 except the Python bootstrap: `.tool-versions` (blocks running Python in the repo), minimal `CLAUDE.md`, `.claude/settings.json`.
3. **GitHub planning** — milestones, labels and issues from the roadmap; decide whether issues or the Readme are the source of truth.
4. **Review engine tasks** against the design, then start the engine in dependency order, bootstrapping the Python project with common defaults.
5. **Rules cleanup** — Milestone 3, as the engine needs each table. Fix the Markdown against the original PDFs in `origin_rules/`; no format conversion yet.
