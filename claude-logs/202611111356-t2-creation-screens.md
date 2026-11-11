# T2: Creation screens

- Date: 2026-11-11
- Session ID: 61f9b9c0-3e38-476b-859c-386c2bda155f (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `t2-creation-screens` (the PR is found from it)
- Model: Opus 5.5
- Transcript: [transcripts/202611111356-t2-creation-screens.txt](transcripts/202611111356-t2-creation-screens.txt)

## Goal

Handle the feedback from the user's first `--drill creation` runs (`feedback/feedback.md`): discuss each note, the user decides, then tests first and the code. Not a planned roadmap entry: the session came out of the first drill, and is recorded as T2 in the Readme.

Done when: creation reads clearly when the user plays the `creation` drill. Met: three more runs; their last notes were wording, fixed in the session.

## Done

- **Branch from `main`** once the T1 PR was merged (the feedback notes stashed and brought back).
- **Knife, stick and kitchen knife** (commit 1): the park sentence moves from the "Knife or stick" heading to the stick's `extra`, the house sentence to the kitchen knife's; the headings keep the rest. Same words, recorded in `book_errors.md` ("Fixed or reworded"); a content test checks each pick-up sentence belongs to its own weapon.
- **Creation screens** (commit 2): the engine tells `StepStarted(Step)` before each of the 5 steps and the terminal shows a heading and what the step asks. The terminal's wording moves into YAML (`interface/screens/`, `screen_text.py`). The points read "share them between Life and Sanity, or give all 3 up for one extra Skill or random item", with the result shown ("→ Life 10, Sanity 9."). The second Skills list keeps its numbers, the Skill taken shown "(TAKEN) Good Shot (TAKEN)" and refused. `readline` for the arrow keys.
- **Second run's notes** (commit 3): `r` hides or shows the Skills' descriptions, on its own line (a screen modifier, the choice kept for the next list); a variant's own sentence in brackets ("Stick (you may pick up a stick every time you visit a park)"); the roll line "Injury table, rolled 1: Facial scar"; the book mode screen: one explanation line between blank lines, "Leads to:", "By hand:", "Your choice?".
- **The character once made** (commit 4, the user's idea): `Created` is told, the terminal shows the character as a list (stats, Skills, weapons, items, notes), names only, `r` for the descriptions, Enter to go on. A base for a character sheet during play. The creation drill no longer shows the character twice.
- **Third run's notes** (commit 5): the introduction lists the 5 steps; "rolled twice", not "roll twice", since the game rolls.
- 898 pass, 10 skipped, ruff clean.
- **`/wrap-up`** (the user's idea): a skill for steps 4 to 8 of a session's end. `/export` cannot be run by Claude and sends it no message, so the skill waits for the transcript file in the background and goes on once it appears (the user chose this over converting the session's raw file into a transcript). First used for this session's export.
- **Wrap-up**: drift check (`docs/architecture.md`: packages, the sequence diagram, creation, book mode and the roll line in the terminal, the recap, screen text, line editing; the Readme's status, How to play, letters table, decisions, T2 entry, E18 and Later; WorkingWithClaude's drill rules and tables; NextSession's reminders, review items, drills and plan).

## What became of each note

Creation drill, first run (13:53 to 13:56): the name, points, Skills and weapon steps lacked context → step headings and explanations; the arrow keys → `readline`, going back a step after the MVP; the second Skills list without descriptions → stable numbers, "(TAKEN)", `r`.

Second run (16:25 to 16:32): `r` as a hide/show option → done; the stick's sentence in brackets → done; the book mode screen and "Apply the text, then where does it lead?" → the new book mode screen; "Random Objects table: 45" → "Random Objects table, rolled 45" (entry names noted for V1); learning an Arcane Skill from a book, and finishing what creation involves first → a planning session moves books and learning Arcane Skills into Step 1.

Third run (23:12, 23:15): the steps listed in the introduction, "rolled twice" → done.

Walk drill (23:18 to 23:23), aborted: Home's "box 1" after choosing 23, and a table's rules line written for paper play → V1 (NextSession); the drill is a pain while most tables are not copied → not suggested until the town tables are.

## Decisions

- **Arrow keys edit the line** (the user, "KISS"): `readline`. Rejected for now: going back to a previous step (after the MVP).
- **A Skill already taken stays in the list**, "(TAKEN) Good Shot (TAKEN)", and is refused (the user: obvious at a glance). Rejected: renumbering the list, strikethrough (terminal styling, after the MVP).
- **`r` is a screen modifier**, on its own line, descriptions shown by default, the choice carried to the next list (the user).
- **The knife keeps its heading** and the park sentence moves to the stick (the user, on Claude's recommendation). Rejected: knife and stick as separate weapons with an "either" option.
- **The engine tells the creation steps** (`StepStarted`, `Created`): the interface could not tell them apart from the requests (the Skills' gear comes before Random Weapon).
- **Screen text in YAML** (the user): `interface/screens/`, never in a folder with Python files, keys like `creation.points.heading`, may repeat the rules' words; the other terminal strings move there in V1.
- **The roll line**: "Table, rolled N: Name". An item entry has no name yet: noted for V1 rather than a content change now.
- **The book mode screen** (the user's tweak: a blank line before and after the explanation, shown every time).
- **Books and learning Arcane Skills move into Step 1** (the user: a core mechanic; books are items already, so no E9 dependency): a planning session splits E18, Gate stays in Step 2.
- **The recap**: names only, no rolls, a list with `r` for the descriptions (the user).
- **Drills before a session** (the user): not in `/start`, never a blocker; the wrap-up writes in NextSession which drills to play before the next session. Whether the roadmap shows the drills is left to the planning session.

## Mistakes

- Claude said learning Arcane Skills needs Clues and Hell Gates; only Gate does.
- Claude said books need E9's inventory; they are items already.
- Claude promised "rolled 45: Random book", but item entries have no names.
- Claude gave a seed for the book without its answers: the book comes only after trading for a 3rd Skill and taking Bow, whose arrows roll first.

## Open questions

- V1: entry names for item tables, the Bow's arrows (d6+3 vs 2d6+3), the Home and Move screens, the rules lines meant for paper play, the other terminal strings into `screens/` (NextSession's "For the next review").
- Planning: whether the roadmap shows the drills.

## Next

A planning session (Opus, medium effort) that moves books and learning Arcane Skills into Step 1, then E9 (Sonnet, high effort). Before it: the `xp` drill.
