# Next sessions

Planned work sessions with Claude, in order, each with the model and effort to use; each wrap-up reviews the next session's. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- Merge the R2 PR (`r2-skills-harm`) before starting E6.
- **Literal blocks for R3's texts** (a small PR, Sonnet, any time): R2 keeps a text of several paragraphs or a list as a literal block (`|-`, a blank line between paragraphs, one list item per line), which the user prefers on screen. R3's mission text and any other folded text with several paragraphs move to the same, without changing a word.
- The Injury and Insanity tables carry the rules' Mental Scars and Injuries section as their text, split between them (the Injury paragraph reworded with the user): E8 reworks it, once it rules between that section and the Life and Sanity passages (1 or 2 points, or all the Damage of an attack).
- [`gameRules/book_errors.md`](gameRules/book_errors.md) now also lists the typos a batch fixed and the text it reworded ("Fixed or reworded"), to check again in the review session.
- E4 dropped log replay (seed + answers played back through the scripted interface): not needed for now. The seed and every answer are still logged, so it can be added when a bug needs it.
- Home is a Safe House by default ([ruling](design/rulings.md#safe-houses)), but until E15 it is a plain box: it rolls the 1 in 6 and can be Searched (a pending test waits for E15).
- Attaching a sheet by stepping onto it (the Readme's "Any time" item) replaces the "attach a new sheet" action: a small PR of its own, any time.
- Taking and dropping items (the Readme's "Any time" item after R3): a small PR, Sonnet. An item is its table entry, a weapon has its own ID ([rules text in YAML](docs/content.md)).
- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.
- Reading the PDFs: this machine has no poppler (`pdftotext`, `pdftoppm`). Install `pypdf` in a scratch venv to extract the ebook's text.
- The pending tests (skipped, in `tests/test_manual_actions.py`) name the task they wait for: E6, E8, E11, E13, E15, after R3. Write their bodies when that task comes.

## Plan

1. **E6** — character and creation, and the rest of D1 (where plain data goes). Decides the weapon IDs that name two weapons (likely two IDs sharing the text, see the Readme).
   Model: **Opus, high effort** (kept after R2: E6 decides D1 and the weapon IDs, design work with the user).
2. **Step 1** — E7 to E17, one task per session, with the R batches done ahead of the task that needs them (R4 before E12, R5 before E16; R6 and R7 any time). The batches do not touch the engine and can run as background agents of a coordinator session.
   Model: per task, from the [model table](WorkingWithClaude.md#which-model-for-which-session): Opus, high effort for E7, E8, E10 and E12; Sonnet for the others; Sonnet, medium effort for the copying agents, Opus for R6 (events).
