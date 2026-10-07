---
name: fixing-a-red-run
description: "When the run a session's push starts goes red, that session fixes it, whether the push broke something or inherited the break, in a push of its own before the next batch"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 120de421-48c5-4cd5-a81d-e0448051ac54
  modified: 2026-10-07T02:52:43.775Z
---

# Fixing a red run after a push

When the CI run a push starts goes red, the session that pushed fixes it, whether the push caused the failure or inherited it from an earlier commit. What sets the rule off is a push's own run going red, not a red run the session merely comes across.

**Why:** a change is unverified until the jobs that test it have actually run, and a conclusion of `failure` reads the same whether the change broke something or inherited a break. A skipped job reports neither pass nor fail. So an inherited failure hides the change's own result for as long as it stands, and the session that pushed is the one whose change is left unverified.

**How to apply:** once the push's run has completed, `gh run view <id> --log-failed` tells a break the change caused from one it inherited. Fix both kinds, forward, per [[a-rejected-push-is-fixed-forward]]. The fix goes in a push of its own, before the next batch of issues ([[a-push-solves-every-open-issue-of-one-stack]]): pushed together, a second red run could not say whether the fix or the batch broke it.
