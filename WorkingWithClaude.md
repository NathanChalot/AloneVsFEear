# Working with Claude

How the work sessions run, and recommendations for them: how many to expect, which model fits which kind of session, and how to prompt them. The plan itself is in [NextSession.md](NextSession.md), the roadmap in the [Readme](Readme.md). The recommendations were written in the MVP scope session; revise them as sessions show what works.

## How a session works

1. Start from [NextSession.md](NextSession.md), the [Readme](Readme.md) and the latest log in [`claude-logs/`](claude-logs/).
2. GitHub issues only for user stories and bugs, and only when needed; the PR then says `Closes #N`. An engine task with no user story gets no issue: the Readme entry is the task.
3. Work on a dedicated branch; one PR per session. Create the branch in the main checkout; use a worktree only when another session runs at the same time (see [Parallel sessions](#parallel-sessions)). During the session, Claude never commits or pushes without explicit permission.
4. End by updating the Readme (checkboxes, decisions), `NextSession.md` (remove the done session, adjust the plan, review the model and effort of each planned session in light of this one) and, if the code structure changed, [`docs/architecture.md`](docs/architecture.md).
5. Claude writes the session log in `claude-logs/YYYYMMDDHHmm-session-name.md`.
6. The user exports the transcript with `/export claude-logs/transcripts/YYYYMMDDHHmm-session-name.txt` (same name as the log).
7. Claude commits the session, pushes the branch, opens the PR, writes the PR link in the log and pushes again. This end-of-session commit and push is agreed once and for all, so the next session starts clean.

## How we develop

- **TDD** for the engine: tests from the task's "Done when" first, shown failing, then the code, then tidying.
- **BDD style in plain pytest**: scenario tests (given/when/then in names and comments) that a scripted interface plays through the engine, one or a few per user story. Gherkin feature files were considered and left out for now; reconsider if feature files should become the shared spec.
- Ambiguous rules: discuss with options, simpler version first if switchable, write the ruling in `design/rulings.md`, and only then the test and the code.
- Decided 2026-10-31 in the project setup session.

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
| Writing user stories and their issues | When a task has a player-facing story (E4 on) | Sonnet, medium effort; Opus if slicing the game into stories turns into a design debate |
| Routine setup | Project setup and GitHub planning | Sonnet (it posts to GitHub, so not Haiku) |
| Small chores | renames, housekeeping | Haiku; never for rules text, where a misreading costs more than it saves |

- Any task can turn out harder than planned: switch to Opus when a Sonnet session hits a design question.
- Fable: not used. It does not follow the same pricing rules as the other models.
- No default effort. Model and effort are picked per session in [NextSession.md](NextSession.md) and reviewed at each wrap-up with what the session showed: a session that struggled moves similar ones up, an easy one moves them down. The table above is only the starting point.
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

Only the YAML batches really parallelize: the engine tasks form a chain (only E8 ∥ E9 and E15 ∥ E12–E14 could overlap), and their design choices are made in conversation with the user. Running batches in parallel saves time, not cost, and reviewing several PRs becomes the bottleneck. Not tried yet: pilot with R2 and R3, then review it at wrap-up.

### Coordinator session

One session (Opus, high effort) talks with the user and launches one background agent per batch (Sonnet, medium effort), each in its own worktree and branch. Agents cannot ask the user: the coordinator gathers their doubts, asks the user in one go and sends the answers back to the right agent. Merge the previous session's PR first, start `claude` on an up-to-date `main`, pick the model with `/model`, then paste:

```
Coordinator session: YAML batches R2 and R3 in parallel. Read NextSession.md, the Readme
(Milestone 3), docs/content.md and the latest log in claude-logs/.

You coordinate; one background agent per batch does the copying. You never copy rules text
yourself.

Before any agent starts:
1. For each batch, list the content that is not a plain table (Skills, Arcane Skills, the
   weapon summary...) and propose its YAML shape and ID kind, with options. Ask me; nothing
   is launched until I answer. D1 (where plain stats go) stays open: keep stats as text
   unless I decide otherwise.
2. Confirm the branch names with me: r2-skills-harm, r3-weapons-items.

Then launch one agent per batch (Agent tool, isolation "worktree", model sonnet, effort
medium). Tell each agent:
- Work only on your branch, in your worktree. Create your own venv there
  (python -m venv .venv && .venv/bin/pip install -e '.[dev]'): the main checkout's venv
  runs the main checkout's code.
- The original PDFs are git-ignored and not in your worktree: read them from
  /Users/nathanchalot/Code/RPGs/AloneVsFEear/origin_rules/
- Copy every entry of your batch into YAML as R1 did (docs/content.md), using the shapes I
  agreed. Fix OCR damage in the YAML and the gameRules Markdown together, turn page
  references into table names, remove your tables from catalogue.yaml. Never change the
  meaning.
- Touch only your own files, your lines of catalogue.yaml and the KINDS you need. Never
  edit the Readme, NextSession.md, claude-logs/ or another batch's files.
- Never guess and never rule. When a reading is doubtful or the format does not fit, note
  it and carry on with the rest; stop and report only if the doubt blocks the batch.
- Tests and ruff must pass. Do not commit or push.
- No spoilers, no book page references in what you write.
- End with a report: what was copied, files touched, test results, and a numbered list
  of doubts (the passage, the possible readings, your suggestion).

While they run: tell me when each agent finishes. Gather every doubt and ask me in one
go, saying which batch each comes from. Send my answers back to the right agent
(SendMessage) and let it finish. Rulings go to design/rulings.md, kept switchable.

At the end, for each batch and only after I approve: commit on its branch, push, open its
PR. Then wrap up on a branch of your own (r2-r3-wrap-up): Readme checkboxes, NextSession
(including how this parallel run went, and whether to repeat it for R4 to R7), one log
per batch in claude-logs/, and ask me for this session's transcript export.
```

For other batches, change the batch names, branches and the non-table content to settle first.

### One terminal per batch

To talk with each batch directly instead, open one terminal per batch, each with its own worktree:

```
cd ~/Code/RPGs/AloneVsFEear
git worktree add ../AloneVsFEear-r2 -b r2-skills-harm
cd ../AloneVsFEear-r2 && claude
```

Use the YAML batch prompt above in each. The user then updates the Readme and NextSession after the batches, or leaves it to the next session.
