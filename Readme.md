# Alone Against Fear — digital solo play

A program that runs a full session of **Alone Against Fear**, a survival-horror solo tabletop game based on the Four Against Darkness engine, from character creation to the end of the mission.

The game rules are extracted from the rulebook PDF into Markdown under `gameRules/`, which serve as the reference for the engine. 

The rules text is from a commercial book: keep this repository private. The original PDFs go in `origin_rules/` at the repository root, which is git-ignored.

## Status

MVP phase. Rules extraction is done; domain design is under way in [`design/`](design/); the game engine has not been started.

**MVP goal:** play one complete mission in the terminal — create a character, roll a mission, explore the town box by box, resolve encounters, search, manage inventory, food and health, and end by completing the mission and returning home, or by dying / going insane. Campaign play (several missions with the same character) comes after the MVP, but the game state is shaped as a campaign from the start: the map, the box counter, Food and Clues carry on across missions (see [game flow](design/game-flow.md)).

## How to use this roadmap

The roadmap is split into milestones. Each `####` entry is sized to become one GitHub issue: its title, description, rules references, "Done when" and "Depends on" lines are the issue body. Check the box when it is done. Decisions are tracked as issues too, so they are made deliberately when they block work, not up front. Before deciding, ask: is it worth deciding yet, or is it a constraint we would have to fight later?

## Working with Claude

Work happens in small, planned sessions with Claude. The upcoming sessions are listed in [`NextSession.md`](NextSession.md); past sessions are summarized in [`claude-logs/`](claude-logs/).

## Decisions

### Made

- **Language:** Python. Strongest ecosystem for planned genAI features (local LLMs, image and video generation).
- **Interface:** terminal CLI first. Engine stays UI-agnostic so other front ends can be added.

### Guidelines

Former decisions that are better kept as guidelines than settled up front.

- **Tooling** (was D3) — pick common defaults when coding starts; change them freely.
- **Portability** (was D7) — keep the engine free of UI and genAI code; otherwise, rework code when a port actually happens.
- **Validation** (was D2) — tests are enough until a content format exists.
- **Saves** (was D4) — the campaign is the game state; saving a game means saving the campaign.
- **Design before code** — model the game in domain terms in [`design/`](design/) before writing engine code.

### Deferred

#### [ ] D1 — Rules content format
Start with content written as plain Python while implementing it; extract a data format only if patterns emerge. Most entries mix plain stats with unique rules, so the format must handle both without inventing a DSL.
- Decide when: the engine implements its first tables (E7).

#### [ ] D8 — genAI integration
Where narration / image generation plug in, kept optional and behind interfaces. Post-MVP, but should not be blocked by MVP architecture.

### Moved to domain design

D5 (town map layout) and D6 (MVP content scope) are design topics, see Milestone 2.

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
- [ ] MVP scope: which tables, creatures and events, and the fallback for the rest (was D6)
- [ ] Review the engine tasks below against the design

### Milestone 3 — Rules cleanup

The OCR mangled the book's two-column layout. Content is complete, but many tables are structurally damaged. If D1 converts tables to another format, fix them during conversion instead of fixing the Markdown twice.

- [ ] Fix tables with missing or misplaced roll numbers: missions, beasts, undead, lab horrors, ghosts, house, clinic, street, magic items
- [ ] Restore the nested d6→d6 structure of the random encounter table
- [ ] Fix the town exploration table (swapped columns, split rows 2 and 12)
- [ ] Fix merged rows: insanity table (2/3), random skill tables
- [ ] Fix body text parsed as headings in `6_unique_events.md`
- [ ] Replace book page references (`p. 65`) with links to the matching files
- [ ] Repair `0_table_of_content.md`
- [ ] Remove or complete stub files (`gameRules/Readme.md`, `2_0_tables.md`), rename `7__optional_rules.md`

### Milestone 4 — Project setup

- [ ] Fix `.tool-versions` (pins Python 3.14.5, not installed locally)
- [x] Add a `.gitignore` (original rulebook files, virtualenvs, caches)
- [ ] Write `CLAUDE.md` with established facts and conventions; extend it as decisions are made
- [ ] Configure `.claude/settings.json` permissions
- [ ] Bootstrap the Python project with common defaults (package layout, test run, CI optional)

### Milestone 5 — Engine MVP

To be revised once Milestone 2 is done.

#### [ ] E1 — Dice and rolls
d3, d6, d6±n, 2d6, d6×d6, d66, "x in 6" chances. Seedable for reproducible tests. Generic roll vs L with modifiers: natural 1 always fails, natural 6 always succeeds. Covers Saves, Charisma, Stealth, Escape, Magic, Strength rolls.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Dice Codes, Saves, Other Rolls)
- Done when: every dice code and the roll-vs-L rule are unit tested.

#### [ ] E2 — Character sheet
Name; Life and Sanity (8 each + 3 points to distribute, or traded for 1 extra Skill / extra table roll); current vs max values; Skills with Basic/Expert level; XP; Food; Clues; up to 3 Injuries and 3 Mental Scars; death at 0 Life, insanity at 0 Sanity.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Your Character, Sanity, Life, Food, Experience), [skills](gameRules/1_2_skills.md)
- Done when: a character can be built and its state queried and modified through the engine API, with tests.
- Depends on: E1.

#### [ ] E3 — Inventory and encumbrance
Two hands (one two-handed weapon uses both); 10 carried items; Food carried separately (10, extra Food takes item slots); negligible-weight items; +5 with backpack (losing it drops everything not in hand), +3 / +5 with Strong / Strong (Expert), hard max 20. Ammo tracked per weapon type (bullets, rifle bullets, bolts, arrows, shells). Stash and retrieve items at a Safe House.
- Rules: [encumbrance summary](gameRules/11_encumbrance_summary.md), [main rules](gameRules/1_1_main_rules.md) (Equipment), [combat](gameRules/3_combat.md) (Keep Track of Ammo)
- Done when: picking up, equipping, discarding and stashing respect every limit, with tests.
- Depends on: E2.

#### [ ] E4 — Character creation
Choose 2 Skills (no Arcane Skills, no Expert) or roll them randomly; distribute 3 points; 1 random weapon + 1 knife; 1 Random Object + 1 Useful Stuff item, rerolling duplicates; d6 starting Food.
- Rules: [main rules](gameRules/1_1_main_rules.md), [random skill generation](gameRules/10_optional_skills_generation.md), [weapons table](gameRules/tables/1_4_random_weapons_table.md), [random objects](gameRules/tables/2_1_random_object_tables.md), [useful stuff](gameRules/tables/2_2_useful_stuff_table.md)
- Done when: the CLI walks the player through creation and produces a valid character.
- Depends on: E2, E3, related Milestone 3 table fixes.

#### [ ] E5 — Mission
Roll d6 on the Mission table at session start; track mission progress and completion conditions; mission ends on returning Home with the goal met.
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Mission), [missions table](gameRules/tables/5_3_missions_table.md)
- Depends on: E2, missions table fix.

#### [ ] E6 — Town map, movement and time
Grid of boxes per the [town map design](design/town-map.md); start in any box; move to any neighbour including diagonals; number each box entered (time counter, ~2 hours per box); consume 1 Food every 5 boxes or lose 1 Life; effects lasting N boxes; annotate box content, Searched flag, occupied boxes (monsters you fled from), Safe Houses (max 3 in play).
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Movement and Mapping, Moving Through Visited Areas), [game overview](gameRules/9_game_overview.md)
- Depends on: town map design, E2.

#### [ ] E7 — Exploration and encounter tables
New box: roll on the Town Exploration table (2d6) then the place sub-table; no roll for the first box. Visited box: 1 in 6 random encounter (nested d6→d6 table); occupied box requires a Stealth roll. Safe House: no encounter, heal Life/Sanity. Generic table-resolution mechanism shared by all tables.
- Rules: [town exploration](gameRules/tables/5_4_town_exploration_table.md), [random encounters](gameRules/tables/5_2_random_encounters_table.md), [places](gameRules/tables/places/), [creatures](gameRules/tables/creatures/), [special events](gameRules/tables/5_19_special_events_table.md)
- Depends on: D1, MVP scope, E6, Milestone 3 table fixes.

#### [ ] E8 — Combat
Surprise (x in 6, reduced by Danger Sense); player attacks first otherwise; damage = attack total / L rounded down; groups of 1-Life monsters; monster turns as Defense rolls; weapon modifiers and Damage; exploding sixes; ammo consumption; vulnerabilities (2 Damage per use) and exorcism; XP on victory only; loot.
- Rules: [combat](gameRules/3_combat.md), [monster rules](gameRules/4_monster_rules.md), [weapons](gameRules/1_4_weapons.md), [weapon summary](gameRules/8_weapon_summary_table.md)
- Depends on: E1, E2, E3.

#### [ ] E9 — Escape, stealth and charisma
Escape rolls vs L (auto-escape from Slow monsters, failures take Damage, retreat to a visited neighbour then 1 in 6 encounter, monsters stay in the box at +1 L). Stealth rolls to slip past. Charisma rolls to negotiate (failure gives -1 to first Attack).
- Rules: [combat](gameRules/3_combat.md)
- Depends on: E6, E8.

#### [ ] E10 — Search, clues and hunting
One Search per box (not in Safe Houses; libraries repeatable for 1 book or 1 Clue); Investigator bonus, natural 1 stays 1; Clues; hunting a specific creature by spending Clues equal to its L (minus Investigator, min 1).
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Search Rolls, Hunting), [search table](gameRules/tables/5_1_search_rolls_table.md)
- Depends on: E6, E3.

#### [ ] E11 — Sanity, injuries and mental scars
Optionally negate a loss by rolling on the Insanity or Injury table (max 3 each, reroll duplicates); apply the permanent effects as modifiers; end the game at 0 Life or 0 Sanity.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Sanity, Life), [combat](gameRules/3_combat.md) (Mental Scars and Injuries), [insanity table](gameRules/tables/3_1_insanity_table.md), [injury table](gameRules/tables/3_2_injury_table.md)
- Depends on: E2, insanity table fix.

#### [ ] E12 — Unique events
Numbered events triggered by tables, with player choices, chained events and persistent effects. Scope per the MVP scope design.
- Rules: [unique events](gameRules/6_unique_events.md)
- Depends on: MVP scope, E7, events headings fix.

#### [ ] E13 — Terminal game loop
Ties everything together: creation → mission → move/explore/resolve/search loop → end screen (mission complete and back Home, death or insanity). Displays character sheet, inventory and map on demand. Save/resume of the campaign state.
- Rules: [game overview](gameRules/9_game_overview.md)
- Done when: a full mission can be played from start to finish in the terminal.
- Depends on: E4–E12.

### Later

- [ ] Campaign play: persisting character between missions (Life/Sanity restored, Injuries/Scars/XP/equipment kept), closing 7 Hell Gates to win, new character after death
- [ ] Spending XP on Skills and Expert levels; Arcane Skills and spells
- [ ] Side missions, rewards, books, magic items beyond MVP scope
- [ ] Optional rules ([optional rules](gameRules/7__optional_rules.md))
- [ ] genAI features: narration (Claude / local LLM), image and video generation (D8)
