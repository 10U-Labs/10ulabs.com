---
name: a-written-plan-is-decided
description: "A plan an unlabelled issue already states is decided; touching live AWS data or costing a few cents is not by itself a reason to label it `needs decision`"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1a537a16-2797-49ae-a98b-30b527ea4b64
  modified: 2026-10-07T04:03:35.983Z
---

# A written plan is decided

When an issue without `needs decision` already states what is to be done, that plan is the decision. Carry it out; do not turn it back into a question. That the work changes live data, such as rewriting objects in an AWS bucket, or carries a small cost, is not on its own a reason to label it `needs decision`.

**Why:** On 2026-10-06 a session labelled #793 `needs decision` and rewrote its title as a choice between moving the central logs from Glacier Flexible Retrieval to Instant Retrieval and leaving them. The user pointed out that the move had been the plan all along, so there was nothing to decide.

**How to apply:** Before labelling, read the issue's own body and title: if they already name the outcome, the label is wrong. Label only where the issue, the code and these memories leave a real choice open, such as two outcomes the issue does not choose between. A consequence the plan carries, such as a restarted expiry, belongs in the body as a note, not as a question. Related: [[a-decision-rewrites-the-issue]].
