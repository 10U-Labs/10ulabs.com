---
name: fixture-liveness-is-a-collection-question
description: Whether a pytest fixture is live cannot be answered by matching its name; it needs a real pytest collection plus a parse for getfixturevalue.
metadata: 
  node_type: memory
  type: project
  originSessionId: c67dcfb9-0480-4d04-98d5-0f32b2f7d8f2
  modified: 2026-09-07T23:47:53.069Z
---

# Fixture liveness is a collection question, not a name match

Deciding whether a pytest fixture is still asked for takes two different reads,
and using only one gives wrong answers in both directions.

**A collection answers reachability.** Only pytest knows which definition a
request resolves to (where two conftests publish the same name, every requester
may resolve to the nearer one, leaving the farther one dead), and only pytest
knows that a test method inside a factory nothing calls never becomes a test.
Matching names credited four dead fixtures on this tree — `sqs_client`,
`ec2_client`, `api_url` and `test_device_id` — all deleted under `#788`.

**A parse answers `getfixturevalue`.** A collection cannot see it at all.
`pytest-deadfixtures` reads no form of it and so reports ten live fixtures here
as dead, including `health_handler_log_group` and `diagnostics_handler_log_group`,
whose deletion in `0e61a640` turned two post-deployment suites red.

**Why:** the two published tools split along exactly this line, which is why
neither was adoptable and `assert-pytest-fixture-is-requested` was built.
`pytest-unused-fixtures` would be accurate but needs one session that runs every
tier, which the deploy-gated tiering here makes impossible.

**How to apply:** never conclude a fixture is dead from a grep or an `ast` name
match. Run the job's own command, which is in all eleven workflows. Needs
[[whole-tree-collection-needs-importlib]].
