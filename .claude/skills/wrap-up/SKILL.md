---
name: wrap-up
description: End the current work session of Alone Against Fear - drift check, Readme, NextSession, architecture, the log, the transcript export (the user types /export; Claude waits for the file), then commit, push and open the PR. Use when the user types /wrap-up.
disable-model-invocation: true
---

# Wrap up a session

The agreed end of a session ([WorkingWithClaude](../../../WorkingWithClaude.md#how-a-session-works), steps 4 to 8). CLAUDE.md agrees this commit and push once and for all; everything else still needs the user's permission. If work is still uncommitted from the session's own tasks, propose its commits first (split as usual) and wait for the go.

## 1. Drift check

Search the repository for the names, numbers, wording and behaviours the session changed, and fix every stale mention (`docs/`, `design/`, the Readme, NextSession, WorkingWithClaude, comments). Write, move or drop the session's pending tests and "decide when implementing" items; remove the NextSession reminders it resolved. Anything noticed outside the session's scope is not fixed: one line under "For the next review" in NextSession.

## 2. Update the docs

- `Readme.md`: the session's entry (checkbox, Decided, Done when met or not), the Status line, the decisions, How to play when what a player can do changed, "Later" for what was pushed past the MVP.
- `NextSession.md`: remove the done session, adjust the plan, review the next session's model and effort in light of this one, and write **"Drills to play before the next session"**: the drills of the features the next session builds on, leaving out a drill whose content is not copied yet. Never a blocker.
- `docs/architecture.md`, if the code structure changed.

No spoilers and no book page references (CLAUDE.md).

## 3. The log

Write `claude-logs/YYYYMMDDHHmm-session-name.md`, the time being the session's start, in the shape of the previous log: date, session ID, branch, model and effort, transcript link; Goal and Done when; Done; Decisions (with what was rejected); mistakes, if any; Open questions; Next. If the session triaged feedback notes, say what became of each.

## 4. The transcript export

The user has to type `/export` (a built-in command: no skill, hook or shell can run it), and it sends Claude no message. So, before asking for it, start a background wait for the file, so Claude is woken when it appears:

```
f=claude-logs/transcripts/<same name as the log>.txt
for i in $(seq 900); do [ -s "$f" ] && sleep 2 && echo "exported: $f" && exit 0; sleep 2; done; echo "no export after 30 minutes"; exit 1
```

Run it with the Bash tool and `run_in_background: true`. Then give the user the exact line to type, `/export claude-logs/transcripts/<name>.txt`, and say that nothing more is needed from them: Claude goes on once the file is there. When the wait ends, check the file is not empty and go on; if it timed out, ask.

## 5. Commit, push, open the PR

- Run the tests and the linter (`.venv/bin/pytest -q`, `.venv/bin/ruff check .`).
- Commit the wrap-up (docs, log, transcript, feedback notes) in its own commit, in a command separate from the push.
- Write the PR body to a scratchpad file: what the session did, the decisions, the test count, `Closes #N` if there is an issue.
- `git push -u origin <branch>`, then `gh pr create --base main --title "<ID>: <title>" --body-file <file>`.
- If auto mode refuses the push or the PR, do not work around it: give the user the two `!` commands to run.
- End with the PR link, and the drills to play before the next session.
