# A test does not restate the source

## Table of Contents

- [The rule](#the-rule)
- [The question that decides it](#the-question-that-decides-it)
- [Why a restatement is not a test](#why-a-restatement-is-not-a-test)
- [Deriving from the source is not quoting it](#deriving-from-the-source-is-not-quoting-it)
- [Where the repository stands](#where-the-repository-stands)

## The rule

The test is written before the code it covers, so it cannot quote that code. What a test asserts is a property the program must have, never a copy of what the program says. A test that names a literal the source also names was written by reading the finished source, and a test derived from the code cannot have driven the code — see [tdd-workflow](tdd-workflow.md) for the authoring order this follows from.

## The question that decides it

Ask whether the test could have been written before the file it reads existed.

If it names a value the source also names — a spelling, a string literal, a line — the answer is no, and it is a restatement rather than an assertion. `assert 'SessionsHandlerRole' in content` over `iam.tf` is the shape: the literal could only have been typed by someone with the finished file open.

If it names a rule the source must satisfy, the answer is yes, and it is a test. `no .tf file outside locals.tf interpolates the resource prefix` is true of files that have not been written yet, which is what makes it writable first.

## Why a restatement is not a test

It holds two copies of one string and passes while they agree, which is not the same as passing while the program is right. Nothing in the pair is the authority, so the assertion cannot distinguish a correct program from a consistently wrong one.

It cannot go red on the defect it was written for. The only edit that breaks it is an edit to one of its own two copies, so what it reports is a rename — and a rename is the one change it should tolerate, since the deployed system is unaffected by how a name is spelled. [Nothing checks that a test is able to fail](https://github.com/10U-Labs/10ulabs.com/issues/577) is the general form of that failure.

`5359c061` deleted four of them from the sessions unit suite and reached the same place by another route: what they check has no consequence, because AWS accepts a dash, an underscore or a leading lower-case letter in an IAM role name, nothing downstream reads either name for its shape, and no deployment, caller or runtime answer changes when one is spelled differently. The only defect such a test can report is that somebody would have spelled a name another way.

## Deriving from the source is not quoting it

The line is between deriving a value from the source and duplicating it, not between touching the source and not touching it.

Reading a value from the place the deployment reads it is deriving. `sessions_config["handler_role_name"]` names a key rather than a name and can be written before any `locals.tf` holds one; `docs/tenets/tests/PRE_DEPLOYMENT_INTEGRATION_TESTS.md` gives this as one of the three things a fixture exists to do, and gives the reason — a test that hardcodes the value it is asserting on asserts that a constant equals itself.

Asserting a property over a set of files is deriving. The set may be empty, may grow, and the assertion still means something.

Reading a deployed response, a plan or an API answer is not reading source at all, and an `assert 'text/html' in content_type` over an HTTP response is not this shape.

Restating is a fixture that types `"TenULabsSessionsHandlerRole"` as a literal, or a unit test that searches a `.tf` file for a name's spelling. Both have a second copy of a string the source owns.

## Where the repository stands

The tree does not comply. 324 asserts of the form `assert <literal> in content` sit in 27 files that also open a `.tf` file, and whole suites do nothing else: `test/www/common/pre_deployment/unit/` and `test/api/operational/health/pre_deployment/unit/` are each eight files of it.

The rule holds every new test from the day it was written. The standing ones are a queue to be worked issue by issue, not a precedent to copy from the file next to you — the same footing as [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md), where nothing enforces the rule and matching the neighbouring file is the wrong instinct.
