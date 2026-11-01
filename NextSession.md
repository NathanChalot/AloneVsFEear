# Next sessions

Planned work sessions with Claude, in order, each with the model and effort to use; each wrap-up reviews the next session's. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- E4 dropped log replay (seed + answers played back through the scripted interface): not needed for now. The seed and every answer are still logged, so it can be added when a bug needs it.
- Home is a Safe House by default ([ruling](design/rulings.md#safe-houses)), but until E15 it still rolls the 1 in 6 like any visited box.
- Attaching a sheet by stepping onto it (the Readme's "Any time" item after E5b) replaces E5a's "attach a new sheet" action: a small PR of its own, any time.
- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.
## Plan

1. **E5b** — book mode, manual actions: gain or lose, items, roll vs L, Search roll, mark a Safe House; the request shapes they need (an amount, an item name, a roll). The turn ends as soon as Life or Sanity reaches 0, once effects have resolved.
   Builds on E5a: a turn is move, arrive (the box resolved, `book_mode.resolve`), free actions (`_actions` in `engine/loop.py`). The manual actions belong in two places: inside the resolve step, offered with "nowhere else" (`Book.DONE`) after an entry the engine cannot read, so the player applies the entry before leaving it; and among the free actions where the rules allow it (spending XP, inventory). Search comes between arriving and the free actions, only once the box is resolved.
   Model: **Opus, high effort**. E5a went smoothly at Opus, high effort, but E5b brings the first requests that are not a choice among options (an amount, a name) and the first rule that interrupts a turn (death at 0).
2. **Step 1** — E6 to E17, one task per session, with the R batches done ahead of the task that needs them (R2 and R3 before E6, R4 before E12, R5 before E16). The batches do not touch the engine and can run as parallel sessions (in a worktree; otherwise a plain branch is enough); R2 and R3 can be piloted with a [coordinator session](WorkingWithClaude.md#coordinator-session). Each batch moves its tables out of `content/catalogue.yaml`. Everything is copied to YAML before step 1 is playable.
   Model: per task, from the [model table](WorkingWithClaude.md#which-model-for-which-session): Opus, high effort for E6, E7, E8, E10 and E12; Sonnet for the others; Sonnet, medium effort for the R batches, Opus for R6 (events).
