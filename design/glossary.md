# Glossary

The domain vocabulary. Docs, issues and code use these words with these meanings. Rules links point to the book text, which stays the reference.

## Campaign and mission

- **Campaign** — one continuous game in one town: map, box counter, Food and Clues carry on across missions. Won when 7 Hell Gates are closed. Survives character death: a new character continues it, without the Food, Clues and stash of the previous one.
- **Mission** — one game session, rolled on the [Mission table](../gameRules/tables/5_3_missions_table.md). Has a goal, mission-specific rules, and rewards. Ends when the goal is met and the character is back Home (or, for some missions, at a Safe House), when the character dies or goes insane, or when aborted at a Safe House (a new mission is rolled).
- **Hell Gate** — a campaign objective. Closing one is possible during any mission.
- **Side mission** — a secondary goal given by a table result, kept alongside the mission.

## Character

- **Character** — the single hero. Has a name, Life, Sanity, Skills, XP, Food, Clues, Inventory, Injuries and Mental Scars.
- **Life** — physical health. At 0 the character dies. Fully restored between missions.
- **Sanity** — mental health. At 0 the character goes insane. Fully restored between missions.
- **Injury** / **Mental Scar** — permanent effect taken to avoid losing 1–2 Life / Sanity. Max 3 of each per character lifetime.
- **Skill** — a capability with a Basic and an Expert level. Most modify rolls. **Arcane Skills** have prerequisites (books, rituals).
- **XP** — experience points, earned by winning combats and missions, spent at any time to buy Skills or upgrade them to Expert.
- **Clue** — currency of investigation. Spent to hunt a specific creature.
- **Food** — points consumed every 5 boxes. Carried separately from items, up to a limit.

## Inventory

- **Item** — a carried object. Bundles (several stakes, candles, medical supplies) count as one item. Max 10, raised by a Backpack and the Strong Skill (hard max 20).
- **Light item** — negligible weight, does not count against the limit.
- **Hands** — what is held. Matters for two-handed weapons and for losing the backpack.
- **Ammo** — tracked per type (bullets, rifle bullets, bolts, arrows, shells).
- **Stash** — items left in a Safe House. Can be stolen if the Safe House stops being one.

## Town

- **Town map** — the town as one grid of boxes, growing sheet by sheet. See [town map](town-map.md).
- **Sheet** — a 5×6 block of 30 boxes. A new one is attached next to an existing sheet when a sheet is fully visited, or after a mission; boxes across the seam are neighbours.
- **Side map** — a separate grid outside the town, opened by an event (the forest of #41).
- **Box** — one area of town (~2 hours of walking). Counts as every place table rolled in it (a haunted clinic is a Clinic and a Haunted House).
- **Neighbour** — a box sharing a side or a corner: diagonals included, up to 8.
- **Distance** — the fewest moves between two boxes, a diagonal step counting as 1.
- **Home** — the starting box. Not a Safe House: random encounters happen there too.
- **Box number** — the order in which boxes are entered (1, 2, 3…). It is the clock of the campaign, never reset between missions: Food, effect durations and some mission triggers count boxes.
- **Unexplored** / **Visited** box — whether its content was already generated.
- **Searched** — the box was Searched (once per box, except libraries).
- **Left-behind encounter** — an encounter the character fled or ignored. It stays in the box with its full text. A box can hold several; each needs its own Stealth roll, or they are fought in waves.
- **Safe House** — a box where the character heals and stashes items, with no random encounters. Max 3 in play.

## Play

- **Table** — a roll (d6, 2d6, d66…) mapped to results. The backbone of the game content.
- **Result** — what a table gives: a short script of steps (encounter, chain, choice, gate, gain or loss, effect, box mark, movement). Can be rolled, forced or shifted by a mission.
- **Chain** — a result sending to another table or a numbered event. Resolved in the same box.
- **Town Exploration table** — rolled when entering an unexplored box. Points to a **place table** (House, Street, Clinic…).
- **Gate** — a condition on a step: a chance (x in 6), an item, Skill or keyword owned, or what happened before.
- **Keyword** — a flag written on the play sheet by a result and checked by others (CLOWNFACE, SNOWY). Belongs to the campaign or the character, depending on what it describes.
- **Moving along** — choosing not to explore a place. Like ignoring, the place stays in the box and the Search is blocked.
- **Random Encounter table** — rolled on a 1 in 6 when entering a visited box. Points to a **creature table** (Beasts, Undead…).
- **Unique Event** — a numbered, scripted event triggered by a table. Played once per campaign unless its text says otherwise. Events chain into short stories.
- **Encounter** — whatever is met in a box: creatures, people, a hazard, an event. Ends **resolved** (won, negotiated, avoided, survived), **ignored** or **fled**. Ignored and fled encounters stay in the box and block the Search.
- **Creature** — an opponent with a Level (L), Life, Damage and traits (Slow, Undead, vulnerabilities…).
- **Group** — the creatures one table result produces ("2d6 Zombies"). Members share a profile, each has its own Life. An encounter can hold several groups.
- **Round** — your turn plus the creatures' turn. The book says "turn" for both.
- **Action** — what you do on your turn: Attack, Escape, use an item, cast, change weapon.
- **Wave** — one of several groups in a box fought one after the other, with no rest between them.
- **Explosion** — a natural 6 on an Attack roll: roll again and add, repeat on each 6.
- **Fumble** — a natural 1 on Defense followed by another 1: take 1 more Damage, skip your next attack, or destroy your weapon.
- **Roll vs L** — the core mechanic: roll d6 plus modifiers, success at L or higher. Natural 1 fails, natural 6 succeeds. Named by purpose: Save, Attack, Defense, Stealth, Escape, Charisma, Strength, Magic.
- **Modifier** — a bonus or malus to a roll, from a Skill, item, Injury, Scar, mission or effect. Modifiers stack unless the text says otherwise.
- **Effect** — one rule change, temporary or permanent (e.g. "-1 to Stealth for the next 3 boxes"). Has a source, a holder, a kind (roll modifier, stat modifier, rule parameter, new action, restriction, reaction) and a lifetime. See [effects](effects.md).
- **Holder** — who carries an effect: the character, an item, a creature or group, a box, the mission or the campaign. The effect is forgotten with its holder.
- **Moment** — a point in play that effects react to or end on: a box of time passes, enter or leave a box, combat starts, you take Damage… A "would" moment can be changed before it applies (armor reduces the Damage), a "did" moment cannot.
- **Reaction** — an effect that acts when its moment comes, with a script of steps like a table result. A deferred event and a timed step ("as you leave") are reactions.
- **Box of time** — a unit of time, the time to walk through one box. Moving takes one; reading a book or performing a ritual can take some without moving.
- **Search** — a roll on the Search table after an encounter is resolved (or when there is none).
- **Hunting** — spending Clues equal to a creature's L to meet it in the next box.
- **Loot** — items or Food gained after an encounter.

## Building the game

- **Written** — content whose rules the engine plays itself. Content that is not written yet goes through book mode. See [MVP scope](mvp-scope.md).
- **Book mode** — the fallback for unwritten content: the engine shows the text of the entry reached, and the player applies it with manual actions. What was reached is still recorded.
- **Manual action** — a game operation the player calls in book mode: gain or lose a resource, add or remove an item, go to a table or event, make a roll vs L or a Search roll, fight a creature, mark a box. It goes through the rules like written content.
- **Step 1** / **Step 2** — the two parts of the MVP: Bring Home the Bacon (one mission), then Close a Hell Gate with campaign play.
