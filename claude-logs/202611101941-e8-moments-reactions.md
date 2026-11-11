# E8: Moments and reactions

- Date: 2026-11-10 to 2026-11-11
- Session ID: b62d3226-f74d-406b-b3ce-fb8be39ab59a (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `e8-moments-reactions` (the PR is found from it)
- Model: Opus 5.5, high effort
- Transcript: [transcripts/202611101941-e8-moments-reactions.txt](transcripts/202611101941-e8-moments-reactions.txt)

## Goal

E8: announce moments; reactions; the lifetimes the Skills and Food need. The Food upkeep becomes a reaction that Resistant to Hunger and Eating Disorder change; "for the next N boxes" effects.

Done when: the Food upkeep is a reaction that Resistant to Hunger and Eating Disorder change, and "for the next N boxes" effects end on time, with tests. Met.

Then, at the user's request before the wrap-up: how to test the game as a player, early and in short runs (drills, playtests).

## Done

- **Rulings and design** (commit 1): the Food clock, the overdue meal, Eating Disorder with Resistant to Hunger, "for the next N boxes", "all your die rolls" (see Decisions). `design/effects.md` gets "until a moment" as a count of 1 and how a moment is announced; `design/mvp-scope.md` the new manual action. The reminders on the harm tables' text move from E8 to E13 (YAML comments, `book_errors.md`).
- **Injuries and Mental Scars held as effects** (commit 2): the character holds them by entry ID (`gain_injury`, `gain_mental_scar`, duplicates refused); a table entry may carry `effects` with a single `amount`; Eating Disorder is `{parameter: food_interval, amount: -2}`; the interval is never below 1. The terminal lists them and can name one as a modifier's source. Only Eating Disorder's effect is written; E13 writes the others.
- **Moments, reactions, lasting effects, Food upkeep** (commit 3): `engine/moments.py` (`announce`: reactions, then lifetimes counted down, each end told); one moment, a box of time, announced by the loop after the arrival; the Food upkeep is its rule reaction, told as `FoodUpkeep`. `campaign.last_meal` and `Game.next_meal()`. `Lasting` effects on the character (`add_lasting`, `remove_lasting`, `ends_at`, `count_down`); an effect with no roll type changes every roll, the Search included. The Food tests moved from `test_town_map.py` to the new `test_moments.py`.
- **Lasting effects by hand, on screen** (commit 4): the manual action "add a lasting effect" (`f`: every roll or one roll type, the modifier, the boxes, Enter for until removed) and "remove a lasting effect" (`u`). The status line shows the next meal and the lasting effects with the box that ends them. Tried in a scripted terminal session: the meal came on entering box 3 with Eating Disorder, the effect ended on entering box 4.
- Four commits, each tested on its own, committed by Claude as the user asked for this session. 843 pass, 10 skipped, ruff clean.
- **Testing as a player** (the wrap-up): drills (T1, then one per task), playtests P1 and P2, written in the Readme, NextSession and WorkingWithClaude (see Decisions).
- **Drift check**: the E8 pending test dropped (covered by the new tests), the town map tests' docstring, the game flow diagram, the Readme's How to play and status, NextSession reminders; two lines added under "For the next review".

## Decisions

- **Moments are announced at loop level** (the user): `moments.announce(game, interface, moment)`, like book mode, so a reaction can tell and later ask the player (Luck, a script's choice). Rejected: inside `Game`, returning outcomes (simpler now, reworked when the first reaction asks). The user asked what moments and reactions are, with examples, and what each option changes in play, before choosing.
- **The Food clock counts from the last meal** (the user): the next meal is the last one plus the interval read now, so a change applies to the interval already running (ate at 20, Resistant to Hunger at 22: next at 26). Rejected: multiples of the interval (learning the Skill could make you eat sooner), a countdown set at each meal (a change waits for the next meal).
- **An overdue meal comes at the next box of time** (the user, switchable): ate at 20, Eating Disorder in box 24, the meal comes on entering 25; only one is owed. Considered and recorded in the ruling at the user's request: eating at once, mid-encounter.
- **Eating Disorder is -2 and stacks with Resistant to Hunger** (the user, switchable): 3, 4 with the Skill, 5 at Expert, like the other Injuries and Scars that stack with Skills. An online search found no answer (the designer's answers thread on BoardGameGeek refuses automated reading; the user pasted it, and it was already in `creator-answers.md`). The user suggested a general switch, "Injuries and Scars override Skills"; held back because Eating Disorder is the only entry that sets a value, and the switch would also flip the plain -1s; the ruling notes to consider it if E13 finds more.
- **"For the next N boxes" starts at the next box** (the user): painkillers taken in box 10 hold through 13 and end as 14 starts.
- **"All your die rolls" are the rolls vs L and the Search** (the user), never a table roll.
- **Injuries and Mental Scars are held by ID now** (the user), with their entries' `effects`; how they are offered stays E13's. Rejected: Eating Disorder as a permanent lasting effect (E13 would redo it).
- **The manual action "add a lasting effect"** (the user, after an example of notes against the engine's bookkeeping): narrow, a modifier on every roll or one roll type, for N boxes or until removed. The user asked for the active lasting effects on screen, and for the next meal shown if cheap and easy to remove (one function in the terminal).
- **The harm tables' text goes to E13** (the user, after a second explanation): the ruling between the two passages was already made; E13 checks the tables' text follows it ("negates all Damage from a single attack", the whole Sanity loss).
- **Home's ruling and the creator answer**: found in the E5a transcript; the user chose Home as a Safe House for role play, but the options then did not cite the creator's answer that the starting space is not one. The decision stands; the ruling's wording goes to V1 (NextSession).
- **Commits by Claude for this session** (the user): the split of four was agreed; each commit was made, then presented with "committed as".
- **Drills and playtests** (the user's idea, shaped together): drills are short scoped runs to play in a break (`--drill NAME`, a start set up through the engine, a natural end, no rule changes); T1 builds the mechanism with `creation`, `walk`, `lasting` and `xp` (the user added the last two) and a way to write feedback while playing; each later task's Done-when includes its drill (`inventory`, `fight`, `harm`, `escape`, `safe-house`); E17 adds the quick run (a pregenerated character, Bring Home the Bacon for d6+2 Food, a campaign option marked as not the book's rules). P1 after E17 and P2 after E20 are playtests before V3 and V4; the V reviews also triage the drill feedback. T1 on Opus (the user: no need to stick to Sonnet), medium effort.

- **`/start`** (the user): a project skill, `.claude/skills/start/SKILL.md`, starts the planned session (or `/start E9`): it reads the plan, the roadmap entry, the latest log and the matching prompt template, checks `main`, the previous PR and the model, gives a plain-words summary (where we are, the goal and Done when, how it will go, before we start) and waits for the go. `CLAUDE.md` asks for that summary however a session starts. No built-in command is named `/start`.

## Open questions

- T1: the feedback format and where it is kept; how each drill ends.
- P1: whether log replay is needed to reproduce what the playtest finds.
- E13: whether more Scars or Injuries set a value a Skill changes, which would argue for one general switch.

## Next

T1 (drills and feedback), Opus, medium effort. Then E9 with its drill, then V1.
