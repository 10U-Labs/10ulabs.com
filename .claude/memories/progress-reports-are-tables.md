---
name: progress-reports-are-tables
description: "A counting job's progress (listing, copy, poll — e.g. the S3 Glacier work) is reported as a markdown table; ordinary status updates are plain prose, not tables"
metadata:
  node_type: memory
  type: user
  originSessionId: 1a537a16-2797-49ae-a98b-30b527ea4b64
  modified: 2026-10-07T12:04:36.365Z
---

# Progress reports are tables — for counting jobs only

When reporting the progress of a long-running job that counts through items, such as a listing, copy or poll (the S3 Glacier work is where this arose), give it as a markdown table with one value per column (time, done, left, time to go, errors; no total column, since done plus left already gives it), not as a sentence stringing the numbers together.

This does not extend to other reports. Task-list status, CI waits, push results and replies to reminders are written as short plain prose, with no table.

**Why:** On 2026-10-07 the user found a progress sentence carrying a count, a total, a remainder, a problem count and a time left hard to read, and asked for a table. Later that day the user pointed out that the table rule was meant only for that kind of job-progress tracking, after tables had crept into every status update in the repo.

**How to apply:** For a counting job, keep the columns the same from one report to the next so they can be compared, use thousands separators, and give times in local time per [[report-times-in-local-time]]. For anything else, write a sentence or two.
