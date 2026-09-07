---
name: commits-go-straight-to-main
description: This repo commits and pushes directly to main; do not create feature branches or PRs
metadata:
  node_type: memory
  type: feedback
  originSessionId: 974e3dcf-8617-4308-b2bc-d89df5ff7d9a
  modified: 2026-09-07T00:10:52.441Z
---

# Commits go straight to main

Work in 10ulabs.com lands as a single commit pushed straight to `main`. There are no pull requests and no feature branches — I created `fix/778-...` once and the user's response was "I am confused because we only push to main".

**Why:** every workflow triggers on `push: branches: [main]` with no `pull_request` trigger, so a side branch gets no CI at all. The commit messages say "Verification is CI's", which only means anything once the commit is on `main`. A branch is therefore strictly worse than useless here.

**How to apply:** commit on `main` and push. Accept that the terraform-deploying workflows will run and deploy — that is the intended flow, not something to warn about each time. Issues are closed by a `Closes #NNN` trailer in the commit message rather than by a merged PR.
