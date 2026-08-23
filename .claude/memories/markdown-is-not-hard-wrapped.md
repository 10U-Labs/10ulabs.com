# Markdown is not hard-wrapped

## Table of Contents

- [The rule](#the-rule)
- [Nothing enforces a width](#nothing-enforces-a-width)
- [What hard wrapping costs](#what-hard-wrapping-costs)
- [The trap in what is already written](#the-trap-in-what-is-already-written)
- [Related notes](#related-notes)

## The rule

There is no column limit on the prose written in this repository. That covers the markdown in `.md` files, the markdown written into GitHub issues, and the body of a commit message. Write a paragraph as one line and let whatever displays it do the wrapping. Do not break a sentence across lines to hit 72, 80 or any other width. The commit subject line is the exception and stays short, because `git log --oneline` and GitHub's commit list both truncate it; the rule is about the paragraphs below it.

## Nothing enforces a width

Nothing enforces a width. `documentation.yml` runs `markdownlint` over every `.md` file in the tree, and the rule that would set a width, MD013, is disabled on the command line that runs it; there is no `markdownlint` configuration file and no `yamllint` configuration file in the repository, and `assert-no-linter-config-files` is a step of that same workflow, so nothing can quietly add one. No check anywhere reads a commit message. A hard-wrapped paragraph and an unwrapped one pass CI identically. The choice is a convention, and the convention is not to wrap.

## What hard wrapping costs

Hard wrapping costs something. An edit to the middle of a wrapped paragraph reflows every line after it, so a one-word change shows up as a rewritten block and the real change hides inside the noise. Unwrapped, a paragraph edit touches one line. This particular cost does not apply to a commit message, which is never edited here — a rejected push is answered with a follow-up commit rather than an amended one, so no commit body is ever rewritten. What applies to the commit body is the second cost: a fixed width is a guess about the reader's window, and every reader who is not at that width gets the guess instead of their own. GitHub renders a commit body into a column of its own choosing and a wrapped paragraph arrives there as a ragged block; `gh issue create --body-file` carries a commit body into an issue where the same paragraph is now markdown and wraps to the browser. The terminal is the case that looks like an argument for wrapping and is not: `git log` pages through `less`, which folds a long line at the terminal width rather than truncating it.

## The trap in what is already written

The trap is the text already written, in both places. Everything wrapped at about seventy columns sat under `products/`, which moved to its own repository, and every markdown file remaining here is unwrapped: `docs/tenets/tests/UNIT_TESTS.md` has a 239-character line and `CLAUDE.md` runs to 1,009. The history is the opposite way round — every commit up to `84c13b33` is wrapped to about seventy-two columns, `84c13b33` itself running 61 to 74 characters a line, because that is git's default and no rule of this repository's said otherwise until this note. So the whole history below that point is an example not to follow, and imitating the commit above yours reproduces the wrapping rather than the convention. Take the width from this note instead.

## Related notes

Related: [tenets-are-generic](tenets-are-generic.md), on the same failure of copying what is already written instead of following the rule that governs it. [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md), on why a commit body is never edited once pushed.
