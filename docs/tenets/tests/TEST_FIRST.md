# Test-First Tenets

These are the non-negotiable rules about when a test is written, and about what a test may read as a consequence. They hold at every tier.

## Table of Contents

- [Start With the Order](#start-with-the-order)
- [What the Order Rules Out](#what-the-order-rules-out)
- [A Worked Example](#a-worked-example)
- [The Objection: Tests Read Things All the Time](#the-objection-tests-read-things-all-the-time)
- [The Question That Settles Any Value](#the-question-that-settles-any-value)
- [The Third Case: Two Artifacts That Must Agree](#the-third-case-two-artifacts-that-must-agree)
- [Why the Derived Version Is the More Dangerous One](#why-the-derived-version-is-the-more-dangerous-one)
- [Quick Reference](#quick-reference)

## Start With the Order

**The test is written before the thing it tests.**

That is the whole premise, and everything else on this page is worked out from it. Nothing below is a separate rule to memorise; each one is what the premise turns into once you follow it far enough.

So begin by taking it literally. You are about to write a test. The thing it covers does not exist yet — no file, no function, no deployed resource. You cannot open it and look, because there is nothing there to open.

## What the Order Rules Out

Since there is nothing to open, the test has to say what it wants.

That is not a limitation of writing tests early. It is the point of writing them early. A test that says what it wants is a specification: a claim about how the thing should behave, made by somebody deciding how it should behave. A test that reports what the thing already does is a description, and a description agrees with whatever it finds.

The difficulty arrives later. By the second week the thing exists. The file is sitting there, it holds the answer, and reading the answer is easier than deciding it. That is the moment the order stops being automatic and becomes something held on purpose: the test would have had to state its expectation if it had been written first, so it states its expectation now as well.

## A Worked Example

Take a component whose definition file gives it a name, and a test that checks the deployed component came out carrying that name.

Written first, before the definition file exists, only one version is available:

```text
name = fetch_deployed_component().name
assert name == "checkout-processor"
```

Written afterwards, with the definition file open beside it, a second version becomes possible, and it looks tidier:

```text
expected = read_name_from(definition_file)
name = fetch_deployed_component().name
assert name == expected
```

Now suppose somebody edits the definition file to read `chekout-processor`, a typo nobody meant to type.

The first test goes red. It was told the name is `checkout-processor`, the deployment no longer matches, and that report is exactly what the test was for.

The second test goes green. It reads `chekout-processor` out of the definition, the deployment was built from that same definition, and so the two agree. They agree on every spelling, correct and incorrect alike, because one of them was copied from the other. What the test asserts is that the definition file equals itself.

The second version is not a weaker check than the first. It is not a check. There is no value the definition file could hold that would make it fail.

## The Objection: Tests Read Things All the Time

This is where the rule looks like it breaks, and the objection is worth stating at full strength before answering it.

A test cannot be written out of nothing at all. The example above still has to know which account to look in, which region, which address to call. Those values come from somewhere, and the sane place to get them is the same place the system itself gets them — otherwise the test is pointing at a different deployment from the one that exists. So tests do read the system's own files, routinely, and that is not merely tolerated but required.

The answer is that two different things are being called "the value", and only one of them is what the test is claiming.

A test makes a sentence. Part of that sentence finds the subject: go to this account, in this region, at this address, and fetch the component. The rest of it is the claim about the subject: and its name is `checkout-processor`.

Reading the finding half from the system's configuration is right. It decides where the test points, and pointing somewhere real is a precondition for the test meaning anything at all.

Reading the claiming half from the subject is the failure in the worked example. It decides what the test demands, and taking that from the subject is what makes the demand empty.

## The Question That Settles Any Value

For any value in front of you, ask: **if this value changed, should the test still pass?**

If the answer is yes, it is configuration. The test is looking somewhere else now, which is fine; it should find the same thing there and stay green. Read it from wherever the system is configured.

If the answer is no — if the change is one somebody ought to be told about — it is an expectation. Write it in the test.

Run the question over both halves of the example. The region changes, because the deployment moved. Should the test still pass? Yes: the component moved with it, and nothing about the component changed. Configuration. The component's name changes. Should the test still pass? No: the name is a decision, and somebody has just changed the decision. Expectation.

The same question disposes of the usual argument against stated values, which is that they are brittle because a rename breaks them. A rename is meant to break them. A name is a decision, the test going red is the record that the decision changed, and editing the test is how the new decision gets agreed to rather than absorbed in silence. A test that follows a rename through has agreed to it on nobody's behalf.

## The Third Case: Two Artifacts That Must Agree

There is one more shape. It reads both files and is sound anyway.

Some claims are not about a value at all. They are about a relationship: every route names a handler that exists, every declared variable is supplied, the two ends of an interface use the same field names. A test of that kind opens both artifacts and checks they line up.

```text
for route in read_routes():
    assert route.handler in read_declared_handlers()
```

Nothing here took an expectation from a subject, because neither artifact is the subject. The relationship is. And the relationship was decided before either file was written, which is the test of whether this shape is genuinely in hand: the assertion above is writable on the first day, when there are no routes and no handlers at all, and it holds for every route anybody adds afterwards.

That is why this case is admissible while the worked example is not. Both of them read the source. Only one of them takes its answer from it.

## Why the Derived Version Is the More Dangerous One

It is worth saying plainly why this failure survives a reading, because it hides better than the thing it usually replaces.

The derived test carries no literals, so it looks like it avoided hardcoding. It survives every rename, so it looks robust. And it never goes red — which is the actual symptom, and which is invisible, because a test that always passes and a test that is satisfied look identical from outside. Nothing tells them apart until the day something is genuinely broken and the suite reports nothing.

A hardcoded value in the wrong place is a visible mistake and gets fixed. A derived expectation is an invisible one and can stand for years.

## Quick Reference

| The value | Where it is written |
| ----------- | --------------------- |
| What a test demands of its subject | In the test |
| Where a test looks for its subject | Where the system is configured |
| A relationship two artifacts must hold | In the test, as the relationship |
| What the subject says about itself | Nowhere; it is not an expectation |

**The one question**: if this value changed, should the test still pass? Yes means configuration. No means expectation.
