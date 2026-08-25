# How issues are written

## Table of Contents

- [Which sections an issue has](#which-sections-an-issue-has)
- [What counts as the program](#what-counts-as-the-program)
- [Answering the tier sections](#answering-the-tier-sections)
- [The static analysis section](#the-static-analysis-section)
- [The regression section](#the-regression-section)
- [The Proposed Solution](#the-proposed-solution)
- [How to write it](#how-to-write-it)
- [An issue on disk goes stale](#an-issue-on-disk-goes-stale)
- [Related notes](#related-notes)

## Which sections an issue has

An issue about the program has seven sections, in this order, and every issue about the program has all seven even when a section is short.

- **Problem** — what is wrong, stated as a fact about the code with the evidence for it.
- **Why Unit Tests Did Not Catch It?** — the specific assertions that passed, and why they could not have failed.
- **Why Integration Tests Did Not Catch It?** — the same, for the tier that checks two units agreeing.
- **Why E2E Tests Did Not Catch It?** — the same, for the tier that makes a caller's journey against the deployed program and judges it on what the caller receives.
- **Why Static Analysis Jobs Did Not Catch It?** — the same, for the half of CI that reads the source without running it: which job saw the file, and why no rule it carries was broken.
- **Which Unit, Integration, or E2E Regression Tests or Static Analysis Jobs Would Prevent This from Happening Again?** — the coverage owed, each test named by the tier it belongs to and the assertion it makes, and each job by the shape it would refuse.
- **Proposed Solution** — the one change to make.

Every heading is in title case. The five that ask something end in a question mark; Problem and Proposed Solution announce something and do not.

An issue about anything else has two sections, **Problem** and **Proposed Solution**, and owes no tests at all.

## What counts as the program

The program is the code a test tier can run: `src/`, `lib/python/`, `lib/terraform/` and `scripts/`. A defect there got past tiers that exist and could have failed, and naming which assertion let it through is what turns one bug report into a gap in the suite that can be closed.

The configs in `etc/`, the workflow files in `.github/` and the documentation in `docs/` are not the program. No tier runs them. A test written against one of them opens the file, reads a value back and asserts the value it just read, so it cannot fail for a reason worth knowing and it fails for reasons that are not: it goes red every time somebody renames a step or adds a path.

Static analysis is the one thing that reaches both sides, because the YAML linter reads every workflow file and the markdown linter reads every document, so the question does have an answer for a defect in one of them. The section stays with the program anyway. The five middle sections travel as a set and are answered against one defect between them, and an issue carrying one of the five carries all five; splitting the set so that a documentation issue takes one section and leaves four would put a third shape of issue in the queue, and the reader would have to work out which of the three is in front of them before knowing what the issue owes.

Most of the open queue here is of that second kind, which is why the split is by directory and there is nothing to weigh. It is also where the practice on disk and the rule disagree, so match the rule rather than the neighbouring issue. #518 through #522 are all `on: push: paths:` changes to `.github/workflows/` and all carry a regression section they do not owe; #522 asks for two integration tests, one asserting that its workflow's `paths:` list is exactly its two entries and one asserting that no step reads `github.event.before`. The first is the shape this rule exists to stop — a test that reads a literal out of a file and asserts the literal. Under this rule neither entry would have been written.

`test/` falls on both sides, and the split is not the directory. The machinery a tier runs on is program code and gets seven sections: the fixtures, the helpers, the doubles, anything that computes a value the assertions then rest on. It can be wrong in a way that makes a whole tier report the wrong answer, and a unit tier can usually reach it, so asking which assertion should have failed has a real answer. Most of that machinery is inside the program by its location already, under `lib/python/` — `test_fixtures/`, `boto_mocks/`, `event_factories/`, `terraform_config/` — but it does not stop being machinery when it sits in a `conftest.py` under `test/`. The assertions themselves are the other side and get two sections: asking why the unit tests did not catch a defective unit test answers itself.

The line is what the defect is in, not what the fix touches. A change to the program that also edits a config file is a program issue and gets all seven. A change confined to config, workflows or docs is not, however much program behaviour it moves.

## Answering the tier sections

Within a program issue, answer each of the three tier sections honestly, including when the honest answer is that the tier does not exist for that part of the program, or that the tier is the wrong home for the question and something else should have caught it. That answer is the finding, not a reason to leave the section out.

## The static analysis section

Static analysis is the half of CI that reads the source without running it, and it is asked about separately from the tiers because it catches a different kind of defect. A tier executes the program and judges what comes back, so it can only catch what a caller could observe, and it catches it in the one place the test happens to reach. A job reads the text and refuses a shape, so it catches every occurrence of that shape everywhere in the tree at once, and it goes on refusing it in code nobody has written yet. Where the defect is one a rule could have named — an unused definition, a type that cannot be what the caller passes, a duplicated block, a suppression comment — the job is the right answer and a regression test for the single occurrence is the wrong one.

The jobs are the linter and the type checker over source and over tests, the formatters for each language, the duplicate detector and this repository's own assertion jobs, which are the rules written here that no off-the-shelf analyser carries. The deployment job is not one of them, however early it runs: it plans and applies against the cloud provider, which makes it the opposite of static.

Answering this section means saying which job read the file and why nothing it carries was broken. The honest answer is often that every job read the file and none of them has a rule about this, which is what makes the regression section reach for a new one.

## The regression section

The regression section is those four read forwards, and it is where the coverage owed is named. A test entry says which tier the test sits in, what it sets up, and what it asserts, so the test can be written from the issue without rediscovering the defect. A job entry says which job gains the rule and what shape it refuses, and whether that job exists yet. It is a separate section from the solution because a fix and the test that would have caught it are separate pieces of work, and an issue that folds the second into the last paragraph of the first tends to ship without it. Name the tier the subsystem actually has — `lib/python/` and `lib/terraform/` have no `pre_deployment/` split, see [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md).

## The Proposed Solution

The closing section is called "Proposed Solution" and not "Solution". It is what the issue proposes, and whoever picks it up is free to do something else; the name says so before they have read a word of it. It names one change and not a choice between two — see [an-issue-states-one-solution](an-issue-states-one-solution.md).

## How to write it

The rules for prose everywhere here — lead with the concept, one idea to a sentence, cut what changes nothing, no bullets inside an argument — are in [prose-leads-with-the-concept](prose-leads-with-the-concept.md). What follows is how they land on the seven sections.

Problem and the four sections that ask what should have caught it name no file and no function at all, beyond the one thing the issue is about, which Problem may name once so the reader knows what is under discussion. They are arguments about behaviour, and an argument that only holds while looking at the file is one the reader cannot check. Naming the subject is not a licence to bring its neighbours in with it. The regression section names a tier and an assertion, or a job and the shape it refuses, which are concepts too. Identifiers belong in Proposed Solution, where the reader has stopped reading and started working, and where naming the one change is the whole job.

Assume the reader has not opened the files and will not open them while reading. That makes the issue self-contained; it does not make each section repeat the last. Problem sets the frame — what the code is for, what is wrong with it, what the defect costs — in its first few lines. The six sections after it inherit that frame and do not restate it.

A section is as long as it needs to be and no longer. A section may be a single sentence, and the four backward-looking sections often are, because the honest answer to them is short. Padding a short answer to fill out a header is the failure to watch for.

## An issue on disk goes stale

An issue is written against the tree as it stood, and the tree moves. Check its claims against the repository before working it or editing it: what it says exists, what it says nothing imports, what it counts, and whether the files its solution names are still the files the change would touch.

Reading #585 this way turned up two false statements and a missing step. It said three of the four Lambda functions wanting a cached client had written their own, which implied a fourth used the shared package, when five functions are deployed, three use clients and all three wrote their own. Its closing paragraph then told the reader to leave four alone. Its solution also missed a documentation file that all three commits it cites as precedent had updated when they deleted a package. None of that was visible from the issue by itself and all of it took one pass over the tree.

Correcting what is wrong is part of picking the issue up rather than a separate errand. Adding a missing step to a `Proposed Solution` is not the same as choosing between two the issue left open, which stays barred — see [an-issue-states-one-solution](an-issue-states-one-solution.md).

## Related notes

Issue bodies are not hard-wrapped, like all markdown here — see [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md). The tier vocabulary and what each tier is for come from `docs/tenets/tests/` — see [read-test-tenets-first](read-test-tenets-first.md). Where a filed issue goes in the queue, and when it carries a `blocked_by` edge at all, is in [an-edge-is-only-a-true-block](an-edge-is-only-a-true-block.md) and in `.claude/skills/autopilot/SKILL.md`.
