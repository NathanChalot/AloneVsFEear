# Alone Against Fear — project guide for Claude

Digital solo play of **Alone Against Fear** (Four Against Darkness engine). Read [`Readme.md`](Readme.md) (roadmap, decisions), [`NextSession.md`](NextSession.md) and the latest log in `claude-logs/` at the start of a session. How a session runs: [`WorkingWithClaude.md`](WorkingWithClaude.md).

## Working rules

- Small planned sessions, one branch and one PR each. **Never commit or push without permission**, except the agreed end-of-session wrap-up (update Readme, NextSession and, if the code structure changed, `docs/architecture.md`; write the log; ask for the transcript export, commit, push, PR, add the PR link to the log).
- Design before code: model in domain terms in `design/` first. Decide only what is worth deciding yet; propose, do not decide.
- **Rule interpretations**: suggest options, never rule. Ask first; rulings go to `design/rulings.md`, kept switchable.
- **No spoilers**: event names are fine, no plot details in chat or docs.
- **No book page references** in committed docs; transcripts stay verbatim.
- The rules text is from a commercial book: the repository stays private; `origin_rules/` (original PDFs) is git-ignored.

## Established facts

- Python, terminal CLI first. The engine is UI-agnostic: it never reads input or prints; it asks requests, an interface answers. No genAI code in the engine.
- **Whole model, thin content.** The engine follows the whole design; only a slice of content is written. Anything unwritten goes through **book mode**: show the entry's text, the player applies it with manual actions (which still go through the rules).
- **Rules text in YAML** (stable ID per table, entry, creature, item, event, Skill); **behaviour in Python**, keyed by the same ID. Plain data placement (stats, weights) is open until E6 (D1). The Markdown in `gameRules/` is the readable copy, fixed together with the YAML.
- Game state refers to content by ID and never holds code (saving = saving the campaign).
- MVP scope and task order: [`design/mvp-scope.md`](design/mvp-scope.md).

## Layout and commands

- `src/alone_against_fear/` — package; `src/alone_against_fear/content/` — rules text in YAML (layout and IDs: [`design/content.md`](design/content.md)); `tests/` — pytest; `design/` — domain design (Mermaid); `docs/` — code documentation ([`docs/architecture.md`](docs/architecture.md): packages, classes, who calls whom); `gameRules/` — extracted rules; `claude-logs/` — session logs.
- Setup: `python -m venv .venv && .venv/bin/pip install -e '.[dev]'`
- Tests: `.venv/bin/pytest`  ·  Lint: `.venv/bin/ruff check .`  ·  Format: `.venv/bin/ruff format .`
- Tests first; stop at the task's "Done when".

## Testing approach

- **TDD** for the engine: write the tests from the task's "Done when" line, see them fail, implement, tidy. Unit tests per rule; dice are seeded so runs are reproducible.
- **BDD style in plain pytest** (no Gherkin): scenario tests named and commented given/when/then, driven by a scripted interface that answers the engine's requests. One or a few scenarios per user story or session issue.
- A test per rule, written from the Markdown rules text, so a misreading shows up as a failing test.
- **Ambiguous rules** (tests are rulings written as code): discuss first, with options proposed; if switchable, start with the simpler version; write the ruling in `design/rulings.md`; only then write the test and the code.
