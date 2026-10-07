---
name: a-rejected-push-is-fixed-forward
description: "A push rejected by CI is answered with a follow-up commit, never an amend and force-push"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:52:39.187Z
---

# A rejected push is fixed forward

A push rejected by CI is answered with a follow-up commit. Do not amend and force-push.

**Why:** `main` is published by the time the run reports ([[commits-go-straight-to-main]]), and rewriting it discards what was tried. Where this collides with solving a batch in a single push, verifying only in CI ([[do-not-run-test-suites-locally]]) is the rule that holds and the extra commit is its cost.

**How to apply:** read the whole failed log, not its first error, and sweep the change for other instances of the same shape before pushing the fix. A run reports every gate at once, so a fix that answers only the first line of the log buys one more red run. Who fixes it, and in which push, is [[fixing-a-red-run]].
