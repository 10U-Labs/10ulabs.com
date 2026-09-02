# An annotation can turn a near-duplicate into a clone

## Table of Contents

- [The rule](#the-rule)
- [What jscpd measures](#what-jscpd-measures)
- [Why a signature is where it bites](#why-a-signature-is-where-it-bites)
- [The incident](#the-incident)
- [Answering it](#answering-it)
- [Related notes](#related-notes)

## The rule

`copy-paste-source` and `copy-paste-tests` run `jscpd --threshold 0`, so any duplication at all fails the job. The threshold is on the percentage of duplicated lines and it is zero, which means one clone is enough. A change that makes two neighbouring functions textually longer in the same way can push a pair that has sat under the detector's floor for months over it, without duplicating anything itself.

## What jscpd measures

`jscpd` compares token sequences, not lines, and its defaults are a floor of 50 tokens and 5 lines. The console report prints line ranges and a token count — `(8 lines, 53 tokens)` — and the token count is the number that decides. Reformatting does not change it: wrapping a signature across lines moves the line count and leaves the tokens where they were.

## Why a signature is where it bites

Two sibling tests that differ only in one assertion already share their whole body. What keeps them apart is the function name, which breaks the token run, so the shared run is whatever follows the name: the parameter list and the body up to the line that differs. An unannotated parameter list is a handful of tokens; `(self, lambda_client: Any, config: Dict[str, str]) -> None:` is about twenty. Annotating a signature therefore lengthens the shared run of every pair of siblings in the file at once, and pairs sitting in the forties cross fifty together.

## The incident

`0845841b` annotated 2,682 functions under `test/` and turned `copy-paste-tests` red; `271cd405` annotated 128 in `lib/python/test_fixtures` and turned `copy-paste-source` red with it. Between them the two jobs reported 31 clone pairs across thirteen files, in test bodies that no commit in this session had otherwise touched.

This is the same shape as `#690` and `72b32527`, with the cause on the other side: there the tool changed and the tree stood still, here the tree changed and the tool stood still. The answer is the same one both of those got.

## Answering it

Fix what it found. `865ebc81` extracted fourteen shared prologues into fourteen helpers, each named for the value it returns rather than for the tests that share it — `_firehose_s3_destination`, `_prod_stage`, `_cloudtrail_event_selector`, `_export_call_kwargs` and the rest — which leaves each test its own setup line and its own assertion.

Two of the thirty-one were not duplication to extract but duplication to delete: `test_missing_host_header_returns_301` and its siblings were building a CloudFront event by hand beside a `make_event` helper in the same file that builds the same one. A clone report is worth reading for that case before reaching for a new helper.

Do not answer it by shortening an annotation to spend fewer tokens. `Dict[str, str]` where the fixture returns `Dict[str, str]` is the annotation the code wants, and writing `dict` to drop five tokens is the pin from [every-tool-is-installed-at-latest](every-tool-is-installed-at-latest.md) in another costume: it keeps the job quiet about duplication that is still there.

## Related notes

- [every-tool-is-installed-at-latest](every-tool-is-installed-at-latest.md) — the other direction of the same surprise, and why the answer is never to loosen the tool
- [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md) — where the two `copy-paste` jobs sit among the passes
- [a-rejected-push-is-fixed-forward](a-rejected-push-is-fixed-forward.md) — reading every check a rejected run names, not the first
