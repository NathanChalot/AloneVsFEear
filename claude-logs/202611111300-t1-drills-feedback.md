# T1: Drills and feedback

- Date: 2026-11-11
- Session ID: a0586fb2-e148-4a41-9ac5-00d7608df36d (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `t1-drills-feedback` (the PR is found from it)
- Model: Opus 5.5, medium effort
- Transcript: [transcripts/202611111300-t1-drills-feedback.txt](transcripts/202611111300-t1-drills-feedback.txt)

## Goal

T1: short scoped runs to play in a break (`--drill creation`, `walk`, `lasting`, `xp`), and a way to write feedback while playing, with the seed and the box number. First, compare the pregenerated characters with the original sheets.

Done when: the four drills can be played from the terminal, and feedback can be written while playing. Met.

## Done

- **Started with `/start`** for the first time: the summary, the checks (main clean, E8 merged, 843 pass), then the go.
- **Pregenerated characters checked** against the original sheets: the ebook's two pages were extracted (`pypdf`) and rendered as images (`pymupdf`, no poppler on this machine). The Markdown matches the sheets word for word; nothing to correct. A stray "3" in the PDF's text layer is not printed on the page.
- **Pregenerated characters in YAML** (commit 1): `content/characters/pregenerated.yaml`, the new ID kind `pregenerated.`, `Pregenerated` in the content model, the loader (numbers only on a sheet, never dice), `reference_problems` over their Skills and gear, and `creation.pregenerated(game, id)`. Douglas's book read is left out until E18, noted in the Readme's E18 entry at the user's request.
- **Drills** (commit 2): `engine/drills.py` (`DRILLS`, `run`); `play()` takes a stop condition, checked after creation and before each turn, after death and insanity, ending with `End.DRILL_OVER`; `loop.choose_home` on its own; a `PREGENERATED` choice; `--drill NAME` in the terminal, which says what the drill tries and shows the character at the end. The `lasting` drill was played through the real command: meals at boxes 3 and 6, the effect ended on entering 5, the drill over at 7.
- **Feedback** (commit 3): `interface/feedback.py` (`FeedbackLog`); every line the terminal reads goes through `_line`, where `#` makes a note, then the same question again. `feedback/feedback.md` holds the notes (committed), `--feedback-file` changes it. Tried in a real run.
- Three commits, each tested and presented, committed with the user's go. 873 pass, 10 skipped, ruff clean.
- **Wrap-up**: drift check (the Readme's status, How to play and T1 entry, WorkingWithClaude's feedback line, NextSession's reminders, review items and plan; `docs/architecture.md` and `docs/content.md` were updated with each commit).
- **The roadmap's letters** (the user asked what they stand for): a table in the Readme's "How to use this roadmap", D decision, R rules text, E engine, T testing tools, V verification, P playtest. T and V were not written anywhere before; their names are Claude's reading of the entries, accepted by the user.

## Decisions

- **The pregenerated characters are content** (the user): YAML with IDs, reused by E17's quick run. Rejected: Python in the drill module (quicker, book data in code).
- **Feedback with `#` at any prompt** (the user): interface only, works during creation and book mode. Rejected: a free action in the menu (only between moves, a new engine action).
- **Feedback kept in `feedback/feedback.md`, committed** (the user). Rejected: `logs/feedback.md` git-ignored, and the run's log alone. Each note also goes into the run's log.
- **The drills with a pregenerated character ask which** (the user), through the engine's protocol (`Topic.PREGENERATED`), so scripted tests can answer it. Rejected: fixed per drill, or picked by the seed.
- **How each drill ends** (decided while implementing, from the roadmap's description): `creation` once the character is made, before Home; `walk` after 10 boxes from Home; `lasting` after 6, with Eating Disorder and -1 to every roll for the next 3 boxes set once Home is chosen (so its end shows the right box); `xp` once nothing can be bought, with XP for the dearest Expert level held and the dearest new Skill (14 for Anna, 13 for Douglas).
- **Where a sheet disagrees with the rules, the rules win**, as the Markdown already said: Douglas's Strong at Basic, Anna's one hammer. The sheets' own words stay in the Markdown; the YAML holds numbers and IDs.

## Open questions

- V1: what happens to a feedback note once triaged (removed, or moved to the triaging session's log).
- E18: Douglas's book read goes back on his sheet (the Readme's E18 entry).

## Next

E9 (inventory, with its `inventory` drill), Sonnet, high effort. Then V1, which triages the first feedback.
