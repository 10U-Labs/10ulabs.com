# Nothing carries a comment or a docstring

## Table of Contents

- [The rule](#the-rule)
- [What refuses it](#what-refuses-it)
- [Why prose beside code is the thing being removed](#why-prose-beside-code-is-the-thing-being-removed)
- [Where the reasoning goes instead](#where-the-reasoning-goes-instead)
- [What a comment was about to say](#what-a-comment-was-about-to-say)
- [What is not a comment](#what-is-not-a-comment)
- [Related notes](#related-notes)

## The rule

No file this repository lints carries a comment or a docstring. That covers every `#` in a Python file, every module, class and function docstring, every `#` in a workflow file, every `#`, `//` and `/* */` in an OpenTofu file, and every `//` and `/* */` in JavaScript. A name, a signature and the shape of a function are the whole of what a reader gets. Where that is not enough to say what a thing holds or does, the thing is named or shaped wrong rather than under-explained, and the answer is to rename or reshape it.

## What refuses it

`assert-no-comments`, published to PyPI from `10U-Labs/assert-no-comments`, in a job of that name in each of the twelve workflow files. Each job reads the argument list that workflow's `assert-no-inline-directives` job carries, plus the `lib/terraform/` modules that workflow's own Terraform sources with a relative `source =`; each is in its workflow's `reconciliation` `needs:` list, so a deployment is gated on it the way it is gated on the other checks. A `.md` file is never read, because prose is the content of a markdown file rather than a gloss on a line of code, and `.terraform.lock.hcl` is never read because OpenTofu writes its header and nobody can delete it.

The twenty-two `pylint-source` and `pylint-tests` jobs run with `--disable=missing-module-docstring`, `--disable=missing-class-docstring` and `--disable=missing-function-docstring`, three separate flags rather than one comma-separated one because the yamllint jobs run with the default line-length rule. Without them pylint's `--fail-on=C,R,W` would demand back the docstrings this tool refuses, and the two checks would deadlock on every file.

## Why prose beside code is the thing being removed

Prose beside code is never checked. The compiler does not read it, the tests do not run it, and no linter asks whether it is still true, so it stops being true and nothing says when. The reader who believes it then works from a program that no longer exists, which is worse than having read nothing at all.

A rename is where the cost shows up first: change one identifier and every sentence naming it is now wrong, in files the rename never touched, and the diff gives no way to find them. `#652` found nine stale `api/backend` names in `lib/python/test_fixtures/terraform_tests.py`, four of them in docstrings, left by `b33d579b` in December. `#653` found two more in the api test tree. `#655` found an example path naming `src/api/endpoints/contact`, a directory `aca4d2d1` had renamed. All three were found by a person reading, in one sweep, because no job reported them.

## Where the reasoning goes instead

The reasoning is not lost, it moves. A commit message and an issue are each dated and attached to a change; a comment sits beside a line claiming to describe it forever. So what would have been a comment goes in the commit message that makes the change, or in the issue that asked for it, and a reader who wants to know why a line is the way it is reads `git log` or the issue that closed on it. Commit bodies here are long for this reason.

## What a comment was about to say

A comment is usually about to say one of three things, and each has somewhere better to go.

- **What the code does.** The name says it, or the name is wrong. Rename.
- **Why the code is the way it is.** The commit message and the issue say it, and they are dated.
- **That a value or a shape is required.** A test says it, and a test fails when it stops being true. `src/bootstrap/wan_synthesizer.tf` carried six lines explaining why its trust policy names two subject claims; `test_trust_policy_names_only_the_synthesizer` is what states that now, and it goes red if a third appears.

## What is not a comment

An assignment to `__doc__` is code and is left alone: `lib/python/test_fixtures/terraform_tests.py` builds a generated test method's `__doc__` from the output name it was given, and `test_lambda_factories.py` reads it back. A `#` inside a string literal is not a comment either, so the fixtures that parse tfvars with `'# comment\nkey = value\n'` keep their sample data, and the `#` filter in `_trusted_repository_patterns` in `test/bootstrap/pre_deployment/unit/test_deploy_roles_terraform.py` stays even though there is nothing left for it to strip.

## Related notes

Related: [markdown-is-not-hard-wrapped](markdown-is-not-hard-wrapped.md), on the prose that does belong in this repository and how it is written. [a-conftest-is-emptied-never-deleted](a-conftest-is-emptied-never-deleted.md), on why an emptied file says nothing at all rather than saying it is empty on purpose. [commit-straight-to-main](commit-straight-to-main.md), on the commit message that now carries the reasoning.
