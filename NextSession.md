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

1. **Project setup** — Milestone 4 except the Python bootstrap: `.tool-versions` (blocks running Python in the repo), minimal `CLAUDE.md` (include book mode and the YAML/Python split), `.claude/settings.json`.
2. **GitHub planning** — milestones, labels and issues from the roadmap (R1–R7, E1–E20); decide whether issues or the Readme are the source of truth.
3. **R1** — YAML layout, ID scheme and the exploration tables, fixed against the original PDFs in `origin_rules/`. Bootstrap the Python project with common defaults for its tests.
4. **Engine skeleton** — E1 to E5, until a whole game can be walked in book mode.
5. **Step 1** — E6 to E17, with the R batches done in the order the engine needs them (R2 and R3 before E6, R4 before E12, R5 before E16). Everything copied to YAML before step 1 is playable.
