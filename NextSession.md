# Next sessions

Planned work sessions with Claude, in order. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions.

## How a session works

1. Start from this file, the [Readme](Readme.md) and the latest log in [`claude-logs/`](claude-logs/).
2. Work in a dedicated worktree and branch; one PR per session. During the session, Claude never commits or pushes without explicit permission.
3. End by updating the Readme (checkboxes, decisions) and this file (remove the done session, adjust the plan).
4. Claude writes the session log in `claude-logs/YYYYMMDDHHmm-session-name.md`.
5. The user exports the transcript with `/export claude-logs/transcripts/YYYYMMDDHHmm-session-name.txt` (same name as the log).
6. Claude commits the session, pushes the branch, opens the PR, writes the PR link in the log and pushes again. This end-of-session commit and push is agreed once and for all, so the next session starts clean.

## Plan

1. **Effects and game moments** — consolidate the two core concepts found in every topic so far; encounters add timed steps ("as you leave", "as soon as you pick up") and deferred events.
2. **Town map and MVP scope** — includes the town map transcription (Milestone 1). Encounters found moves off the grid: forced moves (#16, #42) and a separate map (#41).
3. **Project setup** — Milestone 4 except the Python bootstrap: `.tool-versions` (blocks running Python in the repo), `.gitignore`, minimal `CLAUDE.md`, `.claude/settings.json`.
4. **GitHub planning** — milestones, labels and issues from the roadmap; decide whether issues or the Readme are the source of truth.
5. **Review engine tasks** against the design, then start the engine in dependency order, bootstrapping the Python project with common defaults.
6. **Rules cleanup** — Milestone 3, as the engine needs each table.
