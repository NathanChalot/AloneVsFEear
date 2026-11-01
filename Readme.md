# Alone Against Fear — digital solo play

A program that runs a full campaign of **Alone Against Fear**, a survival-horror solo tabletop game based on the Four Against Darkness engine, from character creation to the last Hell Gate.

The game rules are extracted from the rulebook PDF into Markdown under `gameRules/`, which serve as the reference for the engine. The text of every table, entry, event, item and Skill is also copied into YAML, for the engine to show on screen (Milestone 3).

The rules text is from a commercial book: keep this repository private. The original PDFs go in `origin_rules/` at the repository root, which is git-ignored.

## Status

MVP phase. Rules extraction and domain design ([`design/`](design/)) are done. The rules text is being copied into YAML: the format and the four exploration tables are in (R1). The engine has started: dice (E1), the game state (E2), the town map with moves and time (E3), the engine/interface protocol with the game loop (E4), and book mode's reading half (E5a): a player can walk the town in the terminal, every box's entry shown as text ([how to play](#how-to-play)). Manual actions (E5b) come next.

**MVP goal:** play a whole campaign in the terminal, in two steps ([MVP scope](design/mvp-scope.md)):

1. **Bring Home the Bacon** — one complete mission: create a character, explore the town box by box, resolve encounters, search, manage inventory, Food and health, and end back Home with the Food, dead or insane.
2. **Close a Hell Gate** — Arcane Skills, books, and missions played one after another until 7 Hell Gates are closed. The game state is shaped as a campaign from the start: the map, the box counter, Food and Clues carry on across missions (see [game flow](design/game-flow.md)).

The engine follows the whole design, but only a thin slice of content is written. Everything else goes through **book mode**: the engine shows the entry's text and the player applies it with manual actions.

## How to play

What the game does today: choose Home, walk the town box by box, eat 1 Food every 5 boxes (or lose 1 Life without Food), and quit. A new box rolls the Town Exploration table, a visited box a 1 in 6 chance of a Random Encounter, and the box is resolved before you do anything else: the entry reached is shown, and the game follows it to the next table (it asks when the text says "your choice", it rolls the die when the text rolls one). A table or event not copied yet points to its Markdown file and the number rolled, and you say where its text leads: another table, a numbered event, or nowhere else. You apply what the text does to you yourself, until the manual actions (E5b). Once every box of a sheet is visited, you can attach a new sheet. The character is a placeholder (Life 8, Sanity 8, d6 Food) until character creation (E6).

Setup, with Python 3.13 or later (`.tool-versions` pins the version we use):

```
python -m venv .venv
.venv/bin/pip install -e .
```

Play:

```
.venv/bin/alone-against-fear              # or: .venv/bin/python -m alone_against_fear
.venv/bin/alone-against-fear --seed 7     # the dice of an earlier game
```

- Type the number of an option and press Enter. Actions have letters: `m` move, `s` attach a new sheet (once a sheet is full), `q` quit; where a text leads: `t` a table, `e` a numbered event, `d` nowhere else; `r` the rules of the last table rolled in the box. Tables to choose from are numbered. Ctrl-D or Ctrl-C quits.
- A status line comes before each action: box number, Life, Sanity, Food, XP, Clues.
- The map: `[n]` the boxes you can choose, `@` where you stand, `H` Home, a number for the last box number written in a visited box, `.` a box not visited yet.
- Each game writes a log to `logs/` (git-ignored; `--log-dir` to change it): the dice seed, every roll and every answer. Playing again with that seed and the same answers gives the same game.

## How to use this roadmap

The roadmap is split into milestones. Each `####` entry is sized to be one session's task: title, description, rules references, "Done when" and "Depends on". Check the box when it is done. GitHub issues are kept for user stories and bugs, only when needed. Deferred decisions are tracked here, so they are made deliberately when they block work, not up front. Before deciding, ask: is it worth deciding yet, or is it a constraint we would have to fight later?

## Working with Claude

Work happens in small, planned sessions with Claude. The upcoming sessions are listed in [`NextSession.md`](NextSession.md); past sessions are summarized in [`claude-logs/`](claude-logs/). [`WorkingWithClaude.md`](WorkingWithClaude.md) describes how a session runs and holds recommendations: session estimates, which model for which session, prompt templates.

## Decisions

### Made

- **Language:** Python. Strongest ecosystem for planned genAI features (local LLMs, image and video generation).
- **Interface:** terminal CLI first. Engine stays UI-agnostic so other front ends can be added.
- **MVP scope** (was D6): two steps, Bring Home the Bacon then Close a Hell Gate with campaign play; unwritten content goes through book mode. See [MVP scope](design/mvp-scope.md).
- **Engine/interface protocol** (E4): callbacks. The engine calls `ask(request)` when the player chooses (the answer must be one of the options) and `tell(event)` when something happens. Chosen over generators and a state machine: rules that ask deep inside other rules stay simple; the game is saved between turns. Interfaces read the game state and change it only through their answers. See [architecture](docs/architecture.md).
- **Rules text in YAML** (part of D1): every table, entry, creature, item, event and Skill gets a stable ID and its text in YAML; behaviour stays in Python, keyed by the same ID. The Markdown in `gameRules/` stays as the readable copy, fixed together with the YAML. Files, IDs (`table.town_exploration.7`, `mission.bring_home_the_bacon`) and the shape of a table: [rules text in YAML](docs/content.md).

### Guidelines

Former decisions that are better kept as guidelines than settled up front.

- **Tooling** (was D3) — pick common defaults when coding starts; change them freely.
- **Portability** (was D7) — keep the engine free of UI and genAI code; otherwise, rework code when a port actually happens.
- **Validation** (was D2) — tests are enough until a content format exists.
- **Saves** (was D4) — the campaign is the game state; saving a game means saving the campaign.
- **Design before code** — model the game in domain terms in [`design/`](design/) before writing engine code.

### Deferred

#### [ ] D1 — Rules content format
Partly decided: the text lives in YAML and behaviour in Python, both keyed by ID (see Made). Still open: where plain data goes (creature stats, item weights, Skill XP costs), in the YAML next to the text or in Python next to the behaviour. Most entries mix plain stats with unique rules, so the format must handle both without inventing a DSL.
- Decide when: the engine writes its first content (E6).

#### [ ] D8 — genAI integration
Where narration / image generation plug in, kept optional and behind interfaces. Post-MVP, but should not be blocked by MVP architecture.

### Moved to domain design

D5 (town map layout) and D6 (MVP content scope) were settled as design topics, see Milestone 2.

## Roadmap

### Milestone 1 — Rules extraction

- [x] Parse the rulebook PDF (`gameRules/extractor/`)
- [x] Split parsed output into sections: global rules, rolling tables, how the game works, game overview, random skill generation
- [x] [Character sheet](gameRules/12_character_sheet.md)
- [x] [Town map sheet](gameRules/13_town_map.md)
- [x] [Pregenerated characters](gameRules/14_pregenerated_characters.md)

### Milestone 2 — Domain design

Understand and diagram how the game works in domain terms before coding. Lives in [`design/`](design/). Rule interpretations go to [rulings](design/rulings.md).

- [x] [Glossary](design/glossary.md)
- [x] [Game flow](design/game-flow.md): campaign, mission, arriving in a box
- [x] [Character and progression](design/character.md): stats, Skills, XP, Injuries and Scars
- [x] [Inventory](design/inventory.md)
- [x] [Safe Houses](design/safe-houses.md)
- [x] [Rolls and tags](design/rolls.md), grown as we go
- [x] [Combat](design/combat.md): attack, defense, surprise, escape, groups and waves, ammo, armor
- [x] [Encounters and tables](design/encounters.md): how table results chain, choices, left-behind encounters, Unique Events
- [x] [Effects and game moments](design/effects.md): holders, kinds, lifetimes, moments, reactions
- [x] [Town map](design/town-map.md): grid shape, sheets, distances (was D5)
- [x] [MVP scope](design/mvp-scope.md): two steps, the content written in each, book mode for the rest (was D6)
- [x] Review the engine tasks below against the design: rewritten as Milestones 5 to 7

### Milestone 3 — Rules text in YAML

The text of every table, entry, creature, item, event and Skill is copied into YAML with a stable ID, so book mode can show it on screen ([MVP scope](design/mvp-scope.md#where-the-text-comes-from)). The OCR mangled the book's two-column layout: each batch fixes the damage against the original PDFs in `origin_rules/`, in the YAML and in the Markdown at once, and turns book page references into table names. Batches follow the order the engine needs them; all are done before step 1 is playable.

#### [x] R1 — YAML layout, IDs and exploration tables
Decide the file layout and the ID scheme ([rules text in YAML](docs/content.md)). Copy the Town Exploration, Random Encounter, Search and Missions tables.
- Fixes: Town Exploration (swapped columns, split rows 2 and 12), Random Encounter (nested d6→d6 structure), Missions (missing roll numbers).
- Done when: the four tables are in YAML, and tests check that every table covers its dice range and every reference points to an existing ID.
- Depends on: Milestone 4.

#### [ ] R2 — Skills and harm tables
The 21 Skills, the 11 Arcane Skills, the Injury and Insanity tables.
- Fixes: Insanity table (merged rows 2 and 3).
- Depends on: R1.

#### [ ] R3 — Weapons and items
Random Weapon table, weapon summary, Random Objects, Useful Stuff.
- Depends on: R1.

#### [ ] R4 — Creatures
The 12 creature tables.
- Fixes: missing or misplaced roll numbers in Beasts, Undead, Lab Horrors, Ghosts.
- Depends on: R1.

#### [ ] R5 — Places
The 14 place tables, Special Events, Children's Stuff.
- Fixes: missing or misplaced roll numbers in House, Clinic, Street.
- Depends on: R1.

#### [ ] R6 — Events
The 42 numbered events.
- Fixes: body text parsed as headings in `6_unique_events.md`.
- Depends on: R1.

#### [ ] R7 — The rest
Random Books, Random Magic Items, Rewards, Side Missions.
- Fixes: Random Magic Items (missing roll numbers).
- Depends on: R1.

Housekeeping, any time:

- [ ] Repair `0_table_of_content.md`
- [ ] Remove or complete stub files (`gameRules/Readme.md`, `2_0_tables.md`), rename `7__optional_rules.md`
- [ ] Fix merged rows in the random skill tables (optional rule, after the MVP)

### Milestone 4 — Project setup

- [x] Fix `.tool-versions` (now pins Python 3.14.2, the installed version)
- [x] Add a `.gitignore` (original rulebook files, virtualenvs, caches)
- [x] Write `CLAUDE.md` with established facts and conventions; extend it as decisions are made
- [x] Configure `.claude/settings.json` permissions (added by hand: an agent cannot edit its own permissions)
- [x] Bootstrap the Python project with common defaults: `pyproject.toml`, src layout, pytest, ruff, CI
- [x] GitHub issues: only for user stories and bugs, and only when needed (decided in the E1 and E2 session). Engine tasks with no user story get none: the Readme stays the source of truth, the PR and the session log record the work.

### Milestone 5 — Engine skeleton

A whole game playable in book mode with nothing written yet: the engine keeps the state, the map and the time, and shows the text of every entry reached. Every later task replaces part of book mode and can be tried in the game straight away.

#### [x] E1 — Dice
d3, d6, d6±n, 2d6, d6×d6, d66, "x in 6" chances. Seedable for reproducible tests. A roll result keeps the natural die as well as the total.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Dice Codes)
- Done when: every dice code is unit tested.
- Depends on: Milestone 4.

#### [x] E2 — Game state
The campaign, character and mission levels and what each remembers: the map and its boxes, the box counter, the history (played, found, killed, keywords). For now the character holds plain numbers (Life, Sanity, Food, XP, Clues) and a list of named items. The state refers to content by ID and never holds code, so saving stays easy to add.
- Design: [encounters](design/encounters.md#what-the-game-remembers), [game flow](design/game-flow.md)
- Done when: the state can be built, queried and changed through the engine API, with tests.
- Depends on: E1.

#### [x] E3 — Town map, moves and time
A grid of boxes made of 5×6 sheets; Home in any box of the first sheet; neighbours including diagonals; distance; a new sheet once one is full; every move numbers the box entered; 1 Food every 5 boxes or lose 1 Life; what a box remembers (visited, Searched, places, marks).
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Movement and Mapping), [game overview](gameRules/9_game_overview.md)
- Design: [town map](design/town-map.md)
- Done when: moves, numbering, distance, sheets and Food are unit tested.
- Depends on: E2.

#### [x] E4 — Engine/interface protocol and game loop
The engine asks, the interface answers: every choice is a request, so the engine never reads input or prints. The turn loop: move, arrive, Search, free actions; it ends at death, insanity or when the player quits. A scripted interface plays games in tests; a minimal terminal interface shows the map, the character and the requests.
- Design: [game flow](design/game-flow.md)
- Done when: a scripted test walks 10 boxes, and the terminal lets a player do the same.
- Depends on: E3.

#### [x] E5a — Book mode: reading
Load the YAML by ID; roll a table's dice and show only the entry reached, with the notes it points to; a catalogued table points to its Markdown file and entry number. Arriving: a new box rolls Town Exploration, a visited box has a 1 in 6 Random Encounter. Go to a table or event (the entry's references are offered). Record what was reached. When every box of a sheet is visited, the player can attach a new sheet and walk onto it.
- Design: [MVP scope](design/mvp-scope.md#book-mode), [town map](design/town-map.md)
- Decided: the interface shows a table's own rules; the terminal shows them the first time the table is rolled in a game, and again on request. The 42 numbered events are catalogued (`event.12`) so they can be played and recorded before R6.
- Done when: a player can walk the town in the terminal, every box's entry shown as text, and walk onto a new sheet once the first is full.
- Depends on: E4, R1.

#### [ ] E5b — Book mode: manual actions
Manual actions that go through the rules: gain or lose Life, Sanity, Food, XP or Clues; add or remove an item; make a roll vs L (modifier typed by the player until E7); make a Search roll; mark a Safe House. New request shapes as these actions need them (an amount, an item name, a roll). The turn ends as soon as Life or Sanity reaches 0, once effects have resolved. Fights are applied by hand until E12.
- Design: [MVP scope](design/mvp-scope.md#book-mode)
- Done when: a player can walk the town in the terminal, every box shown as text and applied with manual actions, until death or quitting.
- Depends on: E5a.

Any time:

- [ ] Attach a sheet by stepping onto it: once a sheet is full, moves also offer the boxes across its edges, and stepping onto one attaches its sheet (replaces the "attach a new sheet" action of E5a; smoother to play). A small task of its own, in its own PR.

### Milestone 6 — Step 1: Bring Home the Bacon

Each task writes an engine part together with the content that uses it.

#### [ ] E6 — Character and creation
Life and Sanity with current and max values; the 21 Skills at Basic and Expert; earning and spending XP at any time (Expert costs the Skill's cost again). Creation: 2 Skills (no Arcane, no Expert), 3 points on Life and Sanity or traded for 1 extra Skill or table roll, a random weapon and a knife, 1 Random Object and 1 Useful Stuff rerolling duplicates, d6 Food. Skill effects stay text until E7.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Your Character, Experience), [skills](gameRules/1_2_skills.md), [weapons table](gameRules/tables/1_4_random_weapons_table.md), [random objects](gameRules/tables/2_1_random_object_tables.md), [useful stuff](gameRules/tables/2_2_useful_stuff_table.md)
- Design: [character](design/character.md)
- Decides: the rest of D1.
- Open: the weapon summary entries that name two weapons ("Baseball bat or hammer", "Hockey stick/golf club", "Kitchen knife/ritual dagger", "Knife or stick", "Scythe/shovel") have one ID each, as printed (R3). Likely choice: two IDs sharing the same rule text (`weapon.baseball_bat`, `weapon.hammer`), so the player holds the exact item and a rule can tell them apart (a stake needs a hammer). Decide when creation first stores a weapon.
- Done when: the terminal walks the player through creation, and XP can be spent.
- Depends on: E5b, R2, R3.

#### [ ] E7 — Rolls and effects
Roll types and context tags; roll vs L with natural 1 and 6; effects with source, holder, kind and lifetime; a roll collects matching modifiers from every holder, with stacking limits; max values calculated from effects. Every Skill written as effects. Manual rolls in book mode now get their modifiers.
- Design: [rolls](design/rolls.md), [effects](design/effects.md), [character](design/character.md)
- Done when: every Skill's effect is tested.
- Depends on: E6.

#### [ ] E8 — Moments and reactions
Announce moments; reactions with their scripts; the lifetimes the Skills and Food need (permanent, for the next N boxes, until a moment). Food every 5 boxes becomes a reaction (Resistant to Hunger and Eating Disorder change it); "for the next N boxes" effects. The rest of the effects design comes with the content that needs it: timed steps with E10, combat scopes and the order of reactions on one moment with E12, "would" moments with E13.
- Design: [effects](design/effects.md)
- Open: the Food clock when the interval changes mid-game (the [ruling](design/rulings.md#map) eats on every multiple of 5); options at E8.
- Done when: the Food upkeep is a reaction that Resistant to Hunger and Eating Disorder change, and "for the next N boxes" effects end on time, with tests.
- Depends on: E7.

#### [ ] E9 — Inventory
Two hands; carry limit 10, +5 with a backpack, +3 / +5 with Strong, max 20; Food limit 10, 15 with a backpack, extra Food takes item slots; light items; ammo per weapon type; discarding (items left behind may vanish); stash; losing the backpack; items as effect holders. The item uses that need these (backpack, Food items, ammo).
- Rules: [encumbrance summary](gameRules/11_encumbrance_summary.md), [main rules](gameRules/1_1_main_rules.md) (Equipment), [combat](gameRules/3_combat.md) (Keep Track of Ammo)
- Design: [inventory](design/inventory.md)
- Done when: picking up, holding, discarding and stashing respect every limit, with tests.
- Depends on: E7.

#### [ ] E10 — Tables and result scripts
Results as scripts of steps: encounter, chain, choice, gate, gain or loss, effect, box mark, movement; forced and shifted results; limits and fallbacks read the history; timed steps hooked to moments; an unwritten entry goes to book mode. Town Exploration, Random Encounter and Search written.
- Rules: [town exploration](gameRules/tables/5_4_town_exploration_table.md), [random encounters](gameRules/tables/5_2_random_encounters_table.md), [search table](gameRules/tables/5_1_search_rolls_table.md)
- Design: [encounters](design/encounters.md)
- Done when: arriving in a new box plays itself until it reaches an unwritten entry.
- Depends on: E8, E9.

#### [ ] E11 — Arriving and encounters
The full arrival flow: new box, visited box, left-behind encounters. An encounter is met, then resolved or left behind; hazards and people are encounters too. Search only after dealing with the box, once per box (libraries again for 1 book or 1 Clue), natural 1 stays 1, Investigator bonus; Clues.
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Search Rolls)
- Design: [game flow](design/game-flow.md#3-arriving-in-a-box), [encounters](design/encounters.md#an-encounters-life)
- Done when: the arrival flow is tested for new, visited and left-behind boxes.
- Depends on: E10.

#### [ ] E12 — Combat
Creature profiles, groups and members; surprise; rounds; Attack with exploding sixes and hits = total ÷ L; Defense with fumbles; weapon modifiers, Damage and specials on the natural die; ammo; automatic Damage (vulnerabilities, grenade); XP and loot; end-of-combat reactions. Effects scoped to one attack, round or combat; several reactions on one moment (helpful first, then the player picks). The stats of every creature and every weapon written; special rules stay text, with manual actions open during the fight (creature Life up or down). The "fight a creature" manual action.
- Rules: [combat](gameRules/3_combat.md), [monster rules](gameRules/4_monster_rules.md), [weapons](gameRules/1_4_weapons.md), [weapon summary](gameRules/8_weapon_summary_table.md), [creatures](gameRules/tables/creatures/)
- Design: [combat](design/combat.md)
- Done when: a fight against any creature can be played, with a test on the book's worked example.
- Depends on: E11, R4.

#### [ ] E13 — Harm
Life and Sanity losses as "would" moments: armor, Luck, then the Injury or Mental Scar offer (max 3 each, duplicates rerolled, the whole loss negated), then the loss; death at 0 Life, insanity at 0 Sanity. The Injury and Insanity tables, armor, helmet and first aid kit written.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Sanity, Life), [combat](gameRules/3_combat.md) (Mental Scars and Injuries), [insanity table](gameRules/tables/3_1_insanity_table.md), [injury table](gameRules/tables/3_2_injury_table.md)
- Design: [character](design/character.md#life-and-sanity), [combat](design/combat.md#defense-and-taking-damage), [effects](design/effects.md#would-and-did)
- Open: can something that triggers after a loss bring the character back above 0 before death is checked? Leaning yes; settle it with tests and user stories.
- Done when: the Damage chain is tested in order.
- Depends on: E12.

#### [ ] E14 — Escape, Stealth and Charisma
Escape vs L (free from Slow creatures, none from Flying ones, Damage on a failure, to a visited neighbour, 1 in 6 encounter unless it is a Safe House, creatures stay behind with their wounds); Stealth to slip past or strike first, +1 L on a failure; Charisma; several groups in waves.
- Rules: [combat](gameRules/3_combat.md)
- Design: [combat](design/combat.md#escape), [rulings](design/rulings.md#combat)
- Done when: escaping and sneaking past several groups follow the rulings, with tests.
- Depends on: E13.

#### [ ] E15 — Safe Houses
Created by a result, with that result's healing; no random encounter; healing on each visit; max 3, the closest one stops being one (ties broken randomly); stash, stolen on a d6 of 1-3 when its Safe House is lost. Home is a Safe House from the start ([ruling](design/rulings.md#safe-houses), switchable).
- Design: [Safe Houses](design/safe-houses.md)
- Open: how much Home heals, and whether it counts toward the 3.
- Done when: the lifecycle is tested.
- Depends on: E11.

#### [ ] E16 — Street, Store and Farm
The three place tables of Bring Home the Bacon written; their chains to events, books and other tables stay in book mode.
- Rules: [street](gameRules/tables/places/5_5_street_table.md), [store](gameRules/tables/places/5_13_store_table.md), [farm](gameRules/tables/places/5_11_farm_table.md)
- Done when: every entry of the three tables plays itself up to an unwritten chain.
- Depends on: E14, E15, R5.

#### [ ] E17 — Missions and Bring Home the Bacon
A mission as a holder of effects, with a goal and rewards; rolled among the written missions; it ends back Home with the goal met. Bring Home the Bacon: 2d6+12 Food on top of your own, an optional backpack, a stash at Home or a Safe House, a 3 in 6 chance of d6 Food at Street, Store and Farm locations, 3 XP or 3 Useful Stuff rolls.
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Mission), [missions table](gameRules/tables/5_3_missions_table.md)
- Done when: Bring Home the Bacon can be played from creation to the end screen. **Step 1 done.**
- Depends on: E16.

### Milestone 7 — Step 2: Close a Hell Gate

#### [ ] E18 — Arcane Skills and books
Learning Arcane Skills works for all 11 (prerequisites: a book read, a Skill, Clues spent in a Hell Gate box; XP cost); Gate written, the other effects in book mode. The Random Books table; reading takes d3 boxes of time, which advances the clock without entering a box; each book once per game.
- Rules: [arcane skills](gameRules/1_3_arcane_skills.md), [random books](gameRules/tables/5_32_random_books_table.md)
- Design: [character](design/character.md#xp-and-skills), [rulings](design/rulings.md#effects)
- Done when: Gate can be learned through each of its prerequisites, with tests.
- Depends on: E17, R7.

#### [ ] E19 — Close a Hell Gate
The mission: a Hell Gate after 12+d6 new boxes and another in the 30th box if none was found. Hell Gates as box marks, also from table results (manual action: mark a Hell Gate). The closing roll; Hell Gates can be closed during any mission.
- Rules: [missions table](gameRules/tables/5_3_missions_table.md), [arcane skills](gameRules/1_3_arcane_skills.md) (Gate)
- Open: Will or Magic roll to close ([MVP scope](design/mvp-scope.md#to-decide-when-step-2-starts)).
- Done when: a Hell Gate can be found and closed, with tests.
- Depends on: E18.

#### [ ] E20 — Campaign play
Missions one after another: rewards, Life and Sanity back to max, reroll the same mission; abort at a Safe House; a new character after death or insanity continues the campaign without the previous one's Food, Clues and stash; won when the 7th Hell Gate is closed.
- Design: [game flow](design/game-flow.md#1-campaign)
- Open: a new map sheet after a mission, whether a new character keeps the map ([MVP scope](design/mvp-scope.md#to-decide-when-step-2-starts)).
- Done when: a whole campaign can be played in the terminal. **MVP done.**
- Depends on: E19.

### Later

- [ ] Design review once the MVP is done: a review session reworks `design/` against what the implementation taught. It should not be needed, but the design was written before the code.
- [ ] Save and resume the campaign. A save is the campaign as it stood at the start of the turn: a turn changes the state as it goes, so quitting mid-turn leaves it half played.
- [ ] The other missions: Predator and Prey and Destroy the Coven (with hunting by Clues), Medical Supplies, We Need Weapons
- [ ] Switchable rule options (campaign modes)
- [ ] The remaining content, each piece replacing part of book mode: place tables, events (with the forest map of #41), side missions, rewards, magic items, book effects, Arcane Skill effects
- [ ] Optional rules ([optional rules](gameRules/7__optional_rules.md)) and random Skill generation
- [ ] genAI features: narration (Claude / local LLM), image and video generation (D8)
