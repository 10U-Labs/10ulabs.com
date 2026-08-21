# Committing straight to main

Work goes to `main` as direct commits. Do not create a feature branch, do not open a pull request, and do not structure advice around a review cycle. This overrides the default habit of branching before pushing to the default branch.

The history says it plainly. Every commit from `33031228` upward is direct; the merge commits below it — the newest is `1a34ef78` from 2025-11-19 — are an older pull-request habit that stopped. A side branch now only adds a merge step to a single-maintainer repository.

CI on `main` is the verification gate — see [verification-in-ci-only](verification-in-ci-only.md) — and with no pull-request buffer it is the only review there is, which is why the tests land in the same commit as the code they cover rather than in a follow-up.

One issue is solved by one commit and one push, and the commit closes its issue in the message: `Closes #490` in `31f0066f`, or the qualified `Fixes <owner>/<repo>#<n>` that `1e45d1f9` carries when the issue lives in another repository. That line is what drains the queue. An issue solved by a push that does not carry it stays open and is picked up again on the next traversal, and the work is done twice.

Use commits as the unit when breaking work down, and think in commit ordering rather than branch-and-merge. An issue that cannot be done in one commit is two issues; file the second — see [how-issues-are-written](how-issues-are-written.md) — rather than spreading one issue over pushes.
