# Next sessions

Planned work sessions with Claude, in order. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.

## Plan

1. **R1** — YAML layout, ID scheme and the four exploration tables, fixed against the original PDFs in `origin_rules/`, with the validation tests.
2. **E1 and E2** — dice and game state.
3. **E3** — town map, moves and time.
4. **E4** — engine/interface protocol and game loop. Start with a short design discussion before any code: it is the main architecture choice.
5. **E5** — book mode. The skeleton is done: a whole game can be walked in book mode.
6. **Step 1** — E6 to E17, one task per session, with the R batches done ahead of the task that needs them (R2 and R3 before E6, R4 before E12, R5 before E16). The batches do not touch the engine and can run as parallel sessions. Everything is copied to YAML before step 1 is playable.
