---
name: memories-live-in-dot-claude-memories
description: This project's memories are in .claude/memories/, set by autoMemoryDirectory in .claude/settings.json — not the user-scoped default path.
metadata:
  type: project
---

Read and write this project's memories in `.claude/memories/`, inside the repo. `.claude/settings.json` sets `autoMemoryDirectory` to that path with `autoMemoryEnabled: true`.

**Why:** The default memory path named in the system prompt is user-scoped (`~/.claude/projects/-Users-jdrowne-Git-10U-Labs-10ulabs-com/memory/`) and is empty. On 2026-09-05 a memory was written there and the existing project memory at [[do-not-run-test-suites-locally]] was missed, so guidance already recorded was not followed.

**How to apply:** Check `.claude/settings.json` for `autoMemoryDirectory` at the start of a session and read `MEMORY.md` from the directory it names.
