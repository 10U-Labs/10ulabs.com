# E2E Test Tenets

These are the non-negotiable rules for end-to-end tests.

## Table of Contents

- [Top of the Pyramid](#top-of-the-pyramid)
- [Production-Safe](#production-safe)
- [Test the Full Path](#test-the-full-path)
- [Last Line of Defense, Not First](#last-line-of-defense-not-first)
- [Run During CI/CD](#run-during-cicd)
- [Fail Fast](#fail-fast)
- [Test File Organization](#test-file-organization)
- [Fixture Requirements](#fixture-requirements)
- [Reported Configuration vs Real-World Verification](#reported-configuration-vs-real-world-verification)
- [Boundary with Post-Deployment Integration](#boundary-with-post-deployment-integration)
- [Quick Reference](#quick-reference)

## Top of the Pyramid

**E2E tests are few in number. Only test critical user journeys.**

```text
        /\
       /  \     E2E tests (few) ← YOU ARE HERE
      /----\
     /      \   Integration tests (some)
    /--------\
   /          \
  /            \ Unit tests (many)
 /______________\
```

E2E tests are expensive:

- Slow (seconds to minutes, not milliseconds)
- Flaky (network, timing, external dependencies)
- Run in production (real resources, real costs)

Each test should represent a critical user journey that, if broken, would constitute a major incident.

That standard admits far less than it first appears. A journey qualifies when its failure is an outage: the primary path a user takes through the system, and the security check that path depends on. An edge case does not qualify however plausible it is — an empty field, a malformed request, a value out of range. Those have an answer at a cheaper tier, and asking them here buys the same answer for more time, more flakiness and more production traffic.

## Production-Safe

**E2E tests run in production. They must be non-destructive or use test flags.**

There is no staging environment. E2E tests execute against production resources. Every e2e test must follow one of these patterns:

### Pattern A: Read-Only Verification

The test only inspects state and creates nothing. It asks the system a question it already answers for every other caller, and reads the answer. This is the pattern to reach for first, because a test that creates nothing has nothing to leak and nothing to clean up.

### Pattern B: Test Flag with Minimal Side Effects

The test sets a flag that makes the system take the whole path but stop short of the expensive part, and asserts on the response that says it did. This buys the coverage of the full path at the cost of a signal the production code must carry, so the flag is part of the system's contract and is tested like the rest of it.

### Pattern C: Self-Cleanup Resources

The test creates the smallest thing it can, and that thing ends on its own within a bounded time rather than waiting to be torn down. A test that creates something persistent is not this pattern, whatever it intends to do afterwards: the cost runs from the moment of creation, and a test that fails before its last line never reaches the teardown it was relying on.

### Cleanup Must Succeed

**If cleanup fails, the test fails.** No silent exception handling.

Leaked test resources cost money, clutter the environment they were created in, and cause confusing failures later. If a test creates something, it must clean it up successfully.

Cleanup that swallows its own errors is worse than no cleanup at all, because it reports success while the leak accumulates. Let the teardown raise. A test that cannot remove what it created has found a real defect — either in the system or in its own assumptions about what it created — and the run should say so.

## Test the Full Path

**E2E tests verify end-to-end behavior that unit and integration tests cannot catch.**

An E2E test enters the system where a user enters it, and asserts on the effect the user came for. Everything between the two is exercised rather than named: each hand-off, each queue, each permission the path depends on. A test that reaches past the front door and starts partway along the path is an integration test wearing the wrong label — it skips the very hand-offs that are the reason this tier exists, and skips them silently.

The intermediate steps may be observed, and often must be, since the final effect can lag the request. Observing a step is not the same as starting from it.

## Last Line of Defense, Not First

**If an e2e test catches a bug that a unit test should have caught, that's a unit test gap.**

E2E tests should only catch issues that cannot be caught earlier:

- Race conditions in distributed systems
- Network/timing issues between components
- Production configuration drift
- Integration issues between independently-deployed services

| Issue Type | Should Be Caught By |
| ------------ | --------------------- |
| A logic error in a pure function | Unit test |
| A missing guard on an absent value | Unit test |
| A deployed resource configured with the wrong value | Post-deployment integration |
| A deployed resource that was never created | Post-deployment integration |
| A request that never reaches the component meant to serve it | E2E test |
| Work accepted at the front door and lost before it takes effect | E2E test |
| A failure-handling mechanism that engages when it should not | E2E test |

The line between the last two groups is what the failure needs in order to appear. A missing resource is visible in what the platform reports about it, so the tier that reads that report catches it. Work lost between two components is visible only in the gap between what went in and what came out, which is what this tier and no other measures.

## Run During CI/CD

**E2E tests run when the deployment runs, not on a schedule.**

E2E tests execute:

- As part of the deployment that changed the component
- After the post-deployment integration tier has passed
- Only for the component being deployed

A clock is not a trigger. A deployment is what makes the previous answer stale, so a deployment is what asks the question again; a run on a timer either repeats an answer nothing has changed or reports a failure long after the change that caused it.

## Fail Fast

**E2E tests should fail quickly when something is wrong.**

Don't wait for long timeouts. If the system is working, responses are fast.

Every wait a test performs is a claim about how long the healthy system takes, so set each one just above that and let a breach fail the test. A generous timeout does not make a test more reliable; it makes a slow system indistinguishable from a working one, and it makes the run that reports the failure arrive minutes after it could have.

Retrying compounds the same error. A loop that tries again until something succeeds converts a hard failure into a long one, and converts a system that is degraded into a system that looks fine. Where the effect being asserted on genuinely arrives after the request, wait for that effect with a bound, and fail when the bound is passed.

## Test File Organization

E2E tests are grouped by journey type, not by component. A journey crosses several components by definition, so grouping by component forces every test to be filed under one of the several it touches, and the choice is arbitrary the moment it is made.

The grouping that works divides the happy paths from the security paths, because those are the two questions asked of a released system and they fail for different reasons. Shared setup lives beside the tests that use it, at the narrowest scope that covers them all.

## Fixture Requirements

E2E fixtures must:

1. Build requests the way a real caller builds them, including whatever proves the caller is who it claims to be
2. Use test flags to minimize production impact
3. Provide cleanup utilities for any resources created

The first of those is the one that is quietly abandoned. A fixture that skips the part of a request that authenticates it, or that reaches around the front door to inject a request already accepted, has removed the check this tier exists to exercise — and the test still passes, which is the whole problem. If a real caller must prove something to be served, so must the fixture.

## Reported Configuration vs Real-World Verification

**Integration tests verify what the platform reports. E2E tests verify what the real world experiences.**

This is a critical distinction. That a platform reports a resource as configured correctly does not mean the outside world can actually use it. E2E tests must verify the real-world experience.

### Why This Matters

What a platform reports confirms configuration state. It does NOT confirm:

- A change has been published as far as the callers who depend on it
- Authority over the thing has been delegated to the place now serving it
- Network paths are functioning
- Caching layers are behaving correctly
- External services can reach your resources

### Examples

| What You Want to Verify | Integration Test (Reported State) | E2E Test (Real World) |
| ------------------------ | --------------------------------- | ---------------------- |
| A published record is correct | The platform lists the record with the expected value | An independent query from outside returns that value |
| A service is reachable | The components exist and are attached to one another | A request from outside receives a response |
| A granted permission works | The permission reads as intended where it is defined | An actor holding it performs the action |
| Stored content is available | The store holds the content with the expected access rules | A request for the content returns it |
| A credential is valid | The issuer reports it as issued and unexpired | A caller completes the exchange that relies on it |

### The Test

Ask yourself: "If the platform says it's configured correctly, could it still fail for a real user?"

- **Yes** → E2E test (verify real-world behavior)
- **No** → Integration test (verify reported configuration)

### Both Tiers Are Necessary

Neither test replaces the other, and the second is not a stricter version of the first. The integration test catches a deployment that did not do what it was asked. The E2E test catches everything that stands between a correct deployment and a caller who can use it — publication that has not finished, delegation that points elsewhere, a path that does not carry traffic, a cache still serving what was true yesterday. Those failures leave the reported configuration untouched, which is exactly why the tier that reads the report cannot see them.

## Boundary with Post-Deployment Integration

Post-deployment integration tests answer: "Did my deployment succeed?"
E2E tests answer: "Does the user journey work?"

| Post-Deployment Integration | E2E |
| ---------------------------- | ----- |
| A component exists | That component answers a caller |
| A holding place for work exists | Work put into it comes out the other side |
| Two components are connected | The connection actually carries a hand-off |
| A permission is attached | That permission grants the action in practice |
| Configuration is correct | System behaves correctly |

## Quick Reference

| If you want to test... | Test Type | Why |
| ------------------------ | ----------- | ----- |
| How an input is interpreted | Unit | Pure function, no I/O |
| Error message format | Unit | Pure function, no I/O |
| A deployed setting holds its intended value | Post-deployment integration | Resource configuration |
| Two deployed components are connected | Post-deployment integration | Component wiring |
| A request reaches the component meant to serve it | E2E | Full path verification |
| An unauthorized caller is turned away | E2E | Security-critical path |
| The effect the user came for actually happens | E2E | End-to-end user journey |
