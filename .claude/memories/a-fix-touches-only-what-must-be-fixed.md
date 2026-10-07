---
name: a-fix-touches-only-what-must-be-fixed
description: A fix commit changes only what must be fixed; it never touches another path just to make a workflow run
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:55:17.051Z
---

# A fix touches only what must be fixed

A commit that fixes a red run changes what is broken and nothing else. It does not reach into another path to set off a workflow the fix itself would not.

**Why:** The user rejected api.10ulabs.com's `a-fix-forward-fires-every-stack-the-red-commit-changed` on 2026-10-06, which has a fix touch a shared path so every workflow the red commit changed runs again: "a fix should only touch what must be fixed, nothing else."

**How to apply:** Scope the fix to the failure the log names, per [[a-rejected-push-is-fixed-forward]] and [[fixing-a-red-run]]. Do not add an edit whose only purpose is to make a workflow run.
