# Next sessions

Planned work sessions with Claude, in order. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions.

## How a session works

1. Start from this file, the [Readme](Readme.md) and the latest log in [`claude-logs/`](claude-logs/).
2. Work in a dedicated worktree and branch; one PR per session. Claude never commits or pushes without explicit permission.
3. End by updating the Readme (checkboxes, decisions) and this file (remove the done session, adjust the plan).
4. Claude writes the session log in `claude-logs/YYYYMMDDHHmm-session-name.md`.
5. Export the transcript with `/export claude-logs/transcripts/YYYYMMDDHHmm-session-name.txt` (same name as the log).

## Plan

1. **Combat design** — Milestone 2: attack, defense, surprise, escape, groups and waves, ammo, armor. Grow the [rolls](design/rolls.md) list.
2. **Encounters and tables design** — how table results chain, choices, left-behind encounters, Unique Events.
3. **Effects and game moments** — consolidate the two core concepts found in every topic so far.
4. **Town map and MVP scope** — includes the town map transcription (Milestone 1).
5. **Project setup** — Milestone 4 except the Python bootstrap: `.tool-versions` (blocks running Python in the repo), `.gitignore`, minimal `CLAUDE.md`, `.claude/settings.json`.
6. **GitHub planning** — milestones, labels and issues from the roadmap; decide whether issues or the Readme are the source of truth.
7. **Review engine tasks** against the design, then start the engine in dependency order, bootstrapping the Python project with common defaults.
8. **Rules cleanup** — Milestone 3, as the engine needs each table.
