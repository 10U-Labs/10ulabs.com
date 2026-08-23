# An issue states one solution

## Table of Contents

- [The rule](#the-rule)
- [Why a fork is settled before filing](#why-a-fork-is-settled-before-filing)
- [Ask first and write the answer](#ask-first-and-write-the-answer)
- [Naming the branch that lost](#naming-the-branch-that-lost)
- [Issues already on disk](#issues-already-on-disk)
- [The reasoning to watch for](#the-reasoning-to-watch-for)
- [Related notes](#related-notes)

## The rule

An issue is the instruction to whoever picks it up, and it has to be workable on its own. Its `Proposed Solution` names one change: this function, this file, this algorithm, this test. Not two options to weigh, not a menu with a recommendation, and never a question the reader is left holding. If the section ends with something still to decide, the issue is not finished and should not be filed.

## Why a fork is settled before filing

The trade-off behind an "either" is usually real. Settling it is what makes the issue worth filing, and the place to settle it is before the issue exists, in the conversation where the measurements are fresh and the person who can decide is present. An issue is read weeks later by somebody who was not in that conversation and cannot reconstruct it. Filing the question instead of the answer moves the hardest part of the work onto them and calls it a deliverable.

## Ask first and write the answer

So when a draft reaches a genuine fork, stop and ask which branch, then write the one that came back. The ask moves in front of the filing rather than into the body of it. Asking costs one turn; filing an undecided issue costs the decision being made later by whoever is in a hurry, or made twice.

## Naming the branch that lost

Definitive does not mean silent about what was rejected. Naming the alternative and saying why it lost is worth writing, because it stops the same ground being covered again. The difference is whether the sentence has a verb the reader can act on.

## Issues already on disk

The older half of this rule is about issues already on disk. Where a filed `Proposed Solution` says "either X or Y", do not pick, however clearly the text leans toward one and even when it calls one the smaller change; ask which one before editing a file, and ask before there is a draft, because a draft turns the question into a request to approve what is already done.

## The reasoning to watch for

The reasoning that an either belongs to the user is the one to watch for, because it is half right: the fork does need the user, and what follows from that is asking before the issue is filed, not publishing the fork inside it. An issue that offers two incompatible options gets solved down whichever one it called smaller, and being smaller is not the same as being right.

## Related notes

The sections an issue has and the order they come in are in [how-issues-are-written](how-issues-are-written.md).
