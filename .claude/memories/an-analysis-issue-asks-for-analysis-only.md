---
name: an-analysis-issue-asks-for-analysis-only
description: "When an issue asks for an analysis, its body states the request, the results go in a comment, and nothing more is filed or started without the user's go-ahead"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1a537a16-2797-49ae-a98b-30b527ea4b64
  modified: 2026-10-07T11:19:26.329Z
---

# An analysis issue asks for analysis only

When an issue asks to analyze something, such as a bill, a design or a log, its work is the analysis. The body states the request (what is to be analyzed and that acting on a finding is a separate decision), and the results (breakdown, findings, recommendation) are posted as a comment on it, not written into the body. Do not turn a finding into an issue of its own, and do not start changing code, workflows or infrastructure because of one, until the user says to.

**Why:** On 2026-10-07 #801 asked for the last AWS invoice to be analyzed for savings. The session wrote up the analysis, then filed #802 for a saving it found and began pushing changes for it; the user stopped it, pointing out that the issue asked for an analysis only, and had the body rewritten as the request with the results posted as a comment.

**How to apply:** Give the results in a comment on the issue and in the reply to the user, then ask whether to act on them. A cost analysis's results end with a section showing how a future bill would look with the proposed changes in place: the analyzed bill replayed line by line beside the same bill with the changes, its total and its saving, plus what a quiet month would come to. This is the one place results go in a comment; a decision still rewrites the issue ([[a-decision-rewrites-the-issue]]). Related: [[a-written-plan-is-decided]].
