---
name: new-assert-checks-are-their-own-repo
description: A new repo-wide check is a standalone 10U-Labs repo published to PyPI, not a script under scripts/.
metadata:
  type: project
---

# A new check is its own repo, cloned from the newest one

Every repo-wide rule this project enforces lives in its own public repository in the 10U-Labs org, published to PyPI, installed with `pip` in CI and run as its own job over whole roots. There are thirteen as of 2026-09-08, `assert-no-comments` through `assert-pytest-test-can-fail`. Nothing of this kind belongs under `scripts/`, which holds only `invalidate_cloudfront.py`.

To add one, clone the most recently created `assert-*` repo as the template (`gh repo list 10U-Labs --json name,createdAt`), rename the package and the CLI throughout, replace `src/<pkg>/scanner.py`, `test/samples.py` and the rule-specific test classes, and keep `cli.py` as it stands — it is identical across the family. PyPI trusted publishing is already configured for the org, so `gh repo create ... --push` releases the package on the first green run of `release.yml`; no pypi.org setup is needed.

**Why:** The issue that prompted `assert-pytest-test-can-fail` proposed a script under `scripts/` with tests under `test/scripts/`, which was the old convention and would have been rejected in review. The family shape also gets the check 100% branch coverage, mypy `--strict`, pylint `--fail-on=C,R,W` and jscpd at threshold 0 for free, because the template carries those jobs.

**How to apply:** Copy the newest sibling rather than writing a repo from scratch, then add the job to each workflow that should run it and to that workflow's gate `needs:`. See [[lint-jobs-take-whole-roots]] for the roots the job takes and [[do-not-run-test-suites-locally]] for verifying it.
