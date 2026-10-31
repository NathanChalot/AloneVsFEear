# Working with Claude

How the work sessions run, and recommendations for them: how many to expect, which model fits which kind of session, and how to prompt them. The plan itself is in [NextSession.md](NextSession.md), the roadmap in the [Readme](Readme.md). The recommendations were written in the MVP scope session; revise them as sessions show what works.

## How a session works

1. Start from [NextSession.md](NextSession.md), the [Readme](Readme.md) and the latest log in [`claude-logs/`](claude-logs/).
2. Work in a dedicated worktree and branch; one PR per session. During the session, Claude never commits or pushes without explicit permission.
3. End by updating the Readme (checkboxes, decisions) and `NextSession.md` (remove the done session, adjust the plan).
4. Claude writes the session log in `claude-logs/YYYYMMDDHHmm-session-name.md`.
5. The user exports the transcript with `/export claude-logs/transcripts/YYYYMMDDHHmm-session-name.txt` (same name as the log).
6. Claude commits the session, pushes the branch, opens the PR, writes the PR link in the log and pushes again. This end-of-session commit and push is agreed once and for all, so the next session starts clean.

## How many sessions

Rough estimates, for sessions of about 1.5 hours. Not commitments.

| Phase | Sessions |
| --- | --- |
| Project setup and GitHub planning | 1 |
| R1 (YAML layout, IDs, first tables) | 1 |
| Engine skeleton E1–E5 | 3–4 |
| YAML batches R2–R7 | 5–6, can run in parallel |
| Step 1, E6–E17 | 10–14 (E7, E8, E10 and E12 are the big ones) |
| Step 2, E18–E20 | 3–4 |

- Python code starts with R1 (session 2), engine code with E1 (session 3).
- A game playable in book mode around session 6 or 7; step 1 playable around session 20; the MVP in roughly 25 to 30 sessions.

## Which model for which session

| Kind of session | Tasks | Model |
| --- | --- | --- |
| Architecture: choices later tasks depend on | R1 (IDs), E1 + E2, E4, E6 (rest of D1), E7, E8, E10, E12 | Opus, high effort |
| Clear spec: the design already says what to build | E3, E5, E9, E11, E13–E20 | Sonnet |
| Copying rules text | R2–R7 | Sonnet, medium effort; Opus for a messy batch (events) |
| Routine setup | Project setup and GitHub planning | Sonnet (it posts to GitHub, so not Haiku) |
| Small chores | renames, housekeeping | Haiku; never for rules text, where a misreading costs more than it saves |

- Any task can turn out harder than planned: switch to Opus when a Sonnet session hits a design question.
- Fable: no reliable information on what it is best at yet. Try it on one session and compare before using it more.
- The memory files (ask before ruling, no spoilers, commit rules) load the same way whatever the model.

## Prompts

Once `CLAUDE.md` holds the conventions (project setup session), prompts can stay short: the session workflow is already known.

Architecture session (design, then code):

```
Next session: E4 (engine/interface protocol). Read NextSession.md, the Readme and the latest log.
Restate the goal, then propose the design with 2–3 options before any code.
Tests first; stop at the task's "Done when". Ask before any rule interpretation.
```

Clear-spec code session:

```
Next session: E9 (inventory). Read the task and design/inventory.md. Short plan, then implement
with tests. Flag anything the design doesn't cover instead of deciding it.
```

YAML batch:

```
Next session: R4 (creatures to YAML). Copy every entry from the original PDFs in origin_rules/,
fixing OCR damage in the YAML and the Markdown. Never change the meaning; list every doubtful
reading for me at the end instead of guessing.
```

## Parallel sessions

The YAML batches do not touch the engine, so a batch can run in its own worktree and branch while an engine session runs in another. Each still ends with its own log and PR.
