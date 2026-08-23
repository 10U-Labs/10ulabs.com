# Unit Test Tenets

These are the non-negotiable rules for unit tests.

## Table of Contents

- [Unit Tests Are the Primary Line of Defense](#unit-tests-are-the-primary-line-of-defense)
- [Extreme Atomicity](#extreme-atomicity)
- [Test File Organization](#test-file-organization)
- [Complete Isolation](#complete-isolation)
- [Test Every Code Path](#test-every-code-path)
- [Descriptive Test Names](#descriptive-test-names)
- [Test Error Messages](#test-error-messages)
- [No Test Interdependence](#no-test-interdependence)
- [Fast Execution](#fast-execution)
- [Pre-Deployment Coverage Requirements](#pre-deployment-coverage-requirements)
- [Quick Reference](#quick-reference)

## Unit Tests Are the Primary Line of Defense

**Almost everything wrong should be caught by unit tests.**

The testing pyramid dictates that unit tests form the base: the number of unit tests should be absurdly larger than the integration and end-to-end tests combined. If a defect could have been caught by a unit test and was not, that is a gap in unit coverage, and it is answered by writing the unit test rather than by catching it again higher up.

```text
        /\
       /  \     E2E tests (few)
      /----\
     /      \   Integration tests (some)
    /--------\
   /          \
  /            \ Unit tests (many)
 /______________\
```

A unit test exercises a single unit — one function, one class, one module — with everything it depends on replaced. An integration test exercises two or more units against each other. An end-to-end test exercises the journey a user takes.

**Rule of thumb**: if every dependency is replaced and one unit is left running, it is a unit test. If two or more units are running against each other, it is an integration test, whether or not anything leaves the machine.

## Extreme Atomicity

**One logical assertion per test. No exceptions.**

Each test verifies exactly one behavior. A test that asserts three things reports the first one that fails and says nothing about the other two, so a single run answers one third of the question it appears to answer. Splitting them costs nothing and makes every failure name itself.

Atomicity is also what lets tests run in any order and what keeps a test name honest: a name can describe one behavior accurately, and cannot describe three.

Two shapes break this rule and are worth naming, because both look reasonable while being written. The first asserts several properties of one result, so a failure early in the list hides whether the rest hold. The second asserts the success path and the failure path in the same test, which are two behaviors by definition and belong in two tests.

## Test File Organization

**One test file per source file, in a one-to-one mapping.**

Each source file has exactly one test file, and that test file covers that source file and nothing else. The test tree mirrors the source tree, so the file holding the tests for a unit is found by knowing where the unit is, and a source file with no test file is visible as a gap rather than hidden inside a file named after something else.

Do not organize tests by behavior — a file for the happy paths and a file for the error cases — and do not put the tests for two source files in one file. Both destroy the mapping: the first spreads one unit across several files, the second buries several units in one, and in either case nothing shows which unit is untested.

## Complete Isolation

**Unit tests must have zero external dependencies.**

Nothing a unit test does may leave the process: no network calls, no calls to a remote service, no database connections, no reads or writes of the file system beyond the fixtures the test itself carries, and no change to process-wide state that outlives the test.

Everything external is replaced, and the test asserts on what the unit asked the replacement to do. That is the assertion this tier can make and the tier above it cannot make cheaply: not that the request succeeded, but that the request the unit constructed was the right one.

A test that reaches a real external dependency is an integration test that has been filed as a unit test. It is slower, it fails when something unrelated is down, and it stops answering the question the unit test was written to answer.

## Test Every Code Path

**Full branch coverage is the goal.**

Every branch, every loop that may not run, every error path and every early return has a test. A conditional with two arms and one test leaves half the unit unexercised, and the untested half is usually the error path — the one that runs least often in normal operation and is therefore least likely to be noticed when it breaks.

Testing only the path the code takes when everything goes right is the common failure here, and it is easy to spot: count the branches in the unit, count the tests, and the difference is what is not covered.

## Descriptive Test Names

**A test name states the unit, the condition and the expected result.**

The name is what a failed run shows first, and it should be enough on its own to say what broke. A reader who sees the name and nothing else should know which unit was called, under what condition, and what it was supposed to do.

Names that say a unit "works", names that number themselves, and names that give only a category leave the reader to open the test to find out what failed. That is a cost paid on every failure for a saving paid once when the test was written.

## Test Error Messages

**When a test fails, the failure must explain the problem.**

An assertion that compares two values reports both, and that is usually enough. An assertion that reduces its subject to true or false reports neither, and a failure then says only that something was not what was expected — which the reader already knew from the fact that the run failed.

Assert on the value, not on whether the value is merely present or merely truthy. Where the check is genuinely a predicate, carry a message that names the subject and the expectation, so the run says what was being asked as well as that the answer was wrong.

## No Test Interdependence

**Each test must be completely independent.**

Every test passes when run alone, passes in any order, and shares no mutable state with any other test. State that a test needs is built fresh for that test, in setup that runs before each one rather than once for the file.

A suite whose tests share a mutable object is a suite where the order of the file is part of the contract, and nothing declares it. Such a suite passes until a test is reordered, skipped, or run on its own to reproduce a failure — which is exactly the moment a reader most needs it to be trustworthy.

## Fast Execution

**Unit tests must be fast: milliseconds, not seconds.**

A unit test that takes appreciable time is doing something a unit test should not: reaching something external, building expensive state each time, or covering more than one unit. The slowness is not the defect; it is the symptom that names the defect.

Speed is what makes this tier the primary line of defense. A suite that runs in seconds is run on every change; a suite that takes minutes is run when someone remembers, and it stops catching things shortly after that.

## Pre-Deployment Coverage Requirements

Unit tests must catch these before anything deploys.

| Issue Type | Must Be Caught By |
| ------------ | ------------------- |
| Code that cannot be loaded at all | Unit test |
| A value of the wrong shape passed between units | Unit test |
| An absent value handled as if it were present | Unit test |
| An edge case at the boundary of the input | Unit test |
| A logic error in the rule the unit implements | Unit test |
| An error path that does not do what it claims | Unit test |
| Input accepted that should have been rejected | Unit test |
| A single file parsed or interpreted wrongly | Unit test |
| Two files that disagree about a shared contract | Pre-deployment integration |
| A deployed resource configured with the wrong value | Post-deployment integration |
| A permission the deployment needs and does not hold | Pre-deployment integration |
| A path between two deployed components that does not carry traffic | E2E |
| The journey a user takes, end to end | E2E |

If a defect could have been caught by a unit test, the unit suite failed, whichever tier reported it.

## Quick Reference

| If you want to test... | Test Type | Why |
| ------------------------ | ----------- | ----- |
| A value returned for a given input | Unit | One unit, nothing external |
| An error raised for bad input | Unit | One unit, nothing external |
| The behavior of a method on a class | Unit | One unit, nothing external |
| What a unit asked a replaced dependency to do | Unit | Observable without the dependency |
| How structured data is read and written | Unit | Pure transformation |
| How a value is formatted | Unit | Pure transformation |
| That a prerequisite of the deployment is present | Pre-deployment integration | Exists before the deployment runs |
| That the deployment is permitted to do what it must | Pre-deployment integration | Answers whether it can deploy |
| That a deployed resource holds its intended value | Post-deployment integration | Exists only after deployment |
| That a request reaches the component meant to serve it | E2E | The full path, from where a user enters |
| That the effect the user came for actually happens | E2E | The full path, from where a user enters |
