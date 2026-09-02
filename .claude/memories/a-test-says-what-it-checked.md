# A test says what it checked

## Table of Contents

- [The rule](#the-rule)
- [Why `assert f(...) is None` is refused twice](#why-assert-f-is-none-is-refused-twice)
- [What the assert job counts](#what-the-assert-job-counts)
- [The three forms that work](#the-three-forms-that-work)
- [The incident](#the-incident)
- [Related notes](#related-notes)

## The rule

Every pytest carries exactly one assertion and that assertion has to be able to fail. A test that calls the code under test and checks nothing has no way to report anything, and a test whose assertion is true whatever the program does is the same thing wearing an `assert`.

## Why `assert f(...) is None` is refused twice

`assert f(...) is None` over a function annotated `-> None` reads as a check and is not one: the function returns `None` on every path, so the comparison holds however the call behaved. Two jobs refuse it, for two different reasons, and the pair is what makes the shape hard to escape by halves.

`mypy` reports `func-returns-value` — "does not return a value (it only ever returns None)" — as soon as the enclosing test body is annotated and therefore read. Deleting the assertion answers `mypy` and leaves the test with none, which `assert-one-assert-per-pytest` then reports as a `:0` finding. So neither the assertion nor its removal is the answer; the test needs an assertion that says something.

## What the assert job counts

`assert-one-assert-per-pytest` counts `assert` statements and `pytest.raises` blocks, and an `and` inside an assert counts as two — see [every-tool-is-installed-at-latest](every-tool-is-installed-at-latest.md) for the release that taught it the last of those. A test whose whole body sits inside `with pytest.raises(...)` and carries no `assert` is correct and green, which is why 195 assert-free tests stood in the tree before any of this. A test with neither is what the job refuses.

## The three forms that work

Where the code under test was handed a mock, assert the call that mock was configured for actually happened, taking the deepest one where a test configures several, because reaching that one means the whole path ran:

```python
instance.test_can_call_iam_get_role_api(mock_client, "MyRole")
assert mock_client.get_role.called
```

Where the meaning is that a checker rejects its input, `pytest.raises` is the assertion and no `assert` is wanted:

```python
with pytest.raises(AssertionError):
    _check_lambda_lifecycle_rules(tf_file)
```

Where the meaning is that a checker accepts its input and there is nothing observable to read, `accepted` in `lib/python/test_fixtures/outcomes.py` turns the outcome into a value: it calls the check and returns whether it came back rather than raising `AssertionError`, `pytest.fail.Exception` or `pytest.skip.Exception`.

```python
assert accepted(_check_lambda_lifecycle_rules, tf_file)
```

That assertion can fail where the `is None` it replaced could not, and it reads as the mirror of the `pytest.raises` sibling beside it.

## The incident

`0845841b` annotated 2,682 test functions, which put their bodies in front of `mypy` for the first time and produced 48 `func-returns-value` errors in the workflows that reached those files. `0bbf1bbc` swept the whole tree for the shape and deleted 100 of them, which turned `mypy-tests` green and `assert-one-assert-per-pytest` red with 110 findings — the 100 plus eleven the earlier commit had already emptied. `865ebc81` gave each of the 111 an assertion: 64 the mock call they had set up, 47 the `accepted` form, and wrote `outcomes.py` to hold it.

The lesson is that the vacuous assertion was hiding 111 tests that checked nothing, and that neither job alone would have found them. `mypy` could not see them until the bodies were annotated, and the assert job could not see them while the vacuous `assert` was there to count.

## Related notes

- [a-test-does-not-restate-the-source](a-test-does-not-restate-the-source.md) — the other way an assertion can pass while saying nothing
- [tdd-workflow](tdd-workflow.md) — the tier files, and one assert per pytest as a standing rule
- [test-code-is-placed-by-how-many-suites-use-it](test-code-is-placed-by-how-many-suites-use-it.md) — why `accepted` sits in `lib/python/` rather than beside one suite
- [every-tool-is-installed-at-latest](every-tool-is-installed-at-latest.md) — how a release taught the assert job to read an `and` as two
