# Alone Against Fear — digital solo play

A program that runs a full session of **Alone Against Fear**, a survival-horror solo tabletop game based on the Four Against Darkness engine, from character creation to the end of the mission.

The game rules are extracted from the rulebook PDF into Markdown under `gameRules/`, which serve as the reference for the engine. 

The rules text is from a commercial book: keep this repository private.

## Status

MVP phase. Rules extraction is mostly done; the game engine has not been started.

**MVP goal:** play one complete mission in the terminal — create a character, roll a mission, explore the town box by box, resolve encounters, search, manage inventory, food and health, and end by completing the mission and returning home, or by dying / going insane. Campaign play (several missions with the same character) comes after the MVP.

## How to use this roadmap

The roadmap is split into milestones. Each `####` entry is sized to become one GitHub issue: its title, description, rules references, "Done when" and "Depends on" lines are the issue body. Check the box when it is done. Decisions are tracked as issues too, so they are made deliberately when they block work, not up front.

## Working with Claude

Work happens in small, planned sessions with Claude. The upcoming sessions are listed in [`NextSession.md`](NextSession.md); past sessions are summarized in [`claude-logs/`](claude-logs/).

## Decisions

### Made

- **Language:** Python. Strongest ecosystem for planned genAI features (local LLMs, image and video generation).
- **Interface:** terminal CLI first. Engine stays UI-agnostic so other front ends can be added.

### To decide

#### [ ] D1 — Rules content format
Data files (YAML / TOML / JSON) + Python code for special rules, or content written directly as typed Python. Most entries mix plain stats with unique rules (e.g. "bullets bounce off on 1-2"), so the format must handle both without inventing a DSL.
- Done when: a spike in a worktree implements the Beasts table, the House table and event #4 The Fluid in the candidate formats, and one is chosen.
- Depends on: D3.

#### [ ] D2 — Validation
Schema for rules content and structural checks: d6 tables have 6 entries, 2d6 tables cover 2–12, d66 tables cover 11–66, cross-references resolve.
- Depends on: D1.

#### [ ] D3 — Python tooling
Package manager, linter/formatter, type checker, test runner.

#### [ ] D4 — Game state and saves
How a session is represented and saved (save/resume mid-mission). Should anticipate campaign persistence without implementing it.

#### [ ] D5 — Town map layout
The town map sheet is an image in the PDF ("a chart with 30 boxes", diagonal moves allowed). Decide the grid shape and how extra sheets attach once all boxes are visited.

#### [ ] D6 — MVP content scope
Which tables, creatures and unique events are implemented for the MVP, and the fallback for unimplemented ones (e.g. an unimplemented event becomes a roll on the Random Encounter table).

#### [ ] D7 — Portability constraints
How strictly the engine stays portable (e.g. to DragonRuby): plain data structures, no metaprogramming, UI and genAI isolated.

#### [ ] D8 — genAI integration
Where narration / image generation plug in, kept optional and behind interfaces. Post-MVP, but should not be blocked by MVP architecture.

## Roadmap

### Milestone 1 — Rules extraction

- [x] Parse the rulebook PDF (`gameRules/extractor/`)
- [x] Split parsed output into sections: global rules, rolling tables, how the game works, game overview, random skill generation
- [ ] Character sheet (image in the PDF, needs manual transcription)
- [ ] Town map sheet (image in the PDF, needs manual transcription) — feeds D5
- [ ] Pregenerated characters (image in the PDF, needs manual transcription)

### Milestone 2 — Rules cleanup

The OCR mangled the book's two-column layout. Content is complete, but many tables are structurally damaged. If D1 converts tables to another format, fix them during conversion instead of fixing the Markdown twice.

- [ ] Fix tables with missing or misplaced roll numbers: missions, beasts, undead, lab horrors, ghosts, house, clinic, street, magic items
- [ ] Restore the nested d6→d6 structure of the random encounter table
- [ ] Fix the town exploration table (swapped columns, split rows 2 and 12)
- [ ] Fix merged rows: insanity table (2/3), random skill tables
- [ ] Fix body text parsed as headings in `6_unique_events.md`
- [ ] Replace book page references (`p. 65`) with links to the matching files
- [ ] Repair `0_table_of_content.md`
- [ ] Remove or complete stub files (`gameRules/Readme.md`, `2_0_tables.md`), rename `7__optional_rules.md`

### Milestone 3 — Project setup

- [ ] Fix `.tool-versions` (pins Python 3.14.5, not installed locally)
- [ ] Add a `.gitignore` (PDF, virtualenvs, caches)
- [ ] Write `CLAUDE.md` with established facts and conventions; extend it as decisions are made
- [ ] Configure `.claude/settings.json` permissions
- [ ] Bootstrap the Python project per D3 (package layout, test run, CI optional)

### Milestone 4 — Engine MVP

#### [ ] E1 — Dice and rolls
d3, d6, d6±n, 2d6, d6×d6, d66, "x in 6" chances. Seedable for reproducible tests. Generic roll vs L with modifiers: natural 1 always fails, natural 6 always succeeds. Covers Saves, Charisma, Stealth, Escape, Magic, Strength rolls.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Dice Codes, Saves, Other Rolls)
- Done when: every dice code and the roll-vs-L rule are unit tested.

#### [ ] E2 — Character sheet
Name; Life and Sanity (8 each + 3 points to distribute, or traded for 1 extra Skill / extra table roll); current vs max values; Skills with Basic/Expert level; XP; Food; Clues; up to 3 Injuries and 3 Mental Scars; death at 0 Life, insanity at 0 Sanity.
- Rules: [main rules](gameRules/1_1_main_rules.md) (Your Character, Sanity, Life, Food, Experience), [skills](gameRules/1_2_skills.md)
- Done when: a character can be built and its state queried and modified through the engine API, with tests.
- Depends on: E1, D1.

#### [ ] E3 — Inventory and encumbrance
Two hands (one two-handed weapon uses both); 10 carried items; Food carried separately (10, extra Food takes item slots); negligible-weight items; +5 with backpack (losing it drops everything not in hand), +3 / +5 with Strong / Strong (Expert), hard max 20. Ammo tracked per weapon type (bullets, rifle bullets, bolts, arrows, shells). Stash and retrieve items at a Safe House.
- Rules: [encumbrance summary](gameRules/11_encumbrance_summary.md), [main rules](gameRules/1_1_main_rules.md) (Equipment), [combat](gameRules/3_combat.md) (Keep Track of Ammo)
- Done when: picking up, equipping, discarding and stashing respect every limit, with tests.
- Depends on: E2.

#### [ ] E4 — Character creation
Choose 2 Skills (no Arcane Skills, no Expert) or roll them randomly; distribute 3 points; 1 random weapon + 1 knife; 1 Random Object + 1 Useful Stuff item, rerolling duplicates; d6 starting Food.
- Rules: [main rules](gameRules/1_1_main_rules.md), [random skill generation](gameRules/10_optional_skills_generation.md), [weapons table](gameRules/tables/1_4_random_weapons_table.md), [random objects](gameRules/tables/2_1_random_object_tables.md), [useful stuff](gameRules/tables/2_2_useful_stuff_table.md)
- Done when: the CLI walks the player through creation and produces a valid character.
- Depends on: E2, E3, related Milestone 2 table fixes.

#### [ ] E5 — Mission
Roll d6 on the Mission table at session start; track mission progress and completion conditions; mission ends on returning Home with the goal met.
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Mission), [missions table](gameRules/tables/5_3_missions_table.md)
- Depends on: E2, missions table fix.

#### [ ] E6 — Town map, movement and time
Grid of boxes per D5; start in any box; move to any neighbour including diagonals; number each box entered (time counter, ~2 hours per box); consume 1 Food every 5 boxes or lose 1 Life; effects lasting N boxes; annotate box content, Searched flag, occupied boxes (monsters you fled from), Safe Houses (max 3 in play).
- Rules: [how the game works](gameRules/5_how_the_game_works.md) (Movement and Mapping, Moving Through Visited Areas), [game overview](gameRules/9_game_overview.md)
- Depends on: D5, E2.

#### [ ] E7 — Exploration and encounter tables
New box: roll on the Town Exploration table (2d6) then the place sub-table; no roll for the first box. Visited box: 1 in 6 random encounter (nested d6→d6 table); occupied box requires a Stealth roll. Safe House: no encounter, heal Life/Sanity. Generic table-resolution mechanism shared by all tables.
- Rules: [town exploration](gameRules/tables/5_4_town_exploration_table.md), [random encounters](gameRules/tables/5_2_random_encounters_table.md), [places](gameRules/tables/places/), [creatures](gameRules/tables/creatures/), [special events](gameRules/tables/5_19_special_events_table.md)
- Depends on: D1, D6, E6, Milestone 2 table fixes.

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
Numbered events triggered by tables, with player choices, chained events and persistent effects. Scope per D6.
- Rules: [unique events](gameRules/6_unique_events.md)
- Depends on: D6, E7, events headings fix.

#### [ ] E13 — Terminal game loop
Ties everything together: creation → mission → move/explore/resolve/search loop → end screen (mission complete and back Home, death or insanity). Displays character sheet, inventory and map on demand. Save/resume per D4.
- Rules: [game overview](gameRules/9_game_overview.md)
- Done when: a full mission can be played from start to finish in the terminal.
- Depends on: E4–E12, D4.

### Later

- [ ] Campaign play: persisting character between missions (Life/Sanity restored, Injuries/Scars/XP/equipment kept), closing 7 Hell Gates to win, new character after death
- [ ] Spending XP on Skills and Expert levels; Arcane Skills and spells
- [ ] Side missions, rewards, books, magic items beyond MVP scope
- [ ] Optional rules ([optional rules](gameRules/7__optional_rules.md))
- [ ] genAI features: narration (Claude / local LLM), image and video generation (D8)
