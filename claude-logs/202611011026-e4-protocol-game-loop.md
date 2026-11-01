# E4: engine/interface protocol and game loop

- Date: 2026-11-01
- Session ID: dbea6735-186c-4aa4-a54f-b768c61cc991 (`~/.claude/projects/-Users-nathanchalot-Code-RPGs-AloneVsFEear/`)
- Branch / PR: `e4-protocol-game-loop` / [https://github.com/NathanChalot/AloneVsFEear/pull/14](https://github.com/NathanChalot/AloneVsFEear/pull/14)
- Transcript: [transcripts/202611011026-e4-protocol-game-loop.txt](transcripts/202611011026-e4-protocol-game-loop.txt)
- Model: Opus 5.5, high effort

## Goal

The engine asks, the interface answers; the turn loop until death, insanity or quitting. Done when a scripted test walks 10 boxes and the terminal lets a player do the same.

## Done

- `engine/protocol.py`: `Choose(topic, options)` (topics Home, Action, Move), events `Arrival` and `Ended(end)`, `End` (dead, insane, quit), the `Interface` protocol (`ask`, `tell`), `Quit`.
- `engine/loop.py`: `play(game, interface) -> End`. Placeholder character if none (Life 8, Sanity 8, Food d6), Home if not chosen, then turns: action (move or quit), then a box among the targets in reading order. Answers that are not options are refused (`GameError`) and every answer is logged.
- `interface/scripted.py` (prepared answers, remembers what was asked and told) and `interface/terminal.py` (status line, map with numbered options, `@` and `H`, asks again after a wrong choice, Ctrl-D or Ctrl-C quits). Console script `alone-against-fear` and `python -m alone_against_fear`, with `--seed` and `--log-dir`; the log goes to `logs/` (git-ignored) at DEBUG.
- `RandomDice()` with no seed picks one and logs it.
- 21 new tests written first (scenario tests through the scripted interface, the terminal played with typed lines, the dice seed); 250 pass, ruff clean.
- Docs: `docs/architecture.md` (protocol, loop, interfaces, sequence and class diagrams; `test_town_map.py` added to the tests table), `CLAUDE.md` (protocol as an established fact, Play command), `design/rulings.md`, Readme, NextSession, model table in `WorkingWithClaude.md`.

## Decisions

- **Callback protocol** (the user, from three options: callback, generators, state machine). Nested choices stay simple; saving happens between turns; a GUI would run the engine in a thread.
- **A turn asks the action, then the box** (the user): one decision per request.
- **A fixed placeholder character** until E6 (the user): Life 8, Sanity 8, Food d6, no items.
- **No GitHub issue** for E4 (the user).
- **No log replay for now** (the user): the seed and the answers are still logged.
- **Dead before insane** when Life and Sanity reach 0 together (the user). Ruling in `design/rulings.md`.
- The terminal reads the game state to draw it; interfaces change the game only through their answers.
- **A project review session before E5** (the user): an adversarial step back in a fresh session, findings only.

## Open questions

- Request shapes beyond `Choose` (a number, an order of reactions): with the tasks that need them (E5 manual actions, E8 reactions).
- Saving mid-request is not possible with callbacks; saving between turns is the plan (saves are not a task yet).
- A Mermaid parse error in the new sequence diagram (a participant named `Loop` clashes with the `loop` keyword) was fixed. Once the user installed the Mermaid CLI (and set the Node.js version in `.tool-versions`), every diagram of the repository was rendered with `mmdc`: all 40 pass.

## Next

Project review (Opus, high effort), then E5: book mode (Sonnet).
