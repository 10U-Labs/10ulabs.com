# A conftest is emptied, never deleted

## Table of Contents

- [The rule](#the-rule)
- [Why an empty file earns its place](#why-an-empty-file-earns-its-place)
- [What emptying looks like](#what-emptying-looks-like)
- [Where this came from](#where-this-came-from)
- [Related notes](#related-notes)

## The rule

A file named `conftest.py` is one pytest loads by itself, without anything importing it, before running any test in its directory or in any directory below. Shared test setup goes there, and a fixture — a named piece of setup a test asks for by writing that name as one of its parameters — is written at the highest such file where it still applies. When the last thing in one of these files goes, the file stays and is emptied to nothing. Never delete it.

## Why an empty file earns its place

The empty file is a message to whoever writes the next fixture, and here that is almost always a session like this one. Left to itself a session writes setup into the test file already open in front of it, and the same setup is then copied into every test file that needs it. Sessions reach for these shared files rarely enough that the prompt has to come from the tree rather than from the writer. A file sitting at the level where the setup belongs is that prompt. A directory with nothing in it offers nothing to notice, so the duplication happens and is found later, by which point there are several copies to reconcile rather than one place to write.

Nothing enforces this. No check anywhere counts these files or objects to one going missing, which is exactly why it is written down: the convention survives only by being read.

## What emptying looks like

Zero bytes. Not a docstring saying the file is intentionally empty, not a comment explaining where the fixtures went, nothing. A file that still says something is a file the next reader has to read before learning it holds nothing, and the reason for the emptiness belongs in this note rather than copied into every file that has been emptied.

Emptying rather than deleting also costs nothing elsewhere. A workflow that names one of these files, in the paths that decide whether it runs or in the list of files it hands to a linter, keeps working untouched, where a deletion would mean editing every one of them.

## Where this came from

Written on 2026-08-23, when the shared setup file above all three API endpoint suites was emptied. It defined ten things. Nine were reached by nothing at all, and the tenth was a copy of a fixture already defined one level above it, so every test kept passing when the file went to nothing.

## Related notes

Related: [test-code-is-placed-by-how-many-suites-use-it](test-code-is-placed-by-how-many-suites-use-it.md), for the placement rule this convention protects — a fixture at the highest level that applies, inherited from there rather than copied down. [the-test-tree-splits-on-deployment-phase](the-test-tree-splits-on-deployment-phase.md), for which directories exist to hold one of these files in the first place.
