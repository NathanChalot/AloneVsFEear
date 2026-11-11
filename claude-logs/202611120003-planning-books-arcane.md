# Planning: books and Arcane Skills into Step 1

- Date: 2026-11-12
- Session ID: d89529ba-dc96-4c3b-96e4-76eff48a4f3b (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `planning-books-arcane` (the PR is found from it)
- Model: Opus 5.5, medium effort
- Transcript: [transcripts/202611120003-planning-books-arcane.txt](transcripts/202611120003-planning-books-arcane.txt)

## Goal

Move books and learning Arcane Skills into Step 1 (the T2 decision): split E18, put the Random Book table ahead of it, place it in Step 1's order. Also settle whether the roadmap shows the drills. Planning with the user, no code.

Done when: the roadmap entries are rewritten and NextSession's plan matches. Met.

## Done

- **Read** the Arcane Skills rules, the Random Book table, Random Objects 45 and 61, and the pending tests that name E18. Found: books are only half items (the entries point to the Random Book table but give no item yet); a book you start with is already read; Gate's last path (5 Clues in a Hell Gate box) needs Hell Gates; the pending Faith test is about Exorcism's effect.
- **Roadmap** (`Readme.md`): E18 "Books and Arcane Skills" moves into Step 1 between V1 and E10 (Random Book table, books as items found once per game, reading in d3 boxes of time, a book read by manual action, learning the 11 Arcane Skills through purchases; effects in book mode; Douglas's printout; the `books` drill), with its open questions listed. R7 split into R7a (Random Book table) and R7b. E19 takes Gate's Clue path and depends on E17. E12 takes the Faith pending test. Status and MVP goal updated.
- **`design/mvp-scope.md`**: books and Arcane Skills in Step 1 (engine list and content table), Gate in Step 2.
- **NextSession**: plan E9, V1, R7a, E18, then the rest of Step 1; Faith reminders; the T2 merge reminder removed. **WorkingWithClaude**: session counts. **`catalogue.yaml`**: R7a and R7b comments. **Tests**: the Faith skip reason and a comment say E12. 898 pass, 10 skipped, ruff clean.
- Commits: the `xp` drill note, then the planning changes.

## What became of each note

`xp` drill (2026-11-12 00:02): "Will becomes Expert: 6 XP spent" vs "Spent 6 XP to upgrade Will to Expert" → V1, which moves the terminal's wording into `screens/`; E18's learning lines follow the same pattern.

## Decisions

- **E18 keeps its ID and moves into Step 1**; what is left of it (Gate's Clue path) joins E19, which already has the closing roll. Rejected: E18a / E18b (a very thin E18b), renumbering the roadmap (every reference to E10 to E20 changes).
- **E18 comes after V1, before E10**: V1 tidies the terminal first, V2 reviews E18. Rejected: before V1 (V1 waits, its list already long), after E11 (books found by Search, but later).
- **R7 split**: R7a (the Random Book table) ahead of E18, R7b any time. Rejected: E18 copying the table itself, the whole R7 first.
- **The roadmap does not track drills played**: each Done when names its drill, the log of the session that triages its notes says what became of them. Rejected: a "played" line per entry, a drills table.
- **The Faith pending test waits for E12** (turning a vampire happens in a fight; Faith is one of the 22 Skills Step 1 writes). Rejected: E18 writing Exorcism's effect, Later.

## Open questions

- E18 (listed in its entry): learning any time after reading or only while reading; whether a book takes an item slot; Healing and the Holy Book; a Sanity cost before E13.

## Next

E9 (Sonnet, high effort), then V1, R7a, E18 (Opus, high effort). Drills before E9: none needed; `creation` optional.
