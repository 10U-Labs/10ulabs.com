---
name: issues-have-no-house-style
description: "This repo has no conventions for how an issue is written beyond one: a part of the body takes a header, never a bolded first sentence; a pattern the existing issues share is not a rule"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:52:29.733Z
---

# Issues have no house style

This repository has no conventions on how an issue is written. Many of the issues share the seven headings from `Problem` through `Proposed Solution` that an earlier autopilot reminder asked for, but that reminder is gone, and none of those headings is a rule.

**Why:** The user dropped the seven-header format on 2026-10-06 and asked for the rule api.10ulabs.com already follows. A pattern that was never decided, or no longer is, cannot be enforced, and reading one as a rule makes an issue worse by forcing content into a heading it does not fit.

**How to apply:** When writing or editing an issue, ignore whatever pattern the other issues happen to share and write it however best says what it needs to say. Do not add, rename or reorder sections to match the neighbours, and do not flag a divergence from them as a problem. The one thing an issue still carries is what [[an-issue-is-closed-by-its-commit]] relies on: its number, so the commit can name it.

One rule does hold: a part of the body is introduced by a Markdown header (`## Decision`), never by bolding its first sentence (`**Decided:** ...`).
