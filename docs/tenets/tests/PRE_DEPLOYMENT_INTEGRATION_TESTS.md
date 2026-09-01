# Pre-Deployment Integration Test Tenets

These are the non-negotiable rules for pre-deployment integration tests.

## Table of Contents

- [Integration Tests Verify Components Work Together](#integration-tests-verify-components-work-together)
- [Seven-Layer Testing Model](#seven-layer-testing-model)
- [Test File Organization](#test-file-organization)
- [The Seven Layers](#the-seven-layers)
- [Granular Diagnostics](#granular-diagnostics)
- [Cleanup After Capability Tests](#cleanup-after-capability-tests)
- [Fixture Usage](#fixture-usage)
- [Why Drift Detection Is Not a Separate Step](#why-drift-detection-is-not-a-separate-step)
- [Step Ordering](#step-ordering)
- [Quick Reference](#quick-reference)

## Integration Tests Verify Components Work Together

**Integration tests verify that two or more components integrate correctly.**

There are two kinds of pre-deployment integration test, and they differ in what they read rather than in how they are written.

### Contract Tests

A contract test reads two or more files that must agree with each other and asserts that they do. A value declared in one place and consumed in another, a name one file exports and another references, a setting repeated in two configurations: each of these is a contract, and each can be broken by a change to either side alone.

What makes it an integration test is that it needs both sides. A test that reads one file and asserts something about that file's own structure is a unit test, however far the file is from being code — the second file is what this tier adds.

### Prerequisite Tests

A prerequisite test reads the deployed world and asserts that what this deployment depends on is already there and already right. Something an earlier deployment created, a permission this deployment must hold, a resource it references but does not create: each is a precondition, and each fails the deployment if it is missing.

The boundary is what created the thing. Anything this deployment creates does not exist yet when these tests run, so asserting on it here can only fail or, worse, pass because a previous run left it behind.

Pre-deployment tests answer: "Can I deploy?"
Post-deployment tests answer: "Did the deployment succeed?"

## Seven-Layer Testing Model

Every deployment passes through seven layers, in order.

| Layer | Purpose |
| ------- | --------- |
| 1. Contracts | Local files that must agree with each other do agree |
| 2. Authentication | The identity the deployment runs as is valid |
| 3. Authorization | That identity is permitted to inspect what comes next |
| 4. State | The record of what is deployed matches what is actually deployed |
| 5. Existence | Each prerequisite is present |
| 6. Configuration | Each prerequisite holds its intended values |
| 7. Capability | The operations the deployment performs can actually be performed |

The order is what makes a failure diagnostic, because each layer assumes every layer beneath it holds. A failure at a layer therefore names one cause rather than a set of them:

- Layer 1 fails → two files disagree, and nothing beyond this machine has been consulted yet
- Layer 2 fails → the identity is absent, wrong or expired
- Layer 3 fails → the identity is valid but not permitted to look
- Layer 4 fails → the record and the reality have diverged
- Layer 5 fails → permitted to look, and the thing is not there
- Layer 6 fails → the thing is there and set up wrongly
- Layer 7 fails → the thing is there and set up correctly, and the operation still cannot be performed

Reversing any two of these costs the diagnosis. A failure to read a resource without the layer above it means either an invalid identity, a missing permission or a missing resource, and a single failed assertion cannot say which.

## Test File Organization

**Exactly one test file per layer, named so that the files sort in layer order.**

The name carries the layer number and the layer's subject, so a run reports the layer in the name of the file that failed, and the order the files run in is the order the layers are defined in.

Do not organize by resource. A file per resource asks every question about one thing in one place, which means a failure names the thing and not the layer — and the layer is what says whether the fix is a credential, a permission, a missing prerequisite or a misconfigured one.

## The Seven Layers

### Layer 1: Contracts

Two or more local files are read and asserted to agree. Nothing outside the machine is consulted, so this layer runs before any identity exists and fails fastest of the seven.

Keep single-file assertions out of it. A test that reads one file and checks its own structure belongs to the unit tier; putting it here makes the contract layer look covered when the contracts themselves are not tested.

### Layer 2: Authentication

The identity the deployment will run as is asserted to be valid, and nothing else. The cheapest question that only a valid identity can answer is the right one to ask, and the answer is discarded — this layer establishes that there is someone to ask on behalf of, not that they may do anything.

Asking whether that identity can reach a particular resource mixes the next two layers into this one, and a failure then no longer means what this layer says it means.

### Layer 3: Authorization

The identity is asserted to be permitted to inspect the prerequisites, without asserting that any of them exist. That distinction is the whole of this layer: a refusal is a failure here, and an answer saying the thing is absent is not, because being told it is absent is proof of permission to ask.

This is the one layer whose tests must distinguish between two failure responses from the same call, and the distinction has to be explicit. A test that treats every unsuccessful answer alike collapses this layer into the next one.

### Layer 4: State

The record of what is deployed is asserted to match what is actually deployed. Anything the deployment intends to create is asserted not to exist yet, because something already there under a name the deployment expects to create is drift, and the deployment will fail on it or adopt it silently.

The failure message names each divergence and the command that reconciles it, since the reader of the failed run is being asked to repair the record rather than the code.

Where there is no prior record at all — the first deployment of a thing — this layer has nothing to compare against and is skipped on that condition, explicitly and with the condition stated.

### Layer 5: Existence

Each prerequisite is asserted to be present, and nothing more. Permission to ask is already established by the layer before, so the answer here is read at face value.

Reading a value off the thing while checking that it is there merges this layer with the next, and a failure stops saying which of the two happened.

### Layer 6: Configuration

Each prerequisite is asserted to hold the values this deployment depends on. Existence is already established, so it is not established again — the identifiers found by the previous layer are reused rather than rediscovered.

Only the values this deployment actually depends on belong here. Asserting the rest re-tests someone else's deployment and fails this one for a change that cannot affect it.

### Layer 7: Capability

The operations this deployment performs are asserted to be performable, by performing the smallest instance of each and undoing it. This is the only pre-deployment layer that writes, and it is the last because everything it needs has been established by the six before it.

A capability is not implied by a configuration. A permission can read as granted and still be denied in practice by something above it, and this layer is the only one that finds that out before the deployment does.

## Granular Diagnostics

A failure that says only that something was refused is unacceptable.

- Each test is atomic: one assertion per test
- The layers run in order
- A failure names the exact link in the chain that broke
- A failure message carries the name of the thing and the value that was expected

The reader of a failed run was not there when the test was written. What the message must give them is which layer failed, on what, and what it wanted — everything else they can find themselves.

## Cleanup After Capability Tests

Anything the capability layer creates is removed, in teardown that runs whether the test passed or failed.

Nothing may be left behind. A leftover from a capability test is indistinguishable from a real thing to the layer that checks for drift, so a test that does not clean up after itself fails a later run of the same suite and looks like a defect in the deployment.

## Fixture Usage

Fixtures exist to do three things:

1. Build each client or connection once for the file that uses it, rather than once per test
2. Load configuration — where a test looks, never what it demands — from the place the rest of the system loads it from, rather than restating it
3. Carry forward the identifiers an earlier layer discovered, so a later layer does not rediscover them

The second of those is bounded, and the boundary is what keeps the suite honest. Configuration decides where a test points; an expectation is what it asserts once it arrives. A fixture reads the first from the place the deployment reads it, because a suite aimed at the wrong environment fails for a reason that is not about the deployment. A fixture does not read the second from there. Handing a test the value the deployment intends to produce has handed it the answer, and the test then agrees with that intention whatever it is, a mistaken one included. Expectations are written in the suite, which is the only place they can have been written before the deployment they describe existed — see `TEST_FIRST.md`.

## Why Drift Detection Is Not a Separate Step

The state layer replaces a separate drift-detection step run before the deployment.

It produces the same comparison — what is recorded against what is actually there — and it produces it inside the suite, which buys three things a standalone step does not. A failure names each divergence individually rather than emitting one plan for a reader to scan. A failure carries the command that reconciles each one. And it runs after the identity and permission layers, so a failure to read the world is already ruled out as a cause before the comparison is attempted.

When this layer passes, the deployment will not fail on something that already exists.

## Step Ordering

Pre-deployment integration tests occupy one position, and it is fixed:

```text
1. Static analysis
2. Unit tests
3. Pre-deployment integration tests (layers 1-7)
4. The deployment
5. Post-deployment integration tests
6. E2E tests
```

Each step earns its place by what it depends on and by what it costs.

| Step | Depends On | Reason |
| ------ | ------------ | -------- |
| Static analysis | Nothing | Cheapest, so it goes first |
| Unit tests | Static analysis | No point running code that does not read correctly |
| Pre-deployment integration | The state record being reachable | The state layer must be able to compare |
| The deployment | Pre-deployment passing | Nothing deploys onto unmet preconditions |
| Post-deployment integration | The deployment | Nothing to inspect until it has run |
| E2E | Post-deployment integration | The journey needs every part of it deployed and correct |

The two rules that follow from this are that these tests run before the deployment, not after it, and that a failure here skips the deployment rather than proceeding in the hope that it works.

## Quick Reference

| If you want to test... | Layer |
| ------------------------ | ------- |
| Two files agree about a value one declares and the other consumes | 1. Contracts |
| Two files agree about a name one exports and the other references | 1. Contracts |
| A setting repeated in two configurations is the same in both | 1. Contracts |
| The identity the deployment runs as is valid | 2. Authentication |
| That identity has not expired | 2. Authentication |
| That identity is permitted to inspect a prerequisite | 3. Authorization |
| A refusal to inspect is distinguished from an absence | 3. Authorization |
| The record of what is deployed matches what is deployed | 4. State |
| Nothing the deployment will create is already there | 4. State |
| A prerequisite is present | 5. Existence |
| A prerequisite holds the value this deployment depends on | 6. Configuration |
| An operation the deployment performs can be performed | 7. Capability |
| A permission granted in configuration works in practice | 7. Capability |
