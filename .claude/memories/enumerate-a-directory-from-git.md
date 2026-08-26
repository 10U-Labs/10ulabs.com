# Enumerate a directory from git

## Table of Contents

- [The rule](#the-rule)
- [The case that forced it](#the-case-that-forced-it)
- [Why git status said nothing](#why-git-status-said-nothing)
- [What it cost](#what-it-cost)
- [The rejected alternative](#the-rejected-alternative)
- [Related notes](#related-notes)

## The rule

When an issue body states what a directory holds — a count of its entries, a list of them, or the name of one — enumerate it with `git ls-files` rather than with `ls` or a file browser. A working copy carries ignored build artifacts that git will not report, so a package deleted from the repository goes on reading as a live one to anything that looks at the disk, for as long as one ignored directory survives beside it. The repository is what the issue is a claim about, and `git ls-files` is what reads the repository.

## The case that forced it

`9086acda` deleted `lib/python/runner_labels/` on 2026-08-22 when it removed the self-hosted runner fleet. Git removed the tracked files and left the directory standing, because the only thing still inside it was a `__pycache__` that line 20 of `.gitignore` covers. So the two commands disagreed:

```console
$ ls lib/python/ | wc -l
13
$ git ls-files lib/python/ | cut -d/ -f3 | sort -u | wc -l
12
```

The thirteenth was `runner_labels`, a directory whose entire content was one compiled file for a package that no longer existed. At `HEAD` the two agree at twelve, because the thirty-one `__pycache__` directories and the `.pytest_cache` were deleted from the working copy when the miscount was found; that agreement is a property of one working copy on one day, not a reason to go back to reading `ls`.

## Why git status said nothing

`git status` reported a clean tree throughout, which is why the discrepancy survived nine issue bodies rather than being caught at the first. A clean report is not a statement that the working copy matches the repository — it is a statement that nothing git is willing to report differs, and an ignored file is precisely what git is not willing to report. `git status --ignored` is the command that shows what the plain form suppresses, and it is what turns "the tree is clean" into a claim that can be checked.

## What it cost

Nine issue bodies took the count from the disk rather than from git. `#609`, `#610`, `#611`, `#614`, `#616` and `#617` each stated a total of thirteen packages under `lib/python/` and named `runner_labels` as one of them; each also carried it in the list of packages its workflow does not execute, so the exclusion counts were wrong by one as well, and `#609` went further and stated that `#608` had erred by omitting it. `#612`, `#613` and `#615` had already been corrected in an earlier session. `#608` enumerated with `git ls-files`, counted twelve, and was right throughout.

Nothing shipped wrong on account of it: `runner_labels` earns no test job under either premise, and the six closed issues all landed green with the correct set of jobs. The cost fell on the reader. `#613` as filed told whoever picked it up that twelve of thirteen packages had a suite under `test/lib/python/` and named the thirteenth as the exception; every tracked package has a suite, so the sentence sent its reader looking for a directory git does not have, and could not be checked against the repository without first discovering why.

## The rejected alternative

The alternative was a check inside the `scripts/publish_issue.py` that `#587` proposes, resolving every backticked repository path in a body against `git ls-files` and failing on any that git does not track. It loses because it would not have caught this one. All nine bodies wrote the package as the bare name `runner_labels` in backticks and none of them ever wrote `lib/python/runner_labels/`, so there was no path token in any of them for such a check to resolve. Widening it to fire on any backticked bare name matching an untracked directory somewhere on disk would reach this case, but only by accident of the name colliding with a directory, and it would still say nothing about the stated total of thirteen, which was the defect itself. A count is not a path, and no check over path tokens sees one.

## Related notes

Checking a filed issue's claims against the repository before working it is in [how-issues-are-written](how-issues-are-written.md), and reading the code locally while leaving every check to CI is in [verification-in-ci-only](verification-in-ci-only.md).
