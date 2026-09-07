---
name: memories-live-in-dot-claude-memories
description: This project's memories are in .claude/memories/, set by an absolute autoMemoryDirectory in .claude/settings.local.json — not the user-scoped default path.
metadata:
  type: project
---

# Memories live in .claude/memories

Read and write this project's memories in `.claude/memories/`, inside the repo. `.claude/settings.json` (tracked) sets `autoMemoryEnabled: true`; `.claude/settings.local.json` (gitignored) sets `autoMemoryDirectory` to the absolute path `/Users/jdrowne/Git/10U-Labs/10ulabs.com/.claude/memories/`.

**Why:** `autoMemoryDirectory` only accepts an absolute or `~/`-prefixed path. It was originally set to the relative `.claude/memories/`, which the resolver rejects and silently replaces with the user-scoped default — no warning. Memories written on 2026-09-05 and 2026-09-06 landed in `~/.claude/projects/-Users-jdrowne-Git-10U-Labs-10ulabs-com/memory/` instead, splitting the store so recorded guidance was missed. The path is machine-specific, so it lives in `settings.local.json` rather than the tracked `settings.json`.

**The path is resolved once per `claude` process and cached, so fixing the setting does not fix the running session.** In the binary, `resolveEntry` is memoised on a key of cwd and trust state — not on the contents or mtime of any settings file — so the directory a process starts with is the directory it keeps for its whole life. `/clear` does not reset it; it starts a new transcript inside the same process.

That produced a silent regression on 2026-09-06. The `claude` process was launched 2026-09-05 23:32, when `.claude/settings.json` still held the relative `.claude/memories/`, so it resolved to the user-scoped fallback. 8288d8e1 at 20:36 the next day fixed the setting **and moved `commits-go-straight-to-main.md` out of that fallback directory**, leaving it empty. The long-running process went from seeing one memory to seeing none, and its system prompt still named the fallback path. In the session that followed, both behavioural memories were broken — a branch was created and a virtualenv stood up to run the suites locally.

**How to apply:** After changing `autoMemoryDirectory`, restart `claude`. The change has no effect on any process already running, however correct it is. In a session whose system prompt names the `~/.claude/projects/.../memory/` path, do not conclude the setting is broken — check `.claude/settings.local.json` first, and if it holds an absolute path the setting is fine and this process is simply stale. Either way, read `.claude/memories/*.md` by hand before doing work, and write there. Keep the value absolute or `~/`-prefixed; a relative path is rejected silently and falls back to the same place. See [[do-not-run-test-suites-locally]], [[commits-go-straight-to-main]] and [[lint-jobs-take-whole-roots]].
