---
name: a-wait-runs-in-the-background
description: "A wait for CI or anything else is a Bash run_in_background or a Monitor, never a foreground sleep or gh run watch, so the session stays idle and the autopilot reminders can fire"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:56:43.582Z
---

# A wait runs in the background

Waiting for a workflow run, an invalidation or anything else that takes minutes is done with `Bash` and `run_in_background: true` (one notification when the condition holds) or with `Monitor` (one event per occurrence), never with a foreground `sleep`, `gh run watch` or a polling loop in the session's own shell.

**Why:** the user said so in api.10ulabs.com: wait with Monitor or a background shell rather than a sleep in the session, because a sleep ties up the session and stops the reminders. Cron reminders fire only while the session is idle; a foreground wait holds it busy for the whole run, so the standing rules stop arriving exactly when they are most needed, and the user cannot type either. The user adopted the rule here on 2026-10-06.

**How to apply:** start the wait in the background, end the turn, and act on the completion notification. Find the run by its full hash, per [[find-a-run-by-the-full-hash]]. The autopilot's wait reminder still holds: idle means idle, not doing other work meanwhile.
