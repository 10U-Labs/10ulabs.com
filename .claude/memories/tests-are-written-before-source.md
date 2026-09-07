---
name: tests-are-written-before-source
description: This repo is TDD — the test exists before the source it covers, so proposed test changes must stay valid in the window where the source is absent.
metadata:
  type: feedback
---

# Tests are written before source

Work in 10ulabs.com is test-driven: the test lands before the code or Terraform it covers. There is always a window in which a stack's tests exist and its `src/<stack>/` does not. Any design that has a test read the source tree must behave correctly in that window.

**Why:** I proposed (on #772) that four tests read the state key out of each stack's `backend.tf` instead of hardcoding it, and the user pushed back: "We do TDD. Tests exist before source code does. Ergo, how can a test read from a file that does not exist yet?" The convention is documented nowhere — there is no `CLAUDE.md`, and no TDD note in the docs or workflows — so it has to be remembered.

**How to apply:** Reading a not-yet-written file is not itself the problem — a test that names a missing file and goes red saying so is the red TDD asks for, and it beats a hardcoded value that fails with an unrelated message. What matters is *where* it fails:

- Put such a read behind a **fixture**, never a module-level constant. At module level the absence raises during import, which pytest reports as a collection error: the module never runs and it reads as a broken suite. Behind a fixture, only the test that asked for the value errors, it carries the missing path, and the rest of the module still reports.
- Do **not** soften the absence with a default, a `None`, or a `pytest.skip`. That makes a new stack's tests green before the stack exists, which is the silent-pass failure most of these issues are about.

See [[commits-go-straight-to-main]] and [[do-not-run-test-suites-locally]] for the other unwritten conventions of this repo.
