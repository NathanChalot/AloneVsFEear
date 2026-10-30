# Encounters and tables

How the content of a box is produced: tables, the results they give, how results chain, and what the game must remember afterwards. Words are defined in the [glossary](glossary.md). Sources: `5_how_the_game_works.md`, the tables under `gameRules/tables/`, `6_unique_events.md`. Interpretations go to [rulings](rulings.md); points still to decide are listed at the end.

## The table web

Which tables and events lead to which. Simplified: creature tables, item tables and most events are grouped.

```mermaid
flowchart LR
    explore[Town Exploration 2d6]
    random[Random Encounter d6→d6]
    search[Search d6]
    special[Special Events]

    subgraph places [Place tables]
        street[Street]
        house[House]
        haunted[Haunted House]
        clinic[Clinic]
        worship[Place of Worship]
        other[Cemetery, Military/Lab, Farm,<br/>Store, Sewers, Railways,<br/>School, Woods/Park]
    end

    creatures[Creature tables<br/>Beasts, Undead, Slashers…]
    events[Numbered events]
    items[Item tables<br/>Random Objects, Useful Stuff,<br/>Books, Magic Items, Children's Stuff]
    rewards[Rewards, Side Missions]

    explore -- 2 --> random
    explore -- "3-12, some your choice" --> places
    explore -- "7, then 6 on d6" --> special
    explore -.-> house
    house --> haunted
    clinic --> haunted
    places --> creatures
    places --> random
    places --> events
    places --> items
    places --> rewards
    random --> creatures
    search -- 1 --> random
    search -- 6 --> items
    special --> events
    special -- all played --> house
    creatures --> events
    events --> events
    events --> creatures
    events --> items
```

- The content is a **graph, not a tree**: Haunted House is reached from House, Clinic and Flauros' deal; Random Encounter from Town Exploration, Search, Street; events call events.
- Some results **choose between tables** ("Store or Street, your choice"), or **roll to pick a table** (Railways 3: "1 Undead, 2 Beasts, 3-4 Slashers…").
- **Read only what applies**: "Whenever possible, do NOT read the content of the tables in advance. Read them only when they apply to you" (`5_4_town_exploration_table.md`). The engine reveals a text only when it is reached.

## Picking a result

A result is not always rolled. Missions, side missions and events can force it, shift it, or replace the roll.

```mermaid
flowchart TD
    start([A table applies]) --> forced{Something forces the result?}
    forced -- "yes: mission or event" --> use
    forced -- no --> roll[Roll the table's dice<br/>sometimes several times, then pick one]
    roll --> shift{Shift allowed?<br/>±1 if it reaches what a mission needs}
    shift -- player shifts --> shifted[Use the shifted result]
    shift -- no --> check
    shifted --> check{Result available?}
    check -- yes --> use([Use the result])
    check -- "already played, killed, found" --> fallback{Fallback written?}
    fallback -- reroll --> roll
    fallback -- "another table or result" --> use
    fallback -- "nothing happens" --> none([No encounter])
```

- **Forced**: "the last box you visit will be a clinic" (Medical Supplies), "you can automatically get result 1 on the Railways table" (#32), a witch met by spending Clues (Destroy the Coven), a Hell Gate after 12+d6 new boxes (Close a Hell Gate). Hunting also replaces the box content.
- **Shifted**: ±1 on Town Exploration or an encounter table if it reaches the place or creature a side mission needs (`5_34_side_missions_table.md`), ±1 on Town Exploration to reach a Military Installation or Store (We Need Weapons).
- **Several rolls, pick one**: Search 6 ("roll 4 times… pick a single result"), Military 1 ("roll twice… choose the best"), Destroy the Coven reward ("roll three times and pick the best").

## What a result is made of

A result is a short script: steps in text order, some guarded, some offering choices. The building blocks found in the tables and events:

- **Encounter** — creatures (one or more groups), a hazard (a Save or a Defense roll), or people (helpful farmers, a priest, survivors, a shooter).
- **Chain** — roll another table, play event #N, or roll to pick a table.
- **Choice** — between tables, between outcomes, take it or leave it, explore or move along, fight or ignore.
- **Gate** — a step happens only on a chance (x in 6), if you own an item, Skill or keyword, depending on history (already played, killed, found), or up to a count (after played twice).
- **Gain or loss** — Life, Sanity, Food, XP, Clues, items, ammo, books, Skills, permanent stats.
- **Effect** — for N boxes or N encounters, until a condition (curses), permanent, a keyword on the play sheet, or deferred ("write down #25, read it later").
- **Box mark** — Safe House, Hell Gate, deconsecrated church, unique location (Rosen House).
- **Movement** — a forced move (#16, #42) or a separate map (#41 forest).
- **Mission** — a side mission given, mission progress (a dose found).

- **Encounters are not only creatures.** A falling debris Save, a warning shot, helpful farmers and a ghost asking for a ticket are encounters too.
- **Gates read the whole game**: the inventory (a jar, a train ticket, a shovel), Skills (Gate Arcane Skill), keywords (CLOWNFACE, SNOWY), history (event #10 "already played during this mission", Slashers killed in the campaign), and even what was read (the Necronomicon for #38).
- **Keywords are campaign flags** written on the play sheet: CLOWNFACE (Children's Stuff 5, checked by Railways 1), SNOWY (#23, checked by Demonic Horrors to play #42).

## Resolving a result

```mermaid
flowchart TD
    start([Result reached]) --> reveal[Reveal its text]
    reveal --> step{Next step}
    step --> guard{Guard passes?<br/>chance, item, history}
    guard -- no --> step
    guard -- yes --> kind{Step kind}
    kind -- choice --> ask[Ask the player] --> step
    kind -- "gain, loss, effect, box mark" --> apply[Apply] --> step
    kind -- chain --> sub[[Resolve the chained result<br/>in the same box]] --> step
    kind -- encounter --> enc[[Encounter]] --> step
    step -- no more steps --> later{Steps timed later?<br/>as you leave, as soon as you pick up}
    later -- yes --> wait[Hook them to that moment]
    later -- no --> done
    wait --> done([Box outcome<br/>Search allowed or not])
```

- **Steps run in text order**, unless a timing word moves them: "As you leave, the farm is attacked" (Farm 3), "When you leave, you are attacked" (Haunted House 3), "a random encounter that will happen as soon as you pick up any objects" (Store 6), "After rolling for encounters, you have a 2 in 6 chance of finding a sketchbook" (School 5).
- **A guard can depend on a choice**: the Food store's 3 in 6 encounter happens only "if you do so" (pick up Food), the bookstore's only "if you roll to find any books".
- **A chained result stays in the same box.** Its encounter is the box's encounter: what was fled there decides the Search.
- **Some steps loop**: climb until you get the object (Special Events 3), Save "until you break free" (#31), take down each corpse (Woods 6).
- **Search can be part of a result**: two Search rolls in the Psychiatric Ward (Clinic 5), a Search at +1 after the collapse (House 5), a Search with its own loot list (Farm 2). Search rolling a 1 starts a random encounter.

## An encounter's life

```mermaid
stateDiagram-v2
    [*] --> Met
    Met --> Resolved: defeated, negotiated,<br/>avoided by item or Skill,<br/>hazard survived
    Met --> LeftBehind: fled
    Met --> LeftBehind: ignored, moved along,<br/>the place stays to explore later
    LeftBehind --> SneakedPast: back in the box,<br/>Stealth succeeds
    SneakedPast --> LeftBehind: leave the box
    LeftBehind --> Met: back in the box,<br/>Stealth fails or no sneaking
    SneakedPast --> Met: choose to strike
    Resolved --> [*]
```

- A left-behind encounter keeps its full text: "If you avoid an encounter the text still applies and the monsters are still there" ([creator answers](creator-answers.md)). The zombies guarding the grenades: "The zombies (and the grenades) remain in the area if you leave" (Military 4).
- Some encounters have their own return rule instead: the cultists of the Desecrated Church ("Every time you come back to the church, roll a 2 in 6 chance that they are still there", #2), the sewer survivors (pay 1 Food or roll for the rats, #11).
- Some encounters cannot be left behind: Flying creatures and "You may not escape" (Eliza, Snowy Samuel, Pumpkin Head Demon).
- Search: "If you flee from an encounter, you may NOT Search that area" (`5_4_town_exploration_table.md`). Ignoring and moving along block the Search too ([rulings](rulings.md)).

## Things that run out

Many results can only happen a limited number of times. The limit is usually written **where the result is referenced**, not on the event itself: Street 6 says "Play event #3. If you already played that, roll on the Random Encounter table".

```mermaid
stateDiagram-v2
    [*] --> Available
    Available --> Available: played, if repeatable
    Available --> Used: played, found, killed<br/>or limit reached
    Used --> Available: new mission,<br/>if the limit is per mission
    Used --> [*]: reached again → reroll or fallback
```

| Content | Limit | Scope | When reached again | Source |
| --- | --- | --- | --- | --- |
| Special Events | once | campaign ("in the game") | reroll; all played → House | `5_19_special_events_table.md` |
| Slashers | until killed | campaign | reroll; all killed → no encounter (table text: "count it as a no encounter") | `5_2`, `5_24` |
| Unique Vampires, Unique Zombies | until killed | campaign | reroll; all killed → no encounter | `5_2_random_encounters_table.md` |
| Good Doctor (#29) | until killed | campaign | Unique Zombies table | `6_unique_events.md` |
| Pighead (#5) | until killed | campaign | ignore the event | `6_unique_events.md` |
| Rosen House | once | campaign | reroll; location stays on the map | Haunted House 4 |
| Children's Stuff | once each | mission | reroll; all found → Useful Stuff or Random Object | `5_17_childrens_stuff_table.md` |
| Fluid needle | once | mission | reroll | Military 5 |
| Events #9, #10 | once | mission | keep moving / Beasts | Farm 4, Farm 6 |
| Werewolf, Hangman's Tree | twice | campaign ("in a game") | Beasts | Woods 1, 6 |
| Other numbered events (#1, #3…) | once | campaign (not said) | fallback roll | House 6, Street 6 |
| Graffiti Clue | once | campaign | no effect | Railways 4 |
| Black mirror rituals (#28) | once per demon name | campaign | no effect | `6_unique_events.md` |
| Walrus side mission | once | campaign | reroll | Side Missions 6 |
| Event #2, Hand of Glory (#33) | none | — | play again | `6_unique_events.md` |

- Two scopes: **mission** and **campaign**. "In the game" and unstated limits count as campaign ([rulings](rulings.md)).
- The name "Unique Events" does not mean once: #2 says "This is not a unique event", and most events state no limit at all.

## Unique Events as stories

Numbered events form short story chains, held together by choices, items and keywords found earlier. Spoiler-free: numbers and how they connect, no plot.

```mermaid
flowchart LR
    subgraph fromSpecial [From Special Events]
        s1[Special 1] -- roll --> e26["#26"] & e37["#37"]
        e37 -- choice --> e41["#41<br/>separate map"]
        e27["#27<br/>no caller found"] -- choice --> e30["#30"] -- choice --> e32["#32"]
    end
    subgraph fromHaunted [From Haunted House]
        h4[Haunted House 4] -- choice --> e17["#17"]
        e17 -- choice --> e19["#19"] & e20["#20"]
        e17 -- "choice, needs an item" --> e21["#21"]
        e20 -- choice --> e22["#22"]
        e20 -- "choice, carry an item there" --> e23["#23"]
    end
    subgraph fromFarm [From Farm]
        f1[Farm 1] -- choice --> e5["#5"] -- after a win --> e6["#6"] -- choice --> e8["#8"]
    end
    subgraph fromRailways [From Railways]
        r1[Railways 1] -- after a win --> e13["#13"] -- choice --> e15["#15"]
    end
    e23 -. sets a keyword .-> dh[Demonic Horrors] -- keyword checked --> e42["#42"]
    cs5[Children's Stuff 5] -. sets a keyword .-> r1
    e32 -. unlocks a table result .-> r1
    e32 -. "needs an item and a name" .-> e28["#28"]
    e28 --> e15 & e5
```

- **Story state lives in the inventory and the play sheet**: an item carried to a place (#23), an item kept until another one is found (#36), a ticket that opens an event (#24), names learned for a ritual (#28).
- **Deferred events**: #18 tells you to write down #25 and read it only when a later moment happens (a hit in combat). An event can be armed now and triggered later.
- **Orphan events**: #7, #18, #27 and #39 are referenced nowhere in the extracted text. Lost in the OCR, or missing from the book.
- **A curse can watch events**: #21 can give a curse that costs Sanity "every time you play through a numbered event".

## What the game remembers

What the game remembers is tied to lifetimes, and the lifetimes nest: a campaign outlives its characters, a character outlives its missions. Leaving a level forgets what it held.

```mermaid
stateDiagram-v2
    [*] --> Campaign
    state Campaign {
        [*] --> Character
        Character --> Character: dead or insane,<br/>a new character continues
        Character --> [*]: 7th Hell Gate closed
        state Character {
            [*] --> Mission
            Mission --> Mission: complete or aborted,<br/>a new mission is rolled
        }
    }
    Campaign --> [*]
```

| Level | Forgotten when | What it remembers | Examples |
| --- | --- | --- | --- |
| Campaign | never, it is the game | the map and its boxes, the box counter, content used for good, creatures killed, keywords about the town | Special Events, Slashers, Rosen House, rituals done, SNOWY |
| Character | death or insanity | Food, Clues, stash, items, Skills, XP, Injuries, Scars, curses, what was read, keywords about the person | Necronomicon read, cursed blade, deferred #25, CLOWNFACE |
| Mission | a new mission is rolled | content used this mission, mission progress | Children's Stuff found, #9 and #10 played, doses found |

**Which level a fact belongs to: does it describe the town or the person?** What happened to the town (events played, creatures killed, places found, Hell Gates closed) belongs to the campaign. What the character carries, knows or suffers (Clues, Food, items, Skills, curses, books read, names learned) belongs to the character. What serves the current goal belongs to the mission. This is our design principle, not a book rule. What counts is who a thing belongs to, not where it lies: the stash and discarded items lie in a box but disappear with the character ([creator answers](creator-answers.md), [rulings](rulings.md)).

**One event can write to several levels.** Railways 4: "Gain 1 Clue the first time you find this in the campaign." The campaign remembers the event happened; the Clue goes to the character. If the character dies, the new one loses the Clue and cannot get it again.

**Boxes** are not a lifetime: they are the campaign's map. Each box remembers its places (every place table rolled in it), left-behind encounters, Searched, marks (Safe House, Hell Gate, deconsecrated church, Rosen House) and every-visit rules (cultists 2 in 6, religious symbol "every time you visit"). One box memory crosses levels: the **stash** sits in a box but dies with the character ([creator answers](creator-answers.md)).

- **A box can change its nature later**: Flauros deletes two Safe Houses and a church ("Roll on the Haunted Houses table if you visit those areas", #28), a failed fight makes a deconsecrated church (Place of Worship 2).
- **Not everything happens on the grid**: #16 moves you 1 or 2 boxes, #42 can force you into a neighbouring box, #41 opens a separate forest map.

## What this reveals

- **Results are scripts.** A few step kinds (encounter, chain, choice, gate, gain, effect, box mark, movement) cover the content read so far, but steps mix freely and many results carry one unique rule. This is the main input for D1 (rules content format).
- **The game needs a history.** Gates and exhaustion read what happened before. The memory follows nested lifetimes (campaign, character, mission), so one record of "what happened" (played, found, killed, keywords) per level could serve them all.
- **Game moments again.** "As you leave", "as soon as you pick up", "every time you visit", "as soon as your blade hits", "every time you play a numbered event": the effects and game moments topic must cover them.
- **Encounters are wider than combat.** The combat model covers creature groups; hazards and people need the same lifecycle (met, resolved, left behind) without a fight.

## Decided

The questions this topic raised are settled in [rulings](rulings.md#encounters): ignoring and moving along block the Search, limits and numbered events are campaign-wide unless stated, SNOWY is a campaign keyword, a box counts as every place table rolled in it.
