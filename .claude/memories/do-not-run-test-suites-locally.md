---
name: do-not-run-test-suites-locally
description: Don't run the repo's test suites, linters or other verification locally — push and let CI verify.
metadata:
  type: feedback
---

# Don't verify locally

Do not run pytest, pylint, mypy or the other verification steps locally to check work in this repo. Push the commit and let the GitHub Actions workflows verify it. Do not stand up a virtualenv to replicate the workflow jobs, and do not recite local job results in commit bodies.

**Why:** Running the suites locally burns Claude tokens (setting up interpreters/deps, reading output) while CI runs the same checks for free. The repo says the same thing in its own history: `Verification is CI's` closes commit bodies going back many commits.

**How to apply:** Make the change, commit, push. State in the commit body which jobs bound the change and what they will check, rather than pre-verifying it here. Where a property can be established statically — comparing the parsed AST before and after a refactor, say — do that instead of running the suite. If a local run is genuinely the only way to answer something, ask first. See [[memories-live-in-dot-claude-memories]] for where this file lives.
