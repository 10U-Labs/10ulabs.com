# Test code is placed by how many suites use it

## Table of Contents

- [The rule](#the-rule)
- [A fixture goes as high as it still applies](#a-fixture-goes-as-high-as-it-still-applies)
- [What a helper is named after decides nothing](#what-a-helper-is-named-after-decides-nothing)
- [Check before creating](#check-before-creating)
- [Related notes](#related-notes)

## The rule

Test code that is not itself a test — a fixture, a mock factory, a loader, a parser — is written once and placed where every suite that needs it can see it and no suite that does not has to read it. One question decides the place: how many suites call it. Nothing else does, and in particular the subsystem the thing is about does not.

## A fixture goes as high as it still applies

Fixtures cascade down the test tree, so a fixture is written at the highest level where it still applies and inherited from there. A fixture every test wants sits at the root of the tree, one every test of a subsystem wants sits at that subsystem's directory, and one that only a single tier of a single endpoint wants sits in that tier's own configuration file. Writing it lower than it applies is what produces two copies, and two copies is what drifts.

There is no level for one file. A fixture only one test file uses is that file's business and stays in it.

## What a helper is named after decides nothing

A helper several suites call belongs to the shared Python library, whatever subsystem its name mentions. The website fixtures there are named for one subsystem and are shared all the same, because two suites build their own fixtures out of them. A helper one suite calls belongs beside that suite, however general it sounds.

The failure this catches is a module at the root of the test tree that only one subsystem imports. The root is where every suite looks, so putting a single caller's helper there tells every other suite it has something to read, and the mistake reads as tidiness rather than as a mistake.

## Check before creating

The common fixtures already exist, so writing a new one starts with reading rather than writing. Read the configuration files above the one in hand, because the fixture may already be inherited. Read the packages under `lib/python/`, which is what the shared library holds. Read the shared AWS fixture plugin in particular, since the whole tree already loads it and the clients and identities it provides are the ones most often written again by hand.

## Related notes

The inventory is described in [tenets-are-generic](tenets-are-generic.md), which is also why that file loses to the tree when the two disagree. Where the tests themselves go, rather than the code they share, is [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md).
