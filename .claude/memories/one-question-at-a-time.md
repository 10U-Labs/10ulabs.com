---
name: one-question-at-a-time
description: "Ask the user one question per message, in plain words; queue the rest as tasks and ask them one by one"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:52:10.220Z
---

# One question at a time

Put exactly one question to the user per message. When several decisions are pending, file each as a task ("Ask the user whether …, then wait") and ask them one after another, each after the last is answered.

**Why:** The user said so on 2026-10-06, after a session asked several questions in one message, each with background, options and recommendations. A person cannot take in and answer many distinct questions at once the way a model can, gets confused when handed a pile of them, and prefers one question at a time.

**How to apply:** Lead with the question in a sentence or two of plain words, give a recommendation, and stop. Do not attach a second question, a side conflict or a list of findings to the same message; each of those becomes its own task. When the user says they are lost, start over from the smallest concrete example rather than restating the long version.
