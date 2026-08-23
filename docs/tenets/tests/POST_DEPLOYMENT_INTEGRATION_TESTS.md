# Post-Deployment Integration Test Tenets

These are the non-negotiable rules for post-deployment integration tests.

## Table of Contents

- [Only Test This Deployment's Resources](#only-test-this-deployments-resources)
- [Three-Layer Testing Model](#three-layer-testing-model)
- [Test File Organization](#test-file-organization)
- [The Three Layers](#the-three-layers)
- [Fail Fast with Granular Diagnostics](#fail-fast-with-granular-diagnostics)
- [Boundary with E2E Tests](#boundary-with-e2e-tests)
- [No Cleanup Required](#no-cleanup-required)
- [Fixture Usage](#fixture-usage)
- [Quick Reference](#quick-reference)

## Only Test This Deployment's Resources

**Post-deployment tests only test what this deployment created.**

The subject of this tier is the deployment that just ran: the things it brought into being, the values it set on them, and the connections it made between them. Everything else is out of scope, and each exclusion has its own reason.

The journey a user takes is out of scope because it crosses this deployment and others, and a failure in it does not say which deployment caused it. What another deployment created is out of scope because this run cannot fix it and should not fail for it. The rules the code implements are out of scope because they were settled by the unit tier long before anything was deployed.

Post-deployment tests answer: "Did my deployment succeed?"
E2E tests answer: "Does the user journey work?"

## Three-Layer Testing Model

Everything the deployment created is tested through three layers, in order.

| Layer | Purpose |
| ------- | --------- |
| 1. Existence | The thing was created |
| 2. Configuration | It holds the values the deployment set |
| 3. Wiring | It is connected to what it was meant to be connected to |

Each layer assumes the one beneath it holds, which is what lets a failure name one cause:

- Layer 1 fails → the deployment did not create it
- Layer 2 fails → it was created and set up wrongly
- Layer 3 fails → it was created and set up correctly, and stands alone

Wiring last is not a matter of taste. A connection between two things cannot be asserted before both are known to exist, and a connection asserted first fails identically whether one end is missing, both are, or the link between them is.

## Test File Organization

**Exactly one test file per layer, named so that the files sort in layer order.**

The name carries the layer number and the layer's subject, so a run reports the layer in the name of the file that failed, and the order the files run in is the order the layers are defined in.

Do not organize by resource. A file per resource asks all three questions about one thing in one place, so a failure names the thing rather than the layer — and the layer is what says whether the deployment failed to create something, set it up wrongly, or left it unconnected.

## The Three Layers

### Layer 1: Existence

Each thing the deployment created is asserted to be present, and nothing about it is read beyond enough to identify it. This is the cheapest of the three and the one that fails when the deployment did not do its work at all.

Reading a value off the thing while establishing that it is there merges this layer into the next, and the failure stops distinguishing "never created" from "created wrongly" — which are different defects with different fixes.

### Layer 2: Configuration

Each thing is asserted to hold the values the deployment set on it. Existence is settled by the layer before, so it is not re-established here: identifiers found earlier are carried forward rather than looked up again.

What belongs here is every value the deployment declares and something else depends on. A setting the deployment specifies and nothing reads is not worth a test; a setting something depends on and the deployment does not specify is a defect in the deployment, not in the test.

### Layer 3: Wiring

Each connection the deployment made is asserted to be in place: one component attached to another, one thing configured to trigger another, one identity permitted to act on another's behalf. Existence and configuration are both settled, so a failure here is a failure of the link and nothing else.

Wiring is asserted by reading what the platform reports about the connection, not by exercising it. Sending something through the connection to see whether it arrives is the tier above, and the difference matters: this layer says the link was declared, and only the tier above says traffic crosses it.

## Fail Fast with Granular Diagnostics

A failure that says only that something did not work is unacceptable.

- Each test is atomic: one assertion per test
- The layers run in order, and a layer that fails stops the ones above it
- A failure names exactly what is wrong, not merely that something is
- A failure message carries the name of the thing and the value that was expected

## Boundary with E2E Tests

This tier verifies the deployment. The tier above verifies the journey. The line between them is whether anything is put through the system.

Reading what the platform reports about a deployed thing belongs here: that it is there, that it holds a value, that it is attached to something, that it carries the contents it was built with. Putting a request, a message or a call into the system and asserting on what comes out belongs to the tier above — and so does everything that only appears once something is flowing, such as work accepted and lost on the way, a route that sends a request to the wrong place, or a failure-handling mechanism that engages when it should not.

**Rule of thumb**: if the test causes the deployed system to do work, it is an E2E test.

## No Cleanup Required

Post-deployment tests must not create anything. They only read what the deployment produced, so there is nothing to clean up and no state left behind for the next run to trip over.

Reading a thing's configuration, confirming it is present, and reading what it is connected to are all this tier does. Writing data, sending a message, and invoking something with a payload are all outside it — and each one is also the thing that would create a cleanup obligation. A test here that needs cleanup has become an E2E test and belongs in that tier, under that tier's rules.

## Fixture Usage

Fixtures exist to do three things:

1. Build each client or connection once for the file that uses it, rather than once per test
2. Carry forward the identifiers discovered by an earlier layer, so a later layer does not rediscover them
3. Fetch anything expensive once — the contents of a bundle, a large description — and hand it to every test that reads it

The second is what keeps the layers separate. Without it, every configuration and wiring test starts by finding the thing again, which quietly re-runs the existence layer inside the layers above it and blurs exactly the distinction this model exists to draw.

## Quick Reference

| If you want to test... | Layer |
| ------------------------ | ------- |
| A deployed thing was created | 1. Existence |
| A deployed thing holds a value the deployment set | 2. Configuration |
| A deployed bundle carries the contents it was built with | 2. Configuration |
| A component is attached to another | 3. Wiring |
| One thing is configured to trigger another | 3. Wiring |
| An identity is permitted to act on another component's behalf | 3. Wiring |
| A request from outside receives a response | E2E |
| Work put into the system comes out the other side | E2E |
| The journey a user takes, end to end | E2E |
