# Game flow

How a game runs, from campaign down to a single box. Words are defined in the [glossary](glossary.md).

## 1. Campaign

The campaign is one continuous walk through one town. Missions are goals layered on top of it: the map, the box counter, Food and Clues all carry on from one mission to the next ([creator answers](creator-answers.md)).

```mermaid
flowchart TD
    start([Start campaign]) --> create[Create character]
    create --> roll[Roll mission<br/>reroll if same as last one]
    roll --> play[[Play mission]]
    play --> outcome{Outcome}
    outcome -- aborted at a Safe House --> roll
    outcome -- complete --> rewards[Gain rewards<br/>restore Life and Sanity to max]
    rewards --> gates{7 Hell Gates closed?}
    gates -- yes --> won([Campaign won])
    gates -- no --> sheet[Optionally start a new map sheet]
    sheet --> roll
    outcome -- dead or insane --> lost[Character lost<br/>with Food, Clues and Safe House stash]
    lost --> create
```

Carried between missions: map, box counter, Food, Clues, Skills, XP, items, Injuries, Scars. Reset: Life and Sanity (healed to max).

Open: after a death, does the new character keep the same map? Stash, Food and Clues are lost, the map is not mentioned.

## 2. Mission

```mermaid
flowchart TD
    start([Mission rolled]) --> home[First mission: choose Home box<br/>it is box 1, no content roll<br/>Later missions: continue where you stand]
    home --> turn
    subgraph turn [Turn]
        move[Move to a neighbouring box<br/>number it] --> upkeep[Upkeep<br/>Food every 5 boxes, effects tick,<br/>mission triggers on box count]
        upkeep --> arrive[[Arrive in box]]
        arrive --> search{Search allowed<br/>and wanted?}
        search -- yes --> doSearch[Search roll]
        search -- no --> free
        doSearch --> free[Free actions<br/>inventory, spend XP, stash]
    end
    free --> done{Back Home<br/>with goal met?}
    done -- no --> abort{At a Safe House<br/>and want to abort?}
    abort -- no --> move
    abort -- yes --> aborted([Mission aborted<br/>roll a new one])
    done -- yes --> win([Mission complete<br/>gain rewards])

    anywhere>At any time: Life or Sanity at 0] --> lose([Mission lost])
```

The character must leave a box to play it again: no staying in place to heal twice. Home is not a Safe House.

Search is allowed when the encounter was not fled or ignored ([rulings](rulings.md)) and the box was not Searched yet. A Safe House follows the same rule as any box. Libraries can be Searched again for 1 book or 1 Clue.

## 3. Arriving in a box

```mermaid
flowchart TD
    enter([Enter box]) --> hunt{Hunt paid with Clues?}
    hunt -- yes --> hunted[Meet the hunted creature]
    hunt -- no --> visited{Visited before?}
    hunted --> encounter

    visited -- no --> mission[Mission rules apply<br/>may replace the content: witch found with Clues<br/>or add to it: Hell Gate]
    mission --> explore[Roll Town Exploration 2d6<br/>unless replaced]
    explore --> place[Choose or roll the place table]
    place --> outcome[Resolve table result<br/>may chain to creature tables,<br/>Unique Events, choices]

    visited -- yes --> safe{Safe House?}
    safe -- yes --> heal[Heal, stash or retrieve items<br/>no encounter]
    safe -- no --> remaining{Encounters left here?<br/>fled or ignored}
    remaining -- yes --> sneak{For each group:<br/>sneak past?}
    sneak -- "Stealth roll fails, or no sneaking" --> waves[Fight the groups in waves<br/>no rest between them]
    sneak -- all Stealth rolls succeed --> wander
    remaining -- no --> wander{1 in 6}
    wander -- yes --> random[Roll Random Encounter table]
    wander -- no --> nothing[Nothing happens]

    outcome --> encounter[[Encounter]]
    waves --> encounter
    random --> encounter
    encounter --> result{Result}
    result -- resolved --> canSearch([Search allowed])
    result -- "fled or ignored" --> stays([Encounter stays in the box<br/>no Search])
    nothing --> canSearch
```

Safe Houses, and what happens when one stops being one, are detailed in [Safe Houses](safe-houses.md).

A box can hold several encounters left behind (fled or ignored). Each keeps its full text: an ignored zombie horde with special loot is the same horde when you come back.

Mission rules that say "every time you visit" a place apply to visited boxes too (e.g. Medical Supplies at a Clinic).

Hunting applies to any box, visited or not: a creature hunting you does not care whether you have been there before (our ruling, see [rulings](rulings.md)).

## What the flows reveal

- **Everything is a roll vs L or a table roll.** Two mechanisms carry most of the game.
- **Modifiers come from everywhere**: Skills, items, Injuries, Scars, the mission, temporary effects. A roll must collect them all.
- **Rules react to moments** ("every 5 boxes", "every time you visit a Clinic box", "after 12+d6 boxes", "in the last 5 locations"). Missions are mostly made of such reactions. We need a notion of game moments that rules can hook into.
- **The player chooses constantly** ("your choice", "you may ignore them", "you may explore it or move along"). The engine asks, the interface answers.
- **The box number is the clock**, and it runs for the whole campaign, not per mission. Durations and triggers count boxes. Some count only new boxes (the Hell Gate deadline).
- **The campaign is the real game state.** A mission is a goal plus its rules, swapped in and out of a continuous campaign. Saving a game means saving the campaign.
- **Boxes remember things**: content, encounters left behind, Searched, Safe House, stash. The map is not just geometry.
