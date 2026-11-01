# E5b: book mode, manual actions

- Date: 2026-11-01
- Session ID: a6637d17-e3db-457c-80f6-4a12797dd8e5 (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `e5b-book-mode-manual-actions` (the PR is found from it). The same session ran R3 as a background agent: see [the R3 log](202611012105-r3-weapons-items.md).
- Model: Opus 5.5, high effort
- Transcript: [transcripts/202611012105-e5b-book-mode-manual-actions.txt](transcripts/202611012105-e5b-book-mode-manual-actions.txt)

## Goal

Book mode, manual actions: the player applies what the engine cannot read with actions that go through the rules, and the turn ends at 0 Life or Sanity. Done when a player can walk the town in the terminal, every box shown as text and applied with manual actions, until death or quitting.

## Done

- `engine/manual.py`: the manual actions (gain, lose, roll vs L, write a note, remove a note, mark a Safe House), `offered(game)` (only what the rules allow now), `apply`, and `apply_effects`, the free action "apply an effect" (the ones about the character, until "back").
- Book mode: after an entry the engine cannot read (a table not copied yet, a numbered event, a copied entry with no written lead), the menu offers where the text leads, the manual actions and "nowhere else", and comes back after each action. At 0 Life or Sanity it offers only the manual actions and "nowhere else". `book_mode.follow` follows a table already rolled (the Search).
- Notes: plain text on the character with the box number it was written at (`Note`), shown under the status line and above a modifier to type. The engine never reads them.
- `Game`: `roll_vs` (natural 1 fails, natural 6 succeeds), `search` and `may_search` (once per box, never a Safe House, a natural 1 stays 1, the result kept on the table), `ended`, `add_note` and `remove_note`; `Mark.SAFE_HOUSE`; `End` moved to `state.py`.
- Search as a free action; it asks a modifier only when the character has notes. The Search table's leads: 1 rolls the Random Encounter table, 2-5 lead nowhere (`Nowhere`), 6 stays in book mode until E10.
- Protocol: `Number` and `Text` requests (the answer must fit the request); topics `STAT`, `AMOUNT`, `LEVEL`, `MODIFIER`, `NOTE`, `NOTES`, `APPLY`; events `Changed`, `RolledVsL`, `Searched`, `Marked`, `NoteWritten`, `NoteRemoved`; actions `SEARCH`, `APPLY`.
- Terminal: `s` search, `a` apply an effect (`b` back), `n` new sheet (was `s`); `g`, `l`, `v`, `w`, `x`, `h`; number and text prompts asked again until they fit.
- Content: a weapon list shape (a file with `weapons`, no dice), the `weapon` kind, `Content.weapons`, ready for R3.
- Tests written first: `tests/test_manual_actions.py` (scenarios, the Search, rolls vs L, typed answers) with 9 pending tests, skipped, each naming the task it waits for; terminal tests; the loader tests for weapon lists. 352 pass, 9 skipped, ruff clean, the architecture diagrams render.
- Docs: `design/mvp-scope.md` (where manual actions are offered, notes, death once the entry is applied), `design/game-flow.md` (no Search in a Safe House), `docs/architecture.md`, `docs/content.md` (weapon lists), `CLAUDE.md` (the answer must fit the request), the Readme, `NextSession.md`, `WorkingWithClaude.md` (batch prompts report every correction and keep the book errors list).
- The first plan was decided too fast: twice the user said they did not understand a question and the session picked an answer and called it settled. The user pointed it out; the questions were explained again with concrete screens, and every choice after that was laid out as options with pros and cons for the user to decide. Saved as a working rule for later sessions.

## Decisions

- **Manual actions after an entry the engine cannot read, and the ones about the character as the free action "apply an effect"** (the user). A lasting effect noted earlier must be applicable on a turn where no entry is shown. One action that opens a submenu keeps the free actions short. Marking a Safe House is about the town, not the character: only the entry that gives it offers it.
- **Notes** (the user's idea): the player's reminders of lasting effects and modifiers the engine cannot track, shown on screen. Safer than typed item names: the engine never reads them. Each note keeps the box number it was written at (the user), so an effect "for N boxes" can be followed. They go away only when all content is written; E8 considers manual effects the engine applies by itself (written in the Readme, at the user's request).
- **Search asks a modifier only when there are notes** (the user): no prompt on every Search before Skills exist.
- **Death is checked when leaving the entry** (the user): the player applies the whole entry, a heal included, before the chain stops. Pending tests remind the later tasks of the edge cases (Injury offer, reactions after a loss, a written entry at 0).
- **No Search in a Safe House**, as the book says (the user); `design/game-flow.md` said otherwise and is fixed. Home stays a plain box until E15, so it can be Searched (the user).
- **Items wait for R3** (the user): typed item names were judged risky. Taking and dropping items is a small task after R3.
- **A loss stops at 0, no max on gains until E6, Search 6 by picking the table 4 times, the new keys** (the user, after reviewing what the session had chosen alone).
- **An item is its table entry; weapons get their own IDs** (the user, for R3): duplicates are harmless. The weapon headings that name two weapons keep one ID for now; two IDs sharing the text is the likely choice, decided at E6.
- **Split commits, a finished chunk committed before the next task** (the user). The loader support was committed so R3 could branch from it (stacked PR).

## Open questions

- Weapon headings that name two weapons: two IDs sharing the text, at E6.
- Manual effects the engine applies, replacing notes: at E8.
- The book errors kept as printed: a review session once the batches are done.

## Next

R2 (Skills and harm tables): shapes settled with the user (Opus, high effort), copying by a background agent (Sonnet, medium effort). Then E6.
