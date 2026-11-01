# Project review

- Date: 2026-11-01
- Session ID: 46ed82c6-c247-475c-827c-3ca66b0c9207 (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch: `project-review` (the PR is found from it)
- Model: Opus 5.5, xhigh effort
- Transcript: [transcripts/202611011109-project-review.txt](transcripts/202611011109-project-review.txt)

## Goal

A step back before book mode: an adversarial review of the project so far (design coherence, architecture risks, roadmap, code and tests, process), read cold in a fresh session. Findings only, then the user goes through them; what is agreed becomes roadmap entries, rulings or doc fixes.

## Done

- Read CLAUDE.md, the Readme, NextSession, WorkingWithClaude, `design/`, `docs/`, the code, the tests and the latest logs. Health checks: 250 tests pass, ruff clean, CI green on `main`, all 40 Mermaid diagrams render with `mmdc` (the asdf shim needs to run from the repository, where `.tool-versions` sets Node.js). The YAML texts match their Markdown sources (43 of 44 found word for word; the other comes from another chapter).
- 16 findings, each with a severity and a proposed action. The user's global feedback: we are under development and must stay agile, so no rigid decision too soon. Several findings (1, 3, 4, 5, part of 9) asked to settle early what can be settled as we go; they were dropped or reduced.

| # | Finding | Outcome |
| --- | --- | --- |
| 1 | Rules that ask the player have no home (`Game` holds no interface) | Dropped: settled as we go |
| 2 | E5 is an architecture session planned as a Sonnet one | E5 split into E5a (reading) and E5b (manual actions), both Opus |
| 3 | Death is checked only at the start of a turn | E5b requirement: the turn ends as soon as Life or Sanity reaches 0, once effects have resolved |
| 4 | Only `Arrival` and `Ended` are told; interfaces read the state | Dropped: events are added when a feature needs them |
| 5 | Quitting mid-turn leaves a half-played turn | One line in the Later save item: a save is the state at the start of the turn |
| 6 | E8 builds the whole reaction machinery up front | E8 trimmed to Skills and Food; the rest moved to E10, E12, E13 |
| 7 | Two copies of the rules text, nothing checks they agree | Dropped: book mode shrinks; the YAML is reconsidered in due time |
| 8 | Work with no slot | Attaching a new sheet added to E5a; R6 and the pregenerated check stay as they are |
| 9 | Small doc inconsistencies | Only the glossary fixed (points to the Injury ruling); the rest is work-in-progress noise |
| 10 | Unsourced "no Search in a Safe House" | Removed from game-flow: a Safe House is Searched like any box |
| 11 | The Food ruling breaks when the interval changes | Open question on E8 |
| 12 | Optimistic estimates | Session-number predictions removed; the table stays as rough sizes |
| 13 | The same facts kept in several places, a costly wrap-up | Lighter wrap-up (next session's model only, no PR link in the log), class diagrams without field and method lists, memory files that repeated CLAUDE.md deleted |
| 14 | The no-spoiler rule is unclear | Clarified in CLAUDE.md |
| 15 | The coordinator run left no log and committed on `main` | Dropped |
| 16 | CI checks less than the local commands | `ruff format --check` added to CI |

- Files: `CLAUDE.md` (stay agile, design describes the end state, spoiler scope, lighter wrap-up), the Readme (E5a, E5b, E8, E12, E13, Later), `NextSession.md`, `WorkingWithClaude.md` (wrap-up steps, sizes, model table), `claude-logs/README.md` (template: branch and model, no PR link), `design/glossary.md`, `design/game-flow.md`, `docs/architecture.md`, `docs/content.md`, `.github/workflows/ci.yml`. Memory: five files that repeated CLAUDE.md deleted.

- After the wrap-up (the user): a How to play section in the Readme (setup, command, seed, map legend, log), kept up to date at wrap-up when what a player can do changes; a design review once the MVP is done, under Later.
- The first wrap-up commit held everything; at the user's request the branch was rebuilt as one commit per kind of change (CI, working rules, wrap-up, roadmap, sizes, design and architecture fixes, how to play, design review, this log), and force-pushed.

## Decisions

- **Stay agile** (the user): settle things as we go when changing course later is cheap; raise a question only if its answer changes what we build now; reviews must not ask to decide early what can wait. Written in CLAUDE.md.
- **`design/` describes the game once the MVP is done**; a roadmap task can be a transitional step (E5 applies fights by hand before E12). Where a design page and a ruling disagree, the ruling wins (the user).
- **E5 split into E5a and E5b**, both Opus, high effort (the user).
- **E8 trimmed** to the moments and lifetimes the Skills and Food need (the user).
- **A Safe House is Searched like any box** (the user). The book has no exception, so no ruling is needed; the invented restriction was removed.
- **Spoilers**: chat, `docs/`, the Readme, NextSession, WorkingWithClaude and the logs stay spoiler-free; the rules, `design/` and the code may hold whatever the rules say (the user).
- **Lighter wrap-up** (the user): only the next session's model and effort are reviewed; no PR link in the log, so no second push; CLAUDE.md is the one copy of the working rules.
- **No test that the YAML and the Markdown agree** (the user): book mode shrinks as rules move to Python; what becomes of the YAML is decided in due time.

## Open questions

- Can something that triggers after a loss bring the character back above 0 before death is checked? The user leans yes; settle it in E13 with tests and user stories.
- The Food clock when its interval changes mid-game (Resistant to Hunger, Eating Disorder): options at E8.
- Settled as we go, not before: where the rules that ask the player live, and which events the engine tells the interface.

## Next

E5a: book mode, reading (Opus, high effort), then E5b: manual actions (Opus, high effort).
