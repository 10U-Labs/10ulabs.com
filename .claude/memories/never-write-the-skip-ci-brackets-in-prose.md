# Never write the skip ci brackets in prose

## Table of Contents

- [The rule](#the-rule)
- [Only removing the brackets breaks the match](#only-removing-the-brackets-breaks-the-match)
- [The incident](#the-incident)
- [Why the string turns up at all](#why-the-string-turns-up-at-all)
- [The failure is silent in both directions](#the-failure-is-silent-in-both-directions)

## The rule

A commit message here is prose that explains a change, and it is also input to GitHub Actions. GitHub scans the whole raw message — subject line and body alike — for the bracketed `[skip ci]` directive, and a push whose message contains it anywhere starts no workflow at all. So a message that merely names the directive, reporting what some earlier commit did with it, suppresses every run its own diff was due to start. Write the bracketed form only when this push is meant to start nothing; when describing another commit's use of it, write `skip ci` without the brackets.

## Only removing the brackets breaks the match

Removing the brackets is the only thing that breaks the match. Quoting the string, indenting it, wrapping it in backticks or putting it inside a longer sentence all leave the literal characters in the message, and the scan reads characters rather than markup. There is no way to spell the bracketed form in a commit message and still have the push run.

## The incident

`0463bad9` is the incident. Its body opens by reporting what `52a07c47` did — that it gave "Run pylint on tests" `--recursive=y` and was pushed with the directive — and in doing so wrote the brackets. Its diff edits nine workflow files, `.github/workflows/api_common_routing.yml`, `.github/workflows/bootstrap.yml` and `.github/workflows/www_home.yml` among them, and each of those files is named by its own workflow's `paths` list, so nine runs were due. None started. The only runs recorded against that SHA are two `workflow_dispatch` runs somebody made by hand ten minutes later, `scripts` 32602377864 and `documentation` 32602349681, and the `scripts` one failed. The commit answered 486 `pylint` findings and closed #572 with no deploying workflow having read it, and seven of those nine workflows went on displaying the run from before it.

## Why the string turns up at all

The string appears in messages here because the directive is in live use, not because it is a curiosity: 708 of the 3,618 commit subjects in this history end with it, `52a07c47` and `38674a6c` among them, counted with `git log --format='%s' | grep -c 'skip ci'`. Nothing distinguishes using it from naming it, which is what makes the mistake easy.

## The failure is silent in both directions

The failure is silent in both directions. The push reports success, `git log` shows the commit on `main`, and nothing anywhere says a run was skipped; the absence surfaces only later, as a workflow whose most recent run predates the change. Work goes straight to `main` here and CI is the only review there is — see [commit-straight-to-main](commit-straight-to-main.md) and [verification-in-ci-only](verification-in-ci-only.md) — so a push that starts nothing lands a change nothing has read.
