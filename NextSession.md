# Next sessions

Planned work sessions with Claude, in order. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.

## Plan

1. **Project setup and GitHub planning** — Milestone 4: `.tool-versions` (blocks running Python in the repo), minimal `CLAUDE.md` (include book mode and the YAML/Python split), `.claude/settings.json`, Python bootstrap with common defaults. Then milestones, labels and issues from the roadmap (R1–R7, E1–E20); decide whether issues or the Readme are the source of truth.
2. **R1** — YAML layout, ID scheme and the four exploration tables, fixed against the original PDFs in `origin_rules/`, with the validation tests.
3. **E1 and E2** — dice and game state.
4. **E3** — town map, moves and time.
5. **E4** — engine/interface protocol and game loop. Start with a short design discussion before any code: it is the main architecture choice.
6. **E5** — book mode. The skeleton is done: a whole game can be walked in book mode.
7. **Step 1** — E6 to E17, one task per session, with the R batches done ahead of the task that needs them (R2 and R3 before E6, R4 before E12, R5 before E16). The batches do not touch the engine and can run as parallel sessions. Everything is copied to YAML before step 1 is playable.
