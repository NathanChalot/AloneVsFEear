# Next sessions

Planned work sessions with Claude, in order. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.

## Plan

1. **E1 and E2** — dice and game state. First session with engine code and the first GitHub issue (Milestone 5). The table dice codes (`d6`, `2d6`, `d66`) already exist in `content/model.py` for the YAML checks; E1 may move them into the dice module.
2. **E3** — town map, moves and time.
3. **E4** — engine/interface protocol and game loop. Start with a short design discussion before any code: it is the main architecture choice.
4. **E5** — book mode. The skeleton is done: a whole game can be walked in book mode. Decides how a table's own rules text is shown (on request, or the first time); notes are shown with the entries that point to them ([rules text in YAML](design/content.md)).
5. **Step 1** — E6 to E17, one task per session, with the R batches done ahead of the task that needs them (R2 and R3 before E6, R4 before E12, R5 before E16). The batches do not touch the engine and can run as parallel sessions (in a worktree; otherwise a plain branch is enough). Each batch moves its tables out of `content/catalogue.yaml`. Everything is copied to YAML before step 1 is playable.
