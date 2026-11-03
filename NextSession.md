# Next sessions

Planned work sessions with Claude, in order, each with the model and effort to use; each wrap-up reviews the next session's. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- E10 also moves the die ranges written in Python into the YAML (D1): the leads of `leads.py` and the samurai sword of Random Objects 54 (`PICKED_BY_DIE` in `engine/creation.py`). See the Readme's E10.
- Merge the E7 PR (`e7-rolls-effects`) before starting E8.
- Since E7, Skills give their numbers through `effects` in the YAML and `engine/effects.py`; later tasks plug in the parameters they read (E8 the Food interval, E9 the carry limit, E12 the surprise chance) and the pending tests in `tests/test_effects.py` (Dodge's balance E12, Faith E18, Medic E11).
- **Literal blocks for R3's texts** (a small PR, Sonnet, any time): R2 keeps a text of several paragraphs or a list as a literal block (`|-`, a blank line between paragraphs, one list item per line), which the user prefers on screen. R3's mission text and any other folded text with several paragraphs move to the same, without changing a word.
- The Injury and Insanity tables carry the rules' Mental Scars and Injuries section as their text, split between them (the Injury paragraph reworded with the user): E8 reworks it, once it rules between that section and the Life and Sanity passages (1 or 2 points, or all the Damage of an attack).
- [`gameRules/book_errors.md`](gameRules/book_errors.md) now also lists the typos a batch fixed and the text it reworded ("Fixed or reworded"), to check again in the review session.
- E4 dropped log replay (seed + answers played back through the scripted interface): not needed for now. The seed and every answer are still logged, so it can be added when a bug needs it.
- Home is a Safe House by default ([ruling](design/rulings.md#safe-houses)), but until E15 it is a plain box: it rolls the 1 in 6 and can be Searched (a pending test waits for E15).
- Attaching a sheet by stepping onto it (the Readme's "Any time" item) replaces the "attach a new sheet" action: a small PR of its own, any time.
- Taking and dropping items (the Readme's "Any time" item after R3): a small PR, Sonnet. Since E6 an item has an `item.` ID on its table entries, a weapon (or a variant) its `weapon.` ID, and `Game.add_item` and `remove_item` exist ([rules text in YAML](docs/content.md#items)).
- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread.
- Reading the PDFs: this machine has no poppler (`pdftotext`, `pdftoppm`). Install `pypdf` in a scratch venv to extract the ebook's text.
- The pending tests (skipped, in `tests/test_manual_actions.py` and `tests/test_effects.py`) name the task they wait for: E8, E11, E12, E13, E15, E18, after R3. Write their bodies when that task comes.

## For the next review

Drift noticed outside a session's scope, for the next consistency review (V1) to start from ([consistency reviews](WorkingWithClaude.md#consistency-reviews)).

- Code health: `engine/game.py` (580 lines) and `interface/terminal.py` (609) keep growing with each task; whether to split them, and along which lines (E7).
- `Game.create_character(life, sanity)` now takes the base values (the current ones start at the max); the parameter names do not say so (E7).
- Tests raise a Skill to Expert by writing `character.skills` directly, not through `Game` (E7).

## Plan

1. **E8** — moments and reactions: announce moments, reactions with their scripts, the lifetimes the Skills and Food need; the Food upkeep as a reaction that Resistant to Hunger and Eating Disorder change (it can read `Parameter.FOOD_INTERVAL` since E7). Open: the Food clock when the interval changes mid-game.
   Model: **Opus, high effort** (kept after E7: E7 went smoothly once its design was settled with the user, and E8 shapes the moments every later task hooks into).
2. **E9** — inventory, then **V1**, the first consistency review (Opus, high effort).
3. **Step 1** goes on — E10 to E17 with V2 after E14 and V3 after E17, one task per session, with the R batches done ahead of the task that needs them (R4 before E12, R5 before E16; R6 and R7 any time). The batches do not touch the engine and can run as background agents of a coordinator session.
   Model: per task, from the [model table](WorkingWithClaude.md#which-model-for-which-session): Opus, high effort for E10 and E12 and the reviews; Sonnet for the others (E9 included); Sonnet, medium effort for the copying agents, Opus for R6 (events).
