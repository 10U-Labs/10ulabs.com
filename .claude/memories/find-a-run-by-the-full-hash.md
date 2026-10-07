---
name: find-a-run-by-the-full-hash
description: "gh run list --commit returns an empty list for a short hash, so pass the full 40-character hash from git rev-parse HEAD"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:56:47.286Z
---

# Find a run by the full hash

Find a push's run by the full forty-character hash, from `git rev-parse HEAD`, never by the short hash `git log --oneline` or a commit message shows.

**Why:** `gh run list --commit` silently returns an empty list for a short hash, which is indistinguishable from a run that has not started, so a wait on it polls until its timeout while the run has long passed. It happened in this repository on 2026-10-06, when `gh run list --commit 25ca784b` listed nothing for a run that existed.

**How to apply:** take the hash from `git rev-parse HEAD` right after the push, and pass it whole: `gh run list --commit "$(git rev-parse HEAD)"`, or match `headSha` in `gh run list --json headSha` against it. The wait itself runs in the background, per [[a-wait-runs-in-the-background]].
