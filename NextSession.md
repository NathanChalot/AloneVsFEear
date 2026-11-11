# Next sessions

Planned work sessions with Claude, in order, each with the model and effort to use; each wrap-up reviews the next session's. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- E10 also moves the die ranges written in Python into the YAML (D1): the leads of `leads.py` and the samurai sword of Random Objects 54 (`PICKED_BY_DIE` in `engine/creation.py`). See the Readme's E10.
- Merge the E8 PR (`e8-moments-reactions`) before starting T1.
- Since E7, Skills give their numbers through `effects` in the YAML and `engine/effects.py`; later tasks plug in the parameters they read (E9 the carry limit, E12 the surprise chance) and the pending tests in `tests/test_effects.py` (Dodge's balance E12, Faith E18, Medic E11).
- **Literal blocks for R3's texts** (a small PR, Sonnet, any time): R2 keeps a text of several paragraphs or a list as a literal block (`|-`, a blank line between paragraphs, one list item per line), which the user prefers on screen. R3's mission text and any other folded text with several paragraphs move to the same, without changing a word.
- [`gameRules/book_errors.md`](gameRules/book_errors.md) now also lists the typos a batch fixed and the text it reworded ("Fixed or reworded"), to check again in the review session.
- E4 dropped log replay (seed + answers played back through the scripted interface): not needed for now. The seed and every answer are still logged, so it can be added when a bug needs it. P1 decides whether it needs it.
- Home is a Safe House by default ([ruling](design/rulings.md#safe-houses)), but until E15 it is a plain box: it rolls the 1 in 6 and can be Searched (a pending test waits for E15).
- Attaching a sheet by stepping onto it (the Readme's "Any time" item) replaces the "attach a new sheet" action: a small PR of its own, any time.
- Taking and dropping items (the Readme's "Any time" item after R3): a small PR, Sonnet. Since E6 an item has an `item.` ID on its table entries, a weapon (or a variant) its `weapon.` ID, and `Game.add_item` and `remove_item` exist ([rules text in YAML](docs/content.md#items)).
- Compare the pregenerated characters in [`gameRules/14_pregenerated_characters.md`](gameRules/14_pregenerated_characters.md) against the original sheets in `origin_rules/`: image transcriptions are the part most likely to hold a misread. Do it before T1: its drills start from them.
- Reading the PDFs: this machine has no poppler (`pdftotext`, `pdftoppm`). Install `pypdf` in a scratch venv to extract the ebook's text.
- The pending tests (skipped, in `tests/test_manual_actions.py` and `tests/test_effects.py`) name the task they wait for: E11, E12, E13, E15, E18, after R3. Write their bodies when that task comes.

## For the next review

Drift noticed outside a session's scope, for the next consistency review (V1) to start from ([consistency reviews](WorkingWithClaude.md#consistency-reviews)).

- Code health: `engine/game.py` (655 lines after E8) and `interface/terminal.py` (679) keep growing with each task; whether to split them, and along which lines (E7).
- `Game.create_character(life, sanity)` now takes the base values (the current ones start at the max); the parameter names do not say so (E7).
- Tests raise a Skill to Expert, or learn one mid-game, by writing `character.skills` directly, not through `Game` (E7; again in `tests/test_moments.py`, E8).
- Home's ruling ([Safe Houses](design/rulings.md#safe-houses)) is tagged `gap` and says "the book never says what Home is", but a creator answer says the starting space is not a Safe House ([creator answers](design/creator-answers.md)). The decision stands (E5a, the user's choice for role play); the ruling's wording should say that our default departs from the creator's answer, and that the switchable "horrific" mode is the creator's reading (E8).
- `state.py` now imports `content.Effect`, so a `Lasting` holds the effect itself rather than an ID: plain frozen data, but the first content class in the game state (E8).

## Plan

1. **T1** — drills and feedback: `--drill creation`, `walk`, `lasting`, `xp`, and a way to write feedback while playing, with the seed and the box number. Compare the pregenerated characters with the original sheets first (see Reminders).
   Model: **Opus, medium effort** (the user's choice: a small, clear task, but the drills shape how the user gives feedback from now on).
2. **E9** — inventory, with its `inventory` drill, then **V1**, the first consistency review (Opus, high effort), which also triages the drill feedback.
3. **Step 1** goes on — E10 to E17 with V2 after E14, then P1 (the first playtest) and V3 after E17, one task per session, each with its drill, and the R batches done ahead of the task that needs them (R4 before E12, R5 before E16; R6 and R7 any time). The batches do not touch the engine and can run as background agents of a coordinator session.
   Model: per task, from the [model table](WorkingWithClaude.md#which-model-for-which-session): Opus, high effort for E10 and E12, the reviews and the playtests; Sonnet for the others (E9 included); Sonnet, medium effort for the copying agents, Opus for R6 (events). E8 went smoothly at Opus, high effort: the time went to rulings with the user, the code followed the design; keep E10 and E12 there.
