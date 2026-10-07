---
name: progress-reports-are-tables
description: "Give the user a progress or status report as a small markdown table, one value per column, never as a run-on sentence of numbers"
metadata:
  node_type: memory
  type: user
  originSessionId: 1a537a16-2797-49ae-a98b-30b527ea4b64
  modified: 2026-10-07T10:51:29.783Z
---

# Progress reports are tables

When reporting the progress of a running job, such as a listing, copy or poll, give it as a markdown table with one value per column (time, done, left, time to go, errors; no total column, since done plus left already gives it), not as a sentence stringing the numbers together.

**Why:** On 2026-10-07 the user found a progress sentence carrying a count, a total, a remainder, a problem count and a time left hard to read, and asked for a table.

**How to apply:** Keep the columns the same from one report to the next so they can be compared, use thousands separators, and give times in local time per [[report-times-in-local-time]].
