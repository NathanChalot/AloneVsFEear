# E5a: book mode, reading

- Date: 2026-11-01
- Session ID: 676262e5-ce82-4e83-bd87-4db365aefb16 (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `e5a-book-mode-reading` (the PR is found from it)
- Model: Opus 5.5, high effort
- Transcript: [transcripts/202611011228-e5a-book-mode-reading.txt](transcripts/202611011228-e5a-book-mode-reading.txt)

## Goal

Book mode, reading: arriving rolls the table the rules call for, the entry reached is shown and followed to the next tables or events, what was reached is recorded, and a new sheet can be attached once one is full. Done when a player can walk the town in the terminal, every box's entry shown as text, and walk onto a new sheet once the first is full.

## Done

- **A turn as in the game flow**: move, arrive (the box resolved before anything else), free actions (move, attach a sheet once one is full, quit). A Food upkeep that kills stops the arrival.
- `engine/book_mode.py`: `resolve(game, interface, id)` reaches a table or event, then follows each entry until it leads nowhere. Book mode is what the engine cannot read: after a table not copied yet or a numbered event, the player says where the text leads (a table, an event, or nowhere else).
- `engine/leads.py`: how each entry of Town Exploration and Random Encounter leads on, keyed by entry ID: `Auto` (rolled without asking), `Choice` ("your choice": only the tables named), `DieRoll` (Town Exploration 7: the engine rolls the d6). Transitional until E10.
- `Game.roll_table` (nested tables rolled down to the entry; catalogued tables rolled with no entry), `Game.play_event`, `Game.new_sheets`; `Arrival.new`; entries and events recorded as `PLAYED` at every level there is; the 13 place tables (`PLACE_TABLES`) become places of the box.
- Protocol: topics `CHOICE`, `BOOK`, `TABLE`, `EVENT`, `SHEET`; `Book` (table, event, done); events `Rolled`, `Wandering`, `LeadRolled`, `EventPlayed`, `SheetAttached`; `ask` moved from the loop to `protocol.py` (book mode asks too).
- Content: the 42 numbered events catalogued in `catalogue.yaml` (`event.1` to `event.42`, name and source, no text), `CatalogueEvent`, `Content.events()`, kind `event`.
- Terminal: the entry with its notes, or the source and number of a table not copied yet; "Your choice" and "Where does the text lead?" menus; a table's rules the first time it is rolled in a game and on `r`; letter keys (`m`, `s`, `q`, `t`, `e`, `d`), numbers for tables; the sides of a new sheet in words.
- Tests written first: `tests/test_book_mode.py` (scenarios, leads checked against the YAML refs, engine API, five long random games that fill and attach sheets), new terminal and content tests; the E4 tests given the dice and answers the arrivals now need. 292 pass, ruff clean, the docs' Mermaid diagrams render.
- Docs: `docs/architecture.md`, `docs/content.md`, the Readme (E5a done, How to play, E15, an "Any time" task), `NextSession.md`; the Home ruling in `design/rulings.md`, with `design/safe-houses.md`, `design/glossary.md` and `design/game-flow.md` fixed to match.
- A first version offered the entry's tables among the free actions, next to moving. The user saw that a player could then skip the box, and asked to review how a turn runs together: the design already said it (resolve, then free actions), the code had not followed it. Rewritten as above.

## Decisions

- **Home is a Safe House** (the user), `gap`, switchable to a horrific mode where it is a plain box. It makes sense in role play: the character barricaded their home and starts with a place to heal. The book makes no exception for Home and names the starting box apart from Safe Houses. Written as a ruling now; the mechanics (no encounter, healing) come with E15, with how much Home heals and whether it counts toward the 3.
- **The software guides; it offers only what the rules allow** (the user). The box is resolved before any free action; "another table", "a numbered event" and "nowhere else" appear only where the engine cannot read the text (a table or event not copied yet). They disappear as tables are copied (the references are known) and written (the entry plays itself).
- **Entries lead on as their text says** (the user): rolled without asking when one table is named, a choice when the text says so, the engine's own roll when the text rolls. Behaviour in Python by entry ID (`leads.py`), a small first piece of E10.
- **No random picks for "your choice"** (the user): considered as a switchable option, dropped to keep to the book.
- **A table's own rules are the interface's choice** (the user, option a): the terminal shows them the first time the table is rolled in a game, and again on `r`. Rejected: an engine option in every interface; first time only, kept in the game state.
- **Attaching a sheet is a free action for now** (the user), offered once a sheet is full. Stepping across a full sheet's edge to attach it (smoother) is a small task of its own for later; switching costs little.
- **Numbered events are catalogued now** (the user): IDs `event.<number>`, so they can be played and recorded before the events batch (R6) copies their text. Rejected: moving R6 before E5a; no events until R6.
- **The module is `book_mode.py`** (the user): what the engine cannot play yet; it stays as content grows, used less and less.
- An entry of a catalogued table is not recorded: its ID is not known until the table is copied (a roll of 4 may be entry `3-4`). The place is recorded.

## Open questions

- Home: healing per visit, and whether it counts toward the 3 Safe Houses (E15).
- Where the manual actions sit (E5b): inside the resolve step after an entry the engine cannot read, before "nowhere else", so an entry is applied before the player leaves it; and among the free actions where the rules allow.
- A copied entry with a condition ("if you have…") has no lead kind yet: none of the arrival tables has one. Decided with the first table that does.

## Next

E5b: book mode, manual actions (Opus, high effort).
