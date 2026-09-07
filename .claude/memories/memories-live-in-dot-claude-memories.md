---
name: memories-live-in-dot-claude-memories
description: This project's memories are in .claude/memories/, set by an absolute autoMemoryDirectory in .claude/settings.local.json — not the user-scoped default path.
metadata:
  type: project
---

# Memories live in .claude/memories

Read and write this project's memories in `.claude/memories/`, inside the repo. `.claude/settings.json` (tracked) sets `autoMemoryEnabled: true`; `.claude/settings.local.json` (gitignored) sets `autoMemoryDirectory` to the absolute path `/Users/jdrowne/Git/10U-Labs/10ulabs.com/.claude/memories/`.

**Why:** `autoMemoryDirectory` only accepts an absolute or `~/`-prefixed path. It was originally set to the relative `.claude/memories/`, which the resolver rejects and silently replaces with the user-scoped default — no warning. Memories written on 2026-09-05 and 2026-09-06 landed in `~/.claude/projects/-Users-jdrowne-Git-10U-Labs-10ulabs-com/memory/` instead, splitting the store so recorded guidance was missed. The path is machine-specific, so it lives in `settings.local.json` rather than the tracked `settings.json`.

**A correct setting is not enough on its own.** On 2026-09-06, with `settings.local.json` already holding the absolute path, a session's system prompt still named `~/.claude/projects/-Users-jdrowne-Git-10U-Labs-10ulabs-com/memory/` and none of the memories in `.claude/memories/` were surfaced. Both behavioural memories were then broken in that session — a branch was created and local verification was run. The cause of the mismatch is not established; only the symptom is.

**How to apply:** Do not trust the system prompt's memory path. At the start of any session in this repo, read `.claude/memories/` directly — `cat .claude/memories/*.md` — before doing work, and write there. If the prompt names the `~/.claude/projects/.../memory/` path, check whether `settings.local.json` exists and holds an absolute path; if it does, the setting is fine and the memories simply were not loaded, so read them by hand. Keep `autoMemoryDirectory` absolute; a relative path fails silently. See [[do-not-run-test-suites-locally]], [[commits-go-straight-to-main]] and [[lint-jobs-take-whole-roots]].
