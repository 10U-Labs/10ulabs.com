---
name: file-an-issue-where-it-belongs
description: "An issue is filed in the repository whose code or resources it concerns, even when it is found from this one; the other-repositories reminder covers workflows and runs, not filing"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1a537a16-2797-49ae-a98b-30b527ea4b64
  modified: 2026-10-07T11:18:38.812Z
---

# File an issue where it belongs

A finding is filed as an issue in the repository that owns the code or the AWS resources it concerns, not left as a note in this repository and not filed here. Find the owner from the resource's `Repository` tag or the code's home.

**Why:** On 2026-10-07 the analysis of the September invoice (#801) traced $12.79 to the `api.10ulabs.com` distribution and only said a fix belonged in that repository. The user, confused whether anything had been filed there, said issues should be filed where they belong; it was then filed as 10U-Labs/api.10ulabs.com#253.

**How to apply:** Write the issue from what this session can see (AWS data, the bill), link it from the issue that found it, and stop there: the other repository's workflows and runs are still not read or waited on. Filing still waits on the user's go-ahead when the finding came from an analysis-only issue ([[an-analysis-issue-asks-for-analysis-only]]).
