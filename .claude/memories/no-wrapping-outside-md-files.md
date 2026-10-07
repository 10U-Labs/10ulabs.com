---
name: no-wrapping-outside-md-files
description: GitHub issue bodies and comments get no hard wrapping at all; one line per paragraph and per list item
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:58:36.771Z
---

# No wrapping outside .md files

Do not hard-wrap text written outside `.md` files. GitHub issue bodies and comments get one line per paragraph and per list item, with no newline characters inside either.

**Why:** Wrapping at a column exists to keep the diffs of checked-in files readable. An issue body has no diff to keep clean, GitHub wraps it to the reader's own width, and hard newlines make the web editor and quote-replies awkward. The rule comes from the `assert-*` repositories, and the user adopted it here on 2026-10-06.

**How to apply:** Everywhere outside the repository's `.md` files, write each paragraph as a single line. Do not describe this as "soft-wrapping": there is no wrapping of any kind. How an issue is otherwise shaped is [[issues-have-no-house-style]].
