---
name: memories-live-in-dot-claude-memories
description: This project's memories are in .claude/memories/, set by an absolute autoMemoryDirectory in .claude/settings.local.json — not the user-scoped default path.
metadata:
  type: project
---

# Memories live in .claude/memories

Read and write this project's memories in `.claude/memories/`, inside the repo. `.claude/settings.json` (tracked) sets `autoMemoryEnabled: true`; `.claude/settings.local.json` (gitignored) sets `autoMemoryDirectory` to the absolute path `/Users/jdrowne/Git/10U-Labs/10ulabs.com/.claude/memories/`.

**Why:** `autoMemoryDirectory` only accepts an absolute or `~/`-prefixed path. It was originally set to the relative `.claude/memories/`, which the resolver rejects and silently replaces with the user-scoped default — no warning. Memories written on 2026-09-05 and 2026-09-06 landed in `~/.claude/projects/-Users-jdrowne-Git-10U-Labs-10ulabs-com/memory/` instead, splitting the store so recorded guidance was missed. The path is machine-specific, so it lives in `settings.local.json` rather than the tracked `settings.json`.

**How to apply:** If a session's system prompt names the `~/.claude/projects/.../memory/` path, `settings.local.json` is missing or its path is wrong — restore it before writing anything, then write here. Keep `autoMemoryDirectory` absolute; a relative path fails silently. See [[do-not-run-test-suites-locally]] and [[commits-go-straight-to-main]].
