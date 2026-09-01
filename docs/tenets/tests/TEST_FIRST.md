# Test-First Tenets

These are the non-negotiable rules about when a test is written, and about what a test may read as a consequence. They hold at every tier.

## Table of Contents

- [The Test Is Written Before What It Tests](#the-test-is-written-before-what-it-tests)
- [A Test States Its Expectation](#a-test-states-its-expectation)
- [Configuration Is Not an Expectation](#configuration-is-not-an-expectation)
- [Two Artifacts That Must Agree](#two-artifacts-that-must-agree)
- [Quick Reference](#quick-reference)

## The Test Is Written Before What It Tests

**The test exists before the thing it covers exists.**

Every other rule here is a consequence of that order. A test written first cannot read the thing it tests, because at the moment it is written there is nothing there to read. It has to say what it wants instead, which is what makes it a specification rather than a description.

The order is also what allows a test to be wrong about an implementation, and being able to be wrong is the whole of its value. A test that cannot disagree with the code has nothing to report about the code.

## A Test States Its Expectation

**The value a test asserts on is written in the test. It is not read out of the thing being tested.**

A test that fetches the expected value from its subject and then compares the subject against it asserts that the subject agrees with itself. It passes for every value the subject could hold, the wrong ones included, so its passing carries no information.

This failure hides better than the one it is usually introduced to fix. Such a test has no literals in it, survives every rename, and never goes red. The first two are why it is mistaken for the more rigorous version; the third is the symptom, and it is invisible because a test that always passes looks exactly like a test that is satisfied.

A rename is the change a stated expectation is meant to catch, not a change it should tolerate. A name is a decision. Changing it changes the decision, the test going red is the record that somebody changed it, and editing the test is how the new decision is agreed to rather than absorbed silently. A test that follows the source through a rename has agreed to it on nobody's behalf.

## Configuration Is Not an Expectation

Two different things get called "the value", and only one of them belongs to the subject.

What a test demands of its subject is an expectation and belongs in the test. Where a test goes looking — which environment, which address, which account — is configuration and belongs wherever the system as a whole is configured. Reading configuration from the place the system reads it is correct and is not the failure above: it decides where a test points, never what it demands once it arrives.

The question that separates them is what should happen if the value changes. If the test should still pass, it is configuration. If the test should go red, it is an expectation, and it is written in the test.

## Two Artifacts That Must Agree

A test that reads two artifacts and asserts they agree takes neither as an expectation, and the rule above does not reach it. Neither side is the subject; the agreement between them is. Such a test can be written before either side exists, because what it states is a relationship rather than a value.

This is the one case in which a test may read the thing it covers, and it is admissible precisely because it takes no answer from it.

## Quick Reference

| The value | Where it is written |
| ----------- | --------------------- |
| What a test demands of its subject | In the test |
| Where a test looks for its subject | Where the system is configured |
| A relationship two artifacts must hold | In the test, as the relationship |
| What the subject says about itself | Nowhere; it is not an expectation |
