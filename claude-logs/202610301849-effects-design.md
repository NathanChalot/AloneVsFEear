# Effects and game moments design

- Date: 2026-10-30
- Session ID: dd60dc57-dea0-4ddf-81b2-68d50ee62d59
- Branch / PR: `docs/effects-design` / https://github.com/NathanChalot/AloneVsFEear/pull/7
- Transcript: [transcripts/202610301849-effects-design.txt](transcripts/202610301849-effects-design.txt)

## Goal

Milestone 2 effects topic: consolidate effects and game moments, the two concepts found in every design topic so far.

## Done

- Created `design/effects.md`: what an effect is (source, holder, kind, lifetime), six kinds (the five from the character page plus reactions), holders, lifetimes as moments or conditions, the moment catalogue by scope, "would" and "did" moments (the Damage pipeline), box and time as two moments, how rolls collect their effects, several reactions on one moment.
- Searched the rules text for timing words ("every time", "as soon as", "until", "for the next", "first time"…) to build the moment and lifetime lists from the book.
- New `Effects` section in `design/rulings.md`.
- Glossary: Effect and Modifier updated; new Holder, Moment, Reaction, Box of time.
- Ticked the Readme checkbox, updated `NextSession.md`.

## Decisions

- **Modifiers stack unless the text says otherwise** — the book lists its exceptions (Agile/Dodge, amulets, Good Shot). The user asked for an online check: no creator answer found.
- **A box of time without moving advances the clock only** — Food, "next N boxes" and mission deadlines count it; no encounter roll, no place rules, new-box deadlines ignore it. Switchable: a harsher mode rolls a 1 in 6 random encounter per box of time.
- **Reactions that help you come before reactions that hurt you**, then the player picks; switchable (horrific mode: harmful first). The user decided two examples first (Safe House cures the infection before it costs Life; the first aid kit heals before the grenade's encounter arrives), then agreed to generalise. The user framed the order as story ("you are still bandaging when they come"), useful for narration (D8).

## Open questions

- Decide when implementing: where "every time you cross a box" starts counting, whether a "until the end of the campaign" Save bonus (#28) survives the character, unlimited-retry effects.
- Python cannot run in the repo until `.tool-versions` is fixed (Project setup session).
- Diagrams were not render-checked; check the preview on GitHub.
- `claude-logs/transcripts/202610301100-domain-design.txt` sits untracked on `main`, never committed with PR #3.

## Next

Town map and MVP scope (see [NextSession.md](../NextSession.md)).
