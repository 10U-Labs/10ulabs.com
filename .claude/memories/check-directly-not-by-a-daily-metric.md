---
name: check-directly-not-by-a-daily-metric
description: "Confirm an AWS change by querying the resources themselves, which answers at once, never by waiting on a daily metric such as S3's BucketSizeBytes"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1a537a16-2797-49ae-a98b-30b527ea4b64
  modified: 2026-10-07T10:44:40.401Z
---

# Check directly, not by a daily metric

When AWS work needs confirming, query the resources themselves, such as `list-objects-v2` or `head-object` for S3 storage classes, and take the answer at once. Do not wait on a metric AWS publishes once a day, such as S3's `BucketSizeBytes` by `StorageType`, when a direct query can say the same thing now.

**Why:** On 2026-10-07 #793 had moved 1,657 central logs to Glacier Instant Retrieval, and the session set a job to poll the daily `GlacierStorage` metric for up to a day before closing the issue. The user asked why the work hung on a daily AWS report when the answer could be had directly and at once.

**How to apply:** Write an issue's done line as a direct check, such as a bucket listing that finds no object in a storage class. Use a daily metric only where no direct query can answer, and say so in the issue. Related: [[a-written-plan-is-decided]].
