# Next sessions

Planned work sessions with Claude, in order, each with the model and effort to use; each wrap-up reviews the next session's. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- E4 dropped log replay (seed + answers played back through the scripted interface): not needed for now. The seed and every answer are still logged, so it can be added when a bug needs it.
- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.
## Plan

1. **E5a** — book mode, reading. The skeleton is done: a whole game can be walked with every box's entry shown. Load the YAML by ID, roll on arriving (Town Exploration in a new box, 1 in 6 Random Encounter in a visited one), show only the entry reached with its notes, go to a table or event, record what was reached, attach a new sheet when the first is full. Decides how a table's own rules text is shown (on request, or the first time) ([rules text in YAML](docs/content.md)).
   Builds on the E4 loop: arriving is its hook point. The placeholder character (Life 8, Sanity 8, Food d6) stays until E6.
   Model: **Opus, high effort**. First engine user of the content, and the first requests beyond moving.
2. **E5b** — book mode, manual actions: gain or lose, items, roll vs L, Search roll, mark a Safe House; the request shapes they need (an amount, an item name, a roll). The turn ends as soon as Life or Sanity reaches 0, once effects have resolved.
   Model: **Opus, high effort**. New request shapes, and the first rules that ask from inside a change.
3. **Step 1** — E6 to E17, one task per session, with the R batches done ahead of the task that needs them (R2 and R3 before E6, R4 before E12, R5 before E16). The batches do not touch the engine and can run as parallel sessions (in a worktree; otherwise a plain branch is enough); R2 and R3 can be piloted with a [coordinator session](WorkingWithClaude.md#coordinator-session). Each batch moves its tables out of `content/catalogue.yaml`. Everything is copied to YAML before step 1 is playable.
   Model: per task, from the [model table](WorkingWithClaude.md#which-model-for-which-session): Opus, high effort for E6, E7, E8, E10 and E12; Sonnet for the others; Sonnet, medium effort for the R batches, Opus for R6 (events).
