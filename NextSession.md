# Next sessions

Planned work sessions with Claude, in order, each with the model and effort to use; each wrap-up reviews the next session's. The [Readme](Readme.md) holds the roadmap and decisions; this file holds the plan for upcoming sessions. How a session runs, which model to use and how to prompt it: see [Working with Claude](WorkingWithClaude.md).

## Reminders

- E10 also moves the die ranges written in Python into the YAML (D1): the leads of `leads.py` and the samurai sword of Random Objects 54 (`PICKED_BY_DIE` in `engine/creation.py`). See the Readme's E10.
- Since E7, Skills give their numbers through `effects` in the YAML and `engine/effects.py`; later tasks plug in the parameters they read (E9 the carry limit, E12 the surprise chance) and the pending tests in `tests/test_effects.py` (Dodge's balance and Faith E12, Medic E11).
- **Literal blocks for R3's texts** (a small PR, Sonnet, any time): R2 keeps a text of several paragraphs or a list as a literal block (`|-`, a blank line between paragraphs, one list item per line), which the user prefers on screen. R3's mission text and any other folded text with several paragraphs move to the same, without changing a word.
- [`gameRules/book_errors.md`](gameRules/book_errors.md) now also lists the typos a batch fixed and the text it reworded ("Fixed or reworded"), to check again in the review session.
- E4 dropped log replay (seed + answers played back through the scripted interface): not needed for now. The seed and every answer are still logged, so it can be added when a bug needs it. P1 decides whether it needs it.
- Home is a Safe House by default ([ruling](design/rulings.md#safe-houses)), but until E15 it is a plain box: it rolls the 1 in 6 and can be Searched (a pending test waits for E15).
- Attaching a sheet by stepping onto it (the Readme's "Any time" item) replaces the "attach a new sheet" action: a small PR of its own, any time.
- Taking and dropping items (the Readme's "Any time" item after R3): a small PR, Sonnet. Since E6 an item has an `item.` ID on its table entries, a weapon (or a variant) its `weapon.` ID, and `Game.add_item` and `remove_item` exist ([rules text in YAML](docs/content.md#items)).
- Reading the PDFs: this machine has no poppler (`pdftotext`, `pdftoppm`). Install `pypdf` in a scratch venv to extract the ebook's text, and `pymupdf` to render a page as an image (T1 checked the pregenerated sheets that way).
- **E9: an item's count has no unit on screen**: creation says `You take: Rifle (11).`, where 11 is bullets (uses, jars…). E9 shows the inventory: give the count its unit (`Rifle, 11 bullets`), probably a unit per item in the YAML (noted in the T2 session).
- **Drills from E9 on**: each task adds its drill to `DRILLS` in `engine/drills.py` (a line saying what it tries, a setup through the `Game` API that gives the stop condition) and a scenario in `tests/test_drills.py`; the pregenerated characters (`creation.pregenerated`) are the usual start. E9's is `inventory`.
- The pending tests (skipped, in `tests/test_manual_actions.py` and `tests/test_effects.py`) name the task they wait for: E11, E12, E13, E15, after R3. Write their bodies when that task comes.

## For the next review

Drift noticed outside a session's scope, for the next consistency review (V1) to start from ([consistency reviews](WorkingWithClaude.md#consistency-reviews)).

- Code health: `engine/game.py` (655 lines after E8) and `interface/terminal.py` (679) keep growing with each task; whether to split them, and along which lines (E7).
- `Game.create_character(life, sanity)` now takes the base values (the current ones start at the max); the parameter names do not say so (E7).
- Tests raise a Skill to Expert, or learn one mid-game, by writing `character.skills` directly, not through `Game` (E7; again in `tests/test_moments.py`, E8).
- Home's ruling ([Safe Houses](design/rulings.md#safe-houses)) is tagged `gap` and says "the book never says what Home is", but a creator answer says the starting space is not a Safe House ([creator answers](design/creator-answers.md)). The decision stands (E5a, the user's choice for role play); the ruling's wording should say that our default departs from the creator's answer, and that the switchable "horrific" mode is the creator's reading (E8).
- `state.py` now imports `content.Effect`, so a `Lasting` holds the effect itself rather than an ID: plain frozen data, but the first content class in the game state (E8).
- Feedback notes in `feedback/feedback.md`: V1 decides what happens to a note once triaged (removed, or moved to the log of the session that triaged it) (T1). T2 triaged the `creation` drill's notes (its log says what became of each); the `walk` drill's notes of 2026-11-11 23:18 to 23:23 are V1's.
- Screen wording, from the `walk` drill (T2): the Home screen numbers its choices, then says "Home is box 1." (the user typed 23); Move does the same ("Move to: choose a box", then "Box 2."). The user's idea: "Choose your starting square", then "Home is now box 1", saying that boxes are numbered in the order you explore them. Also a table's rules line keeps sentences meant for paper play ("do NOT read the content of the tables in advance"): how the rules text is adapted to the screen.
- Screen text (T2): the other terminal strings move into `interface/screens/`; `test_every_creation_text_is_used` covers only `creation.*` (book mode and rolls are checked by their own tests); the recap's `_sheet` and the status line's `_status` both list the character (T2).
- Item-table entries have no `name` (T2): a roll line reads "Random Objects table, rolled 45" where an Injury reads "Injury table, rolled 1: Facial scar", because the book prints an item entry's name as the first words of its text ("Random book. Roll 2d6…", `content/tables/random_objects.yaml`). Whether Random Objects, Useful Stuff and Random Weapon entries get a `name:`, and whether the text keeps it at its start.
- Arrows (T2, seen in the creation recap): the Bow Skill gives "a bow and d6+3 arrows" at creation (what the engine rolls), the weapon summary's Bow says "Comes with 2d6+3 arrows". Not in `book_errors.md` nor the rulings yet: a book error to record, and maybe a ruling for a bow found during play (options to the user).
- `interface/terminal.py` is 964 lines after T2 (730 after T1); `tests/test_feedback.py` repeats the `Typist` of `tests/test_terminal.py` (a shared test helper, `conftest.py`, may be worth it) (T1).

## Drills to play before the next session

- `xp` (5 minutes): buying a Skill with XP, which learning Arcane Skills extends; the planning session can start from what you notice.
- Not `walk` for now: most town tables are not copied, so nearly every box ends in book mode (T2 feedback). It comes back once the town tables are copied.

## Plan

1. **E9** — inventory, with its `inventory` drill.
   Model: **Sonnet, high effort** (a clear spec in `design/inventory.md`, but many limits that may need rulings; switch to Opus if a design question comes up).
2. **V1** — the first consistency review (Opus, high effort), which also triages the drill feedback (the `xp` drill's note among them: the wording of a purchase).
3. **R7a** — the Random Book table, ahead of E18. Model: **Sonnet, medium effort** (a copying batch of 12 entries; can run any time before E18, also as a background agent).
4. **E18** — books and learning Arcane Skills, moved into Step 1 (the planning session after T2), with its `books` drill. Model: **Opus, high effort** (new engine parts, time without moving and prerequisites, and four open rule questions in its entry).
5. **Step 1** goes on — E10 to E17 with V2 after E14, then P1 (the first playtest) and V3 after E17, one task per session, each with its drill, and the R batches done ahead of the task that needs them (R4 before E12, R5 before E16; R6 and R7b any time). The batches do not touch the engine and can run as background agents of a coordinator session.
   Model: per task, from the [model table](WorkingWithClaude.md#which-model-for-which-session): Opus, high effort for E10 and E12, the reviews and the playtests; Sonnet for the others (E9 included); Sonnet, medium effort for the copying agents, Opus for R6 (events). E8 went smoothly at Opus, high effort: the time went to rulings with the user, the code followed the design; keep E10 and E12 there.
