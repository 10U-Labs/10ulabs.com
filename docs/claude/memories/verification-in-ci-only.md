# Verifying in CI, never locally

Do not run tests, linters or builds locally to verify a change. Write the code and the tests, commit, push to `main`, and read the run. This covers every gate, not only pytest: `pylint`, `mypy`, `jscpd`, `yamllint`, `tflint`, the Terraform plan and every test tier all run from `.github/workflows/`, so a lint sweep is verified by pushing and reading the failed step rather than by running an analyser here file by file.

The reason is cost, and it is one-sided. GitHub Actions is free to the user; a local verification pass is paid for in tokens, and it re-runs work the push is about to do anyway. On 2026-08-19 a session built a virtualenv, installed eight packages, ran four suites and did a `git stash` pylint baseline comparison — all to confirm what a reading of its own diff had already shown, and all of it duplicated by the run that followed.

Reading the code locally is the other half of this and is cheap: `grep`, `sed -n` and file reads are how the findings that matter surface, and two suites asserting opposite things about one setting is the kind of defect only reading catches. The line is at *executing* checks. No virtualenv, no dependency install, no `pytest` or `pylint` run to confirm what CI confirms for free.

A change is not done when the push succeeds. Every workflow here is path-filtered, so one commit can start several, and the change is done when each one that fired is green rather than when the first is — see [find-a-run-by-the-full-hash](find-a-run-by-the-full-hash.md) for the trap in finding them. `workflowctl.yml` runs on every push to `main` and carries the tree-wide `pylint`, `mypy` and `jscpd` passes, so it is in nearly every run and is what reports a defect in a file no other workflow claims.

The consequence for TDD is that the red observation and the green one both belong to CI — see [tdd-workflow](tdd-workflow.md). Verify with `gh run list`, `gh run watch` and `gh run view --log-failed`.
