---
name: confirming-a-push-closed-its-issues
description: "GitHub can leave every issue a pushed commit names with Closes open, so once a push's runs are clean its closes are checked, and made by hand where they did not take"
metadata:
  node_type: memory
  type: project
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:52:35.086Z
---

# Confirming that a push closed its issues

GitHub can push a commit to `main` without acting on any of its `Closes #N` lines. In deltahdl a commit naming 64 issues in a 103 KB message closed none of them, while one naming 19 in a 27 KB message closed all of its issues. Whether the count or the size is at fault is not known.

**Why:** an issue left open after its fix landed looks unsolved, so the autopilot loop takes it up again and works on code that already satisfies it.

**How to apply:** once a push's runs are clean, check that every issue its message closes is closed, with `gh issue view N --json state`. Close any still open with `gh issue close N --reason completed`, commenting which commit solved it. Keep a batch's message to one paragraph per issue ([[a-push-solves-every-open-issue-of-one-stack]]) rather than a subject that joins dozens of them. See [[an-issue-is-closed-by-its-commit]].
