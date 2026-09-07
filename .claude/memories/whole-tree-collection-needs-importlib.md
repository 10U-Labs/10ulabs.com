---
name: whole-tree-collection-needs-importlib
description: "Collecting test/ whole requires --import-mode=importlib, because nine test files share a basename and the __init__.py that separated them are gone."
metadata: 
  node_type: memory
  type: project
  originSessionId: c67dcfb9-0480-4d04-98d5-0f32b2f7d8f2
  modified: 2026-09-07T23:47:43.948Z
---

# Collecting test/ whole needs --import-mode=importlib

Any pytest run that collects `test/` whole must pass `--import-mode=importlib`.
Without it collection dies with 89 `import file mismatch` errors: nine files are
named `test_01_existence.py`, nine `test_03_wiring.py` and so on across the
subsystems, and commit `026cedd5` deleted the 92 empty `__init__.py` that used to
keep their module paths distinct.

**Why:** no CI job had ever hit this, because each workflow collects only its own
subtree, where basenames do not repeat. It only appears for a tool that reads the
whole tree at once — which is what `assert-pytest-fixture-is-requested` does, and
why `--import-mode=importlib` is its default.

**How to apply:** when running pytest over `test/` as a whole locally or in a new
job, add `--import-mode=importlib`, and set `PYTHONPATH=lib/python:scripts` with
`boto3 botocore dnspython pytest requests` installed — that is the full set the
whole tree imports. Anything less produces collection errors, and a file that
fails to import registers none of its fixture requests. See
[[fixture-liveness-is-a-collection-question]].
