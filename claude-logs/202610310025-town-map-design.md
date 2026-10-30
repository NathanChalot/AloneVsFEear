# Town map design

- Date: 2026-10-31
- Session ID: d5021e7c-848a-4aa1-90cd-5e5a732674e0
- Branch / PR: `town-map-design` / https://github.com/NathanChalot/AloneVsFEear/pull/8
- Transcript: [transcripts/202610310025-town-map-design.txt](transcripts/202610310025-town-map-design.txt)

## Goal

Finish Milestone 1 (the three image transcriptions) from the original PDFs, then the Milestone 2 town map topic. Milestone 3 (rules cleanup) stays for later.

## Done

- Copied the original rulebook files (ebook PDF, play aids PDF, character sheet PNG; not the zip) into `origin_rules/` at the root of the main checkout.
- Added `.gitignore`: `origin_rules/`, `*.pdf`, `*.zip`, Python virtualenvs and caches, `.DS_Store`. Milestone 4 item ticked.
- Rendered the image pages with PyMuPDF in a scratch virtualenv (no poppler installed, Python in the repo blocked by `.tool-versions`). Sources: play aids p. 3 and 4, ebook pp. 105-106.
- Transcribed `gameRules/12_character_sheet.md` (fields, as a table), `gameRules/13_town_map.md` (5×6 grid, number circle at bottom right) and `gameRules/14_pregenerated_characters.md` (Anna Miller, Douglas Harrison, with their differences from the rules).
- Created `design/town-map.md`: one town grid made of 5×6 sheets, side maps, neighbours, distance, the move family (normal, Escape, led astray, forced, jump), open points.
- Rulings (Map), glossary (Town map, Sheet, Side map, Neighbour, Distance), Readme checkboxes and E6 link, `NextSession.md`.

## Decisions

- **Distance counts moves, diagonals = 1** — the user chose it and asked whether it was certain. It is not: the book only says "the number of boxes… that you should cross". Moves fit the diagonal movement rule and #16. Recorded as `interpretation`; orthogonal counting rejected.
- **One grid, sheets attached on seams, edges are walls until a sheet is full** — follows "adding more sheets next to the previous ones"; separate linked sheets and a switchable unbounded grid rejected.
- **New sheet after a mission before the current one is full** — left open, it only matters for campaign play.
- **Forest map of #41** — size and entry decided with the MVP scope.
- **Milestone 3 without format conversion** — the user does not want to convert tables to another format yet.

## Open questions

- #16's jump (box in between crossed or skipped, 1 or 2 boxes of time), "most distant unrevealed box" scope and ties, distance around a missing sheet.
- The pregenerated sheets' text layer holds a hidden "3" in the left border, invisible on the page; ignored.
- Diagrams were not render-checked; check the preview on GitHub.

## Next

MVP scope (see [NextSession.md](../NextSession.md)).
