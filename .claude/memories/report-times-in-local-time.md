---
name: report-times-in-local-time
description: "Give times to the user in the local machine's timezone (from `date`), never in UTC/Zulu"
metadata:
  node_type: memory
  type: user
  originSessionId: 1a537a16-2797-49ae-a98b-30b527ea4b64
  modified: 2026-10-07T10:48:02.522Z
---

# Report times in local time

When telling the user a time, such as a progress line, an estimate of when something finishes or when a run started, give it in the local machine's timezone as `date` prints it (US Eastern, EDT or EST), never in UTC or Zulu. Status scripts whose lines the user reads print `date +'%-I:%M:%S %p %Z'`, not `date -u`.

**Why:** On 2026-10-07 the user asked for progress reports in the machine's timezone rather than Zulu time.

**How to apply:** Convert any UTC time from AWS, GitHub or a log before stating it. Related: [[a-wait-runs-in-the-background]].
