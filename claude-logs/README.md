# Claude session logs

One file per work session with Claude, named `YYYYMMDDHHmm-session-name.md` (start time, kebab-case name).

Logs are short summaries. The [Readme](../Readme.md) is the source of truth for the current state and roadmap, [NextSession.md](../NextSession.md) for the upcoming plan; logs keep the history: what was decided, why, and what was left open.

## Transcripts

Full transcripts live in [`transcripts/`](transcripts/), with the same name as their log and a `.txt` extension. Export one at the end of a session with:

```
/export claude-logs/transcripts/YYYYMMDDHHmm-session-name.txt
```

The raw Claude Code transcript (JSONL) stays in `~/.claude/projects/<project>/<session-id>.jsonl`; the session ID recorded in each log identifies it.

## Template

Write the log at the end of each session:

```markdown
# <Session name>

- Date: YYYY-MM-DD
- Session ID: <Claude Code session id>
- Branch: <branch> (the PR is found from it)
- Model: <model, effort>
- Transcript: [transcripts/YYYYMMDDHHmm-session-name.txt](transcripts/YYYYMMDDHHmm-session-name.txt)

## Goal

## Done

## Decisions
- <decision> — <why>; <alternatives rejected>

## Open questions

## Next
```
