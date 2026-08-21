# How issues are written

An issue about the program has six sections, in this order, and every issue about the program has all six even when a section is short.

- **Problem** — what is wrong, stated as a fact about the code with the evidence for it.
- **Why Unit Tests Did Not Catch It** — the specific assertions that passed, and why they could not have failed.
- **Why Integration Tests Did Not Catch It** — the same, for the tier that checks two units agreeing.
- **Why E2E Tests Did Not Catch It** — the same, for the tier that makes a caller's journey against the deployed program and judges it on what the caller receives.
- **Which Unit, Integration, or E2E regression tests would prevent this from happening again?** — the tests to write, each named by the tier it belongs to and the assertion it makes.
- **Proposed Solution** — the one change to make.

An issue about anything else has two sections, **Problem** and **Proposed Solution**, and owes no tests at all.

The program is the code a test tier can run: `src/`, `lib/python/`, `lib/terraform/` and `scripts/`. A defect there got past tiers that exist and could have failed, and naming which assertion let it through is what turns one bug report into a gap in the suite that can be closed.

The configs in `etc/`, the workflow files in `.github/`, the documentation in `docs/` and the hardware work in `products/` are not the program. No tier runs them. A test written against one of them opens the file, reads a value back and asserts the value it just read, so it cannot fail for a reason worth knowing and it fails for reasons that are not: it goes red every time somebody renames a step or adds a path.

Most of the open queue here is of that second kind, which is why the split is by directory and there is nothing to weigh. It is also where the practice on disk and the rule disagree, so match the rule rather than the neighbouring issue. #518 through #522 are all `on: push: paths:` changes to `.github/workflows/` and all carry a regression section they do not owe; #522 asks for two integration tests, one asserting that its workflow's `paths:` list is exactly its two entries and one asserting that no step reads `github.event.before`. The first is the shape this rule exists to stop — a test that reads a literal out of a file and asserts the literal. Under this rule neither entry would have been written.

`test/` falls on both sides, and the split is not the directory. The machinery a tier runs on is program code and gets six sections: the fixtures, the helpers, the doubles, anything that computes a value the assertions then rest on. It can be wrong in a way that makes a whole tier report the wrong answer, and a unit tier can usually reach it, so asking which assertion should have failed has a real answer. Most of that machinery is inside the program by its location already, under `lib/python/` — `test_fixtures/`, `boto_mocks/`, `event_factories/`, `terraform_config/` — but it does not stop being machinery when it sits in a `conftest.py` under `test/`. The assertions themselves are the other side and get two sections: asking why the unit tests did not catch a defective unit test answers itself.

The line is what the defect is in, not what the fix touches. A change to the program that also edits a config file is a program issue and gets all six. A change confined to config, workflows or docs is not, however much program behaviour it moves.

Within a program issue, answer each of the three backward-looking sections honestly, including when the honest answer is that the tier does not exist for that part of the program, or that the tier is the wrong home for the question and something else should have caught it. That answer is the finding, not a reason to leave the section out.

The regression section is those three read forwards, and it is where the coverage owed is named. Each entry says which tier the test sits in, what it sets up, and what it asserts, so the test can be written from the issue without rediscovering the defect. It is a separate section from the solution because a fix and the test that would have caught it are separate pieces of work, and an issue that folds the second into the last paragraph of the first tends to ship without it. Name the tier the subsystem actually has — `lib/python/` and `lib/terraform/` have no `pre_deployment/` split, see [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md).

The closing section is called "Proposed Solution" and not "Solution". It is what the issue proposes, and whoever picks it up is free to do something else; the name says so before they have read a word of it. It names one change and not a choice between two — see [an-issue-states-one-solution](an-issue-states-one-solution.md).

Write prose in simple, plain, ordinary English. Short sentences, no hedging, no jargon from computer science where a plain word will do. Assume the reader has not opened the files and will not open them while reading: each section opens with a plain sentence saying what the thing is and what it is for, and the identifiers follow it. Problem says what the code is there to do before it says what is wrong with it, and says what the defect costs in ordinary words within the first few lines rather than in the seventh paragraph. A detail that changes nothing the reader would do is cut, table or not. That rule is stated in full in the `:05` reminder of `.claude/skills/autopilot/SKILL.md`, which is the only place it is written down here.

Tables are allowed where a table genuinely reads better than a paragraph: a name-to-name rename mapping, or two measured columns being compared. Bullets are allowed only when enumerating a list of things. Do not use bullets to break up an argument — an argument is prose.

Back a claim with a number computed from the repository's own data wherever a number is available, and say how it was computed so a reader can redo it. Prefer bounds that survive new data over exact figures that go stale.

Issue bodies are not hard-wrapped, like all markdown here — see [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md). The tier vocabulary and what each tier is for come from `docs/tenets/tests/` — see [read-test-tenets-first](read-test-tenets-first.md). Where a filed issue goes in the queue, and the `blocked_by` edge it must carry, is in `.claude/skills/autopilot/SKILL.md`.
