# Feedback

Notes written while playing (`#` at any prompt), newest last. Each is triaged at the next consistency review or playtest ([Working with Claude](../WorkingWithClaude.md#playtesting)).

## 2026-11-11 13:53 · drill creation · seed 3844001354 · box 0

- Character: none yet
- Asked: Your character's name:
- Log: logs/20261111-135243.log

I think at this step we should add some context and also that we should be able to go back and forth in our input with the keyboards arrow. Thats something we should discuss in a chat

## 2026-11-11 13:54 · drill creation · seed 3844001354 · box 0

- Character: none yet
- Asked: Your choice:
- Log: logs/20261111-135243.log

Same here, "Your 3 points: on Life and Sanity (8 each), or traded" is really unclear, we need some kind of explanation of what is asked

## 2026-11-11 13:55 · drill creation · seed 3844001354 · box 0

- Character: none yet
- Asked: Skill? [1-22]
- Log: logs/20261111-135243.log

Same there is nothing understandable oabout how the character is created here. I chose life and sanity, had to give an imnput, now I have the skill menu, From a user pov that s really not understandable. What should I do ? Whats going on ?

## 2026-11-11 13:56 · drill creation · seed 3844001354 · box 0

- Character: none yet
- Asked: Skill? [1-21]
- Log: logs/20261111-135243.log

Same comment, why the same sreen ? but this time without the descriptions?

## 2026-11-11 13:56 · drill creation · seed 3844001354 · box 0

- Character: Johny
- Asked: Which weapon? [1-2]
- Log: logs/20261111-135243.log

same we lack context

## 2026-11-11 16:25 · drill creation · seed 3592792389 · box 0

- Character: none yet
- Asked: Skill 2 of 2? [1-22, r: the texts again]
- Log: logs/20261111-162312.log

here "r: the text again" should become an hide option. Beside that I think that "show skills description" or something alike would be clearer phrasing

## 2026-11-11 16:26 · drill creation · seed 3592792389 · box 0

- Character: Johny
- Asked: Knife or stick? [1-2]
- Log: logs/20261111-162312.log

For stick I think the extra should be in parenthesise, its a note about it but here it seems like its description, this is weird

## 2026-11-11 16:28 · drill creation · seed 3809940781 · box 0

- Character: Johnnny
- Asked: Apply the text, then where does it lead?
- Log: logs/20261111-162645.log

this screen is unclear, I did not have to roll in the last drill, and now I do, what s going on

## 2026-11-11 16:28 · drill creation · seed 3809940781 · box 0

- Character: Johnnny
- Asked: Apply the text, then where does it lead?
- Log: logs/20261111-162645.log

Here "but you may learn any Arcane Skill taught by the book as soon as you have enough XP to pay its cost)" when do we plan to handle that ?

## 2026-11-11 16:30 · drill creation · seed 3809940781 · box 0

- Character: Johnnny
- Asked: Apply the text, then where does it lead?
- Log: logs/20261111-162645.log

From whayt I deducted "Random Objects table: 45" mean that I rolled a 45 against Random object table, and that this results allow me to roll against random book table. But that s not clear at all. Maybe having something .like: "Random object roll: 45 Random book table" or something like that ?

## 2026-11-11 16:31 · drill creation · seed 3809940781 · box 0

- Character: Johnnny
- Asked: Apply the text, then where does it lead?
- Log: logs/20261111-162645.log

"Apply the text and where does it lead ?" is it refering to: 1) Random Book table  g) gain  l) lose  v) roll vs L  f) add a lasting effect  w) write a note  d) nowhere else ?? If yes then its not clear

## 2026-11-11 16:32 · drill creation · seed 3809940781 · box 0

- Character: Johnnny
- Asked: Apply the text, then where does it lead?
- Log: logs/20261111-162645.log

I m skipping this and we will need to test uit specicially once we iomplemnted the book roll. As an observation, we may want to finish everything involved in charcter creation before going further don t we ? We may want to rediscuss our ourder of implementation here

## 2026-11-11 23:12 · drill creation · seed 3809940781 · box 0

- Character: none yet
- Asked: Your character's name:
- Log: logs/20261111-231056.log

"... table, and d6 Food. It takes 5 steps." seems a bit rough, "\n It takes 5 steps to complete your character creation:\n1. Your name\n2. XXXX\n YYYYY...." would be nicer

## 2026-11-11 23:15 · drill creation · seed 3809940781 · box 0

- Character: GG
- Asked: Knife or stick? [1-2]
- Log: logs/20261111-231056.log

"(roll twice if you traded your points for it)" we may want to say "(rolled twice if you traded your points for it)" as the player do not actually roll the dice, we do it for him.

## 2026-11-11 23:18 · drill walk · seed 3001718221 · box 1

- Character: Douglas Harrison
- Asked: What do you do?
- Log: logs/20261111-231645.log

"Home is box 1." feels weird as we just typed box 23. So maybe on the previous screen "Choose your starting position" and then "Home is now box 1" wdyt ?

## 2026-11-11 23:19 · drill walk · seed 3001718221 · box 2

- Character: Douglas Harrison
- Asked: Your choice?
- Log: logs/20261111-231645.log

"Rules: Roll on this table every time you move into an unexplored area. Then roll on the sub-table indicated by the result. Whenever possible, do NOT read the content of the tables in advance. Read them only when they apply to you.

## 2026-11-11 23:22 · drill walk · seed 3001718221 · box 2

- Character: Douglas Harrison
- Asked: Your choice?
- Log: logs/20261111-231645.log

its kind of a pain to test this drill without all the table implemented

## 2026-11-11 23:23 · drill walk · seed 3001718221 · box 3

- Character: Douglas Harrison
- Asked: Your choice?
- Log: logs/20261111-231645.log

same comment IO ll quite the session. I think we should post pone the drill to after we implement the other tables

## 2026-11-12 00:02 · drill xp · seed 3525280453 · box 1

- Character: Anna Miller
- Asked: What do you do?
- Log: logs/20261112-000054.log

"Will becomes Expert: 6 XP spent" wdyt of "Spent 6 XP to upgrade Will to Expert" ?
