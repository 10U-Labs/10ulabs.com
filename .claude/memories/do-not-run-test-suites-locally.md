---
name: do-not-run-test-suites-locally
description: Don't run the repo's test suites, linters or other verification locally — push and let CI verify.
metadata:
  type: feedback
---

Do not run pytest, pylint, mypy or the other verification steps locally to check work in this repo. Push the commit and let the GitHub Actions workflows verify it.

**Why:** Running the suites locally burns Claude tokens (setting up interpreters/deps, reading output) while CI runs the same checks for free.

**How to apply:** Make the change, commit, push. Report what CI will check rather than pre-verifying it here. If a local run is genuinely the only way to answer something, ask first.
