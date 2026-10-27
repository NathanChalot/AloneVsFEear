# Next sessions

Planned work sessions with Claude, in order. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions.

## How a session works

1. Start from this file, the [Readme](Readme.md) and the latest log in [`claude-logs/`](claude-logs/).
2. Work in a dedicated worktree and branch; one PR per session. Claude never commits or pushes without explicit permission.
3. End by updating the Readme (checkboxes, decisions) and this file (remove the done session, adjust the plan).
4. Claude writes the session log in `claude-logs/YYYYMMDDHHmm-session-name.md`.
5. Export the transcript with `/export claude-logs/transcripts/YYYYMMDDHHmm-session-name.txt` (same name as the log).

## Plan

1. **Project setup** — Milestone 3 except the Python bootstrap: `.tool-versions`, `.gitignore`, minimal `CLAUDE.md`, `.claude/settings.json`.
2. **GitHub planning** — milestones, labels and issues from the roadmap; decide whether issues or the Readme are the source of truth.
3. **Python tooling** — D3, then bootstrap the Python project.
4. **Sheet transcription** — character sheet and town map from the PDF images; settles D5.
5. **Content format spike** — D1 and D2.
6. **MVP scope** — D6.
7. **Rules cleanup** — Milestone 2, table batches in the D1 format.
8. **Engine** — E1 to E13 in dependency order, one or two per session.
