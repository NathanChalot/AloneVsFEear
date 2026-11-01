# Next sessions

Planned work sessions with Claude, in order, each with the model and effort to use, reviewed at the end of every session. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- E4 dropped log replay (seed + answers played back through the scripted interface): not needed for now. The seed and every answer are still logged, so it can be added when a bug needs it.
- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.

## Plan

1. **Project review** — a step back before book mode: an adversarial review of the project so far (design, rulings, roadmap, architecture, code and tests, process). Findings only, no fixes during the review: each finding gets a severity and a proposed action, then the user goes through them one at a time; what is agreed becomes roadmap entries, rulings or doc fixes. A fresh session on purpose: it reads the repository cold, not the session that wrote E4.
   Model: **Opus, high effort**.
   Prompt:
   ```
   Project review session: an adversarial review of the project so far, before E5. Read
   CLAUDE.md, the Readme, NextSession.md, WorkingWithClaude.md, design/, docs/, the code and
   tests, and the latest logs in claude-logs/.
   Look for what is wrong, risky or not worth its cost, on five angles: design coherence
   (docs consistent with each other and with gameRules/), architecture risks (the callback
   protocol against saving, reactions, a GUI; the state; content by ID), the roadmap (order,
   estimates, missing tasks), code and test quality, and the process (docs and rituals worth
   what they cost). Do not fix anything. Give me a short list first, one line per finding with
   a severity and a proposed action, then go through them one at a time, waiting for my answer.
   Decide nothing and rule nothing yourself. No spoilers.
   ```
   If the Mermaid CLI is installed (`mmdc`), also check that every diagram renders.
2. **E5** — book mode. The skeleton is done: a whole game can be walked in book mode. Decides how a table's own rules text is shown (on request, or the first time); notes are shown with the entries that point to them ([rules text in YAML](docs/content.md)).
   Builds on the E4 loop: arriving, Search and the free actions are its hook points; manual actions are new `Choose` topics (or new request shapes). The placeholder character (Life 8, Sanity 8, Food d6) stays until E6.
   Model: **Sonnet**. Clear spec, and E4 left a simple protocol to extend; switch to Opus if how a table's rules are shown, or a new request shape, turns into a design debate.
3. **Step 1** — E6 to E17, one task per session, with the R batches done ahead of the task that needs them (R2 and R3 before E6, R4 before E12, R5 before E16). The batches do not touch the engine and can run as parallel sessions (in a worktree; otherwise a plain branch is enough); R2 and R3 can be piloted with a [coordinator session](WorkingWithClaude.md#coordinator-session). Each batch moves its tables out of `content/catalogue.yaml`. Everything is copied to YAML before step 1 is playable.
   Model: per task, from the [model table](WorkingWithClaude.md#which-model-for-which-session): Opus, high effort for E6, E7, E8, E10 and E12; Sonnet for the others; Sonnet, medium effort for the R batches, Opus for R6 (events).
