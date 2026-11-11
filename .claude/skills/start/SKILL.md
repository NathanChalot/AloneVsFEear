---
name: start
description: Start the next planned work session of Alone Against Fear - read the plan, check the setup, give a plain-words summary, then run the session. Use when the user types /start, optionally with a session name (/start E9).
argument-hint: "[session, e.g. E9; default: the first one planned in NextSession.md]"
disable-model-invocation: true
---

# Start a session

The session to run: `$ARGUMENTS` if given, otherwise the first entry of the Plan in `NextSession.md`.

## 1. Read

- `NextSession.md`: the session's line in the Plan (model and effort), the Reminders, "For the next review" when the session is a review or a playtest.
- `Readme.md`: the session's roadmap entry (description, Rules, Design, Decided, Open, Done when, Depends on) and the Status.
- The latest log in `claude-logs/` (the newest `YYYYMMDDHHmm-*.md`, not `README.md`).
- `WorkingWithClaude.md`: how a session works, and the prompt template that matches the session's kind (architecture, clear spec, YAML batch, consistency review, playtest).
- The design pages and rules the roadmap entry links to, as far as the summary needs them.

## 2. Check

- `git status` and `git log`: on `main`, clean, up to date with `origin/main` (`git pull --ff-only`), and the previous session's PR merged (`gh pr list --state all --limit 3`). If not, say what is off and ask before going further.
- The session's "Depends on" are checked in the Readme.
- The model and effort planned in NextSession against the model you run on. If they differ, say so plainly so the user can switch with `/model` before anything else.
- Tests pass: `.venv/bin/pytest -q`.

## 3. Summarise, in plain words

Short, for someone who has not looked at the project for a while. No spoilers, no book page references (CLAUDE.md). Use this shape:

```
Where we are
  Two or three sentences: what the game can do today, and what the last session added.

This session: <ID> — <title>
  Goal: one or two sentences, in player terms where possible.
  Done when: the roadmap's Done when, in plain words.

How it will go
  The kind of session and its steps (design first and options, or a short plan;
  tests first; commits; the wrap-up).

Before we start
  Planned model and effort, and the one you run on.
  The reminders from NextSession that concern this session, and anything the
  checks found.
```

Then stop and wait for the user's go.

## 4. Run

Once the user says go: create the session's branch from `main` (a plain branch, not a worktree, unless another session runs at the same time), then follow the prompt template for the session's kind and the working rules of CLAUDE.md.
