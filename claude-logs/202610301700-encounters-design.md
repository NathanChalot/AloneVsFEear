# Encounters and tables design

- Date: 2026-10-30
- Session ID: afe8e30f-82f3-474d-851b-e0474cfedb88
- Branch / PR: `docs/encounters-design` (stacked on `docs/combat-design`) / https://github.com/NathanChalot/AloneVsFEear/pull/5
- Transcript: [transcripts/202610301700-encounters-design.txt](transcripts/202610301700-encounters-design.txt)

## Goal

Milestone 2 encounters topic: how table results chain, choices, left-behind encounters, Unique Events.

## Done

- Committed and pushed the combat log update and its transcript to PR #4.
- Created `design/encounters.md`: the table web, picking a result (forced, shifted, rolled, fallback), the building blocks of a result, resolving a result, an encounter's life, things that run out, Unique Events as stories (spoiler-free graph), what the game remembers (nested lifetimes campaign → character → mission).
- New `Encounters` section in `design/rulings.md`; the discarded items ruling now says what happens on death.
- Fixed the glossary and `game-flow.md`, which disagreed on ignored encounters; new glossary entries (result, chain, gate, keyword, moving along), updated Box and Unique Event.
- Ticked the Readme checkbox, updated `NextSession.md`.

## Decisions

- **Purpose recentred** — the user felt Claude was making difficulties up. The design must answer what a table and a result are, how results connect, what state they read and write, and what happens to an encounter. Rule details that do not change the model are decided when implementing.
- **Diagram per idea** — the user asked why a class diagram; each idea now gets the form that fits it. The building blocks are a bullet list (a mindmap was unclear and added nothing), memory is a nested state diagram of lifetimes.
- **No plot details** — the user has not played the events; event names and numbers are fine, story details are not. The story graph shows only numbers and connections.
- **Ignoring and moving along block the Search** — they do not "deal with" what is in the box. A place you moved along from stays, and can be explored on a later visit ("more fun").
- **Limits are campaign-wide, numbered events happen once, unless the text says otherwise** — the book says "mission" when it means one; House 6 and Street 6 give fallbacks for already-played events. Searched online for a creator answer, found none.
- **Search result 1 dropped** — not an ambiguity: the Search is used, the fled creature stays.
- **Town or person** — a fact belongs to the campaign if it describes the town, to the character if the character carries, knows or suffers it; what counts is who it belongs to, not where it lies (stash). One event can write to several levels (Railways 4).
- **SNOWY is campaign level, CLOWNFACE character level.** Discarded items disappear when the character dies, like the stash.
- **A box counts as every place table rolled in it** — a haunted clinic is a Clinic and a Haunted House; if one is needed, the first place wins.

## Open questions

- Events #7, #18, #27, #39 are referenced nowhere in the extracted text: OCR loss or a book gap.
- Diagrams were not render-checked (downloading the Mermaid CLI was denied); check the preview on GitHub.
- The optional player-death rule (equipment stays on the body) is campaign-play material.

## Next

Effects and game moments (see [NextSession.md](../NextSession.md)).
