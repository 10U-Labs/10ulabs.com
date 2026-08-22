# Working in 10ulabs.com

These are the standing conventions for working in this repository. Each section links the longer write-up behind it, one note per topic under `docs/claude/memories/`; [docs/claude/memories/README.md](docs/claude/memories/README.md) indexes them all.

## Verification

CI is the source of truth. Do not run tests, linters or builds locally to verify a change — write the code and the tests, commit, push to `main`, and read the run with `gh run list` / `gh run watch` / `gh run view --log-failed`. Local runs cost tokens and pull in dependencies this machine does not otherwise need; CI is free and checks every gate at once. Reading the code locally is still right and cheap — `grep` and file reads are how the useful findings surface, and two suites asserting opposite things about one setting is the kind of thing only reading catches. The line is at executing checks: no virtualenv, no dependency install, no `pytest` or `pylint` run to confirm what CI confirms for free.

A push starts several workflows, because every workflow here is path-filtered and one commit can touch the paths of more than one. The change is done when each workflow that fired is green, not when the first one is. Nearly every workflow carries the tree-wide `pylint`, `mypy` and `jscpd` passes over `lib/python/` and `test/` as steps of its own, so whichever run fired is the one that reports a defect in a file no workflow claims. `scripts.yml` is the one to look for when nothing deployed: it runs on `.github/`, `lib/python/`, `scripts/` and their tests, and carries the contract tests over the workflow files.

Find the run by the full forty-character hash from `git rev-parse HEAD`. `gh run list --commit` silently returns an empty list for the short hash `git log --oneline` prints, which is indistinguishable from a run that has not started, so anything that polls should list recent runs and match `headSha` by prefix locally.

Longer: [verification-in-ci-only](docs/claude/memories/verification-in-ci-only.md), [find-a-run-by-the-full-hash](docs/claude/memories/find-a-run-by-the-full-hash.md).

## Commits

Work goes straight to `main` as direct commits. Do not create a feature branch, do not open a pull request, and do not structure advice around a review cycle. The merge commits below `33031228` are the older pull-request habit rather than the current one; everything above it is a direct commit. There is no pull-request buffer, so CI is the only review there is and the tests land in the same commit as the code they cover.

One issue is solved by one commit and one push, and the commit closes its issue in the message: `Closes #490` in `31f0066f`, or the qualified `Fixes <owner>/<repo>#<n>` that `1e45d1f9` carries when the issue lives in another repository. That line is what drains the queue — an issue solved by a push that does not carry it stays open and is picked up again on the next pass. An issue that cannot be done in one commit is two issues, and filing the second is the answer rather than spreading one issue across pushes.

A push rejected by CI is answered with a follow-up commit. Do not amend and force-push: `main` is published by the time the run reports, and rewriting it discards what was tried. The static-analysis checks here are steps of a single `deploy` job rather than jobs of their own, and a job stops at its first failing step, so a run reports the first failing check and nothing about the ones behind it. Read the whole failed step rather than its first line — one `pylint` step reports every finding it has — and sweep the change for other instances of the same shape before pushing the fix, because the step after it stays unread until this one passes.

Longer: [commit-straight-to-main](docs/claude/memories/commit-straight-to-main.md), [a-rejected-push-is-fixed-forward](docs/claude/memories/a-rejected-push-is-fixed-forward.md).

## Tests

We do TDD: the test is written first, then the code that makes it pass. Test-first means authoring order — the red and the green observations belong to CI, since nothing runs locally.

Read `docs/tenets/tests/` before implementing. Unit tests alone are not sufficient: add coverage at every tier the change touches, one assert per pytest. `Assert one assert per pytest` is a step in every one of the twenty-five workflows, so a test with two asserts fails the push rather than being noticed in review.

The four tier files there — `UNIT_TESTS.md`, `PRE_DEPLOYMENT_INTEGRATION_TESTS.md`, `POST_DEPLOYMENT_INTEGRATION_TESTS.md` and `E2E_TESTS.md` — are tenets, not a description of the suite. They name no language, tool, directory or resource, because the repository already states all of that and a second copy drifts. When a tenet and the repository disagree, the repository is what changes; editing a tenet to match the code is backwards. `OVERVIEW.md` beside them is the opposite kind of document and is read the opposite way: it describes this suite by name, down to the conftest levels and the four static-analysis steps, so where it and the tree disagree it is `OVERVIEW.md` that is out of date.

A subsystem that deploys is laid out as `pre_deployment/{unit,integration}` and `post_deployment/{integration,e2e}`, and a tier directory appears only when there is a test to put in it — everything under `test/api/` and `test/www/`, plus `test/bootstrap/` and `test/github/workflows/`. The deployment phase is the top split because neither post-deployment tier can be attempted until there is a deployment to call. What decides the tier is what the test reads, not how end-to-end it looks: `test/www/paths/home/pre_deployment/integration/test_05_existence.py` reads the Terraform on disk, while `test/www/paths/home/post_deployment/e2e/spa-routing.spec.ts` drives `https://10ulabs.com` through Playwright.

Code under `lib/` deploys nothing of its own and so carries no such split. `test/lib/python/` mirrors the package and stops — `test/lib/python/test_ec2_fleet/` holds the tests for `lib/python/ec2_fleet/`, with no tier directory in between — and `test/lib/terraform/` names the module and then the one tier it has, as in `test/lib/terraform/s3_bucket/unit/test_s3_bucket_module.py`. Two of the four directories that owe tests are `lib/python/` and `lib/terraform/`, so this is the common case rather than the exception.

Longer: [tdd-workflow](docs/claude/memories/tdd-workflow.md), [read-test-tenets-first](docs/claude/memories/read-test-tenets-first.md), [tenets-are-generic](docs/claude/memories/tenets-are-generic.md), [the-test-tree-splits-on-deployment-phase](docs/claude/memories/the-test-tree-splits-on-deployment-phase.md).

## Markdown

Markdown is not hard-wrapped. There is no column limit on `.md` files here, and none on the bodies of GitHub issues: write each paragraph as one line and let the reader wrap it. Nothing enforces a width — the repository has no `markdownlint` and no `yamllint` configuration file, and none of the twenty-five workflows runs a markdown linter. The hard-wrapped files that used to sit under `products/` left with it, so nothing here is wrapped now; match this rule rather than the file next to you.

Longer: [markdown-is-not-hard-wrapped](docs/claude/memories/markdown-is-not-hard-wrapped.md).

## Issues

An issue about the program has six sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It", "Why Integration Tests Did Not Catch It", "Why E2E Tests Did Not Catch It", "Which Unit, Integration, or E2E regression tests would prevent this from happening again?", "Proposed Solution". Every such issue has all six; where a tier does not exist for the part of the program in question, saying so is the finding rather than a reason to drop the section. The regression section names the tests to write, each with its tier and its assertion, and is separate from the solution so that a fix cannot ship with the coverage folded into its last paragraph.

The four test sections belong to the program and to nothing else. The program is what a test tier can run: `src/`, `lib/python/`, `lib/terraform/` and `scripts/`. An issue about the configs in `etc/`, the workflow files in `.github/`, the documentation in `docs/` or the hardware work in `products/` has two sections, "Problem" and "Proposed Solution", and owes no tests — a test over a file no tier runs only reads a value back and asserts what it just read. Most of the open queue is of this second kind, so the split is by directory and there is nothing to weigh. `test/` falls on both sides: the machinery a tier runs on is program code and gets six, conftest fixtures included, because it can make a whole tier report the wrong answer; the assertions themselves get two, since asking why the unit tests did not catch a defective unit test answers itself. What the defect is in decides this, not what the fix touches.

Write plain, ordinary English prose. Tables where a table genuinely reads better, bullets only when enumerating things, never to break up an argument. Back claims with numbers computed from the repository's own data, and say how they were computed. Each section opens with a plain sentence saying what the thing is and what it is for before any identifier appears; "Problem" says what the code is there to do before it says what is wrong with it, and says what the defect costs within its first few lines.

An issue is definitive. Its `Proposed Solution` names one change — this function, this file, this algorithm — because the issue is the instruction to whoever picks it up and they were not in the conversation that produced it. Never file "either X or Y", a menu with a recommendation, or a question left for the reader; an issue that ends with something still to decide is not finished. Where a draft reaches a genuine fork, stop and ask which branch and then write down the branch that came back, so the asking happens before the filing rather than inside the body. Naming the rejected alternative and why it lost is still worth writing, because it stops the same ground being covered twice; what is not allowed is leaving the choice open. For issues already on disk that carry an either, do not pick: ask which one before editing a file, however clearly the text leans toward one of them, and ask before there is a draft, because a draft turns the question into a request to approve what is already done.

A filed issue is placed in the queue before the work goes on, with a `blocked_by` edge either onto the issue it unblocks or onto the tail of the sequence. `.claude/skills/autopilot/SKILL.md` states the three cases and the `gh api` call that writes the edge.

Longer: [how-issues-are-written](docs/claude/memories/how-issues-are-written.md), [an-issue-states-one-solution](docs/claude/memories/an-issue-states-one-solution.md).

## Notes

A convention learned in a session belongs in this repository: a paragraph in this file and a topic file under `docs/claude/memories/`, linked from both indexes — or a file under `docs/tenets/` when it says what a kind of work is for rather than how this repository does it. The session tool's local memory directory is one machine's unversioned files, and a rule kept in both places drifts with nothing to signal it, which is why the local copy of the CI rule was deleted when these notes were written. Keep there only what is true of that machine alone.

`.claude/skills/autopilot/SKILL.md` is the other half of this and does a different job: this file is read at the start of a turn, and the skill's reminders fire into a session that has gone idle. It carries how to pick the next issue and how to place a new one, and points here for the rules a turn already has in front of it.
