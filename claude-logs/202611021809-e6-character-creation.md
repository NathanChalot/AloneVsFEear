# E6: Character and creation

- Date: 2026-11-02
- Session ID: b3cca2bb-76a0-4408-a656-5398ffd2b837 (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `e6-character-creation` (the PR is found from it)
- Model: Opus 5.5, high effort
- Transcript: [transcripts/202611021809-e6-character-creation.txt](transcripts/202611021809-e6-character-creation.txt)

## Goal

E6: Life and Sanity with current and max values, the Skills at Basic and Expert, spending XP at any time, and character creation in the terminal. Decide the rest of D1 (where plain data goes) and the weapon summary headings that name two weapons.

Done when: the terminal walks the player through creation, and XP can be spent. Met.

## Done

- **D1 and the content** (tests first, loader then data):
  - The loader reads `item`, `count` and `uses` on entries, weapon `variants` (with an optional `extra` sentence), and `starting_gear` on Skills. An item ID is defined only on entries; a variant only on its heading.
  - The YAML gets item IDs on every Random Objects and Useful Stuff entry that gives an object, counts and uses, entries pointing to the exact variant, and Bow's and Faith's starting gear.
  - One text per item and per weapon: the Backpack and the candles reworded to the clearest text, six weapon texts completed from the tables (the flashlight, the Molotov cocktail, the flail, the kitchen knife, the hammer's and the shovel's extra sentences). All recorded in `gameRules/book_errors.md` ("Fixed or reworded"); the Markdown fixed together.
  - `docs/content.md`: the plain-data rule, variants, the new Items section, `starting_gear`; "Open" is now empty.
- **The character** (`engine/state.py`, `engine/game.py`): name, base Life and Sanity, `max(stat)`, gains stop at the max, Skills with a level, `Purchase`, `purchases()` and `buy()`, items held (`Item`, `add_item`, `remove_item`). GAIN tells the real change.
- **Creation** (`engine/creation.py`): name, the 3 points, Skills, starting gear, the three tables with duplicates rolled again, the knife or stick, d6 Food. Special entries keyed by ID: the samurai sword picked by a die, Food points, the books (book mode, through a new `book_mode.lead_on`).
- **The loop and the terminal**: creation replaces the placeholder character; a `p` action spends XP when a Skill is affordable; the status line shows the name and the max values, then the Skills and items.
- Eight commits, each tested on its own. 673 pass, 8 skipped, ruff clean.

## Decisions

- **Plain data in YAML** (D1, the user): a number the engine reads is a field next to the text, added when the engine first reads it. The user asked whether this locks anything in: no, the field shapes may change while no saved game depends on them.
- **Weapon variants on one heading** (the user): the heading keeps its ID and text; each weapon named becomes a variant with its own ID, holding the exact weapon. An `extra` sentence for what one variant does and not the other (the hammer, the shovel).
- **Item IDs on entries** (the user, after asking whether it could be a problem): an `item.` ID shared by the entries that give the same object (the Backpack is in two tables). No separate items file (the user).
- **One text per item and weapon, reworded to the clearest** (the user): where two tables or the summary say different things, keep the clearest wording, completed with what is missing (candles: "Used for many spells and rituals").
- **`count` and `uses` apart** (the user): how many objects, and how many times one object serves (the first aid kit, the strong coffee). Armor durability waits for E13.
- **Rulings** (in `design/rulings.md`, switchable): the knife or stick is the player's choice; Random Weapon 1 gives the bat or the hammer, the player's choice; a duplicate is anything already given at creation; Faith's holy symbol is the Religious symbol.
- **Skills give their starting gear through a YAML field** (`starting_gear`, the user): Bow and Faith.
- **Smaller commits** (the user): the work split into eight commits.
- **The die ranges written in Python stay until E10** (the user): the samurai sword's 1-2 / 3-6 (`PICKED_BY_DIE`) and the leads of `leads.py` go against D1, but E10 shapes "roll a die to pick a result" once for every table. Added to the Readme's E10.

## Open questions

- E10: the die ranges into the YAML.
- E13: armor durability.
- E18: buying Arcane Skills, and the books met at creation (book mode until then).
- The Readme's "Any time" items: taking and dropping items, attaching a sheet by stepping onto it, literal blocks for R3's texts.

## Next

E7 (rolls and effects), Opus, high effort.
