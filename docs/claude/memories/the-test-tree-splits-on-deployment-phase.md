# The test tree splits on deployment phase, then on tier

A subsystem that deploys has the same four directories available to it, and the first split is whether a deployment has to exist:

```text
{subsystem}/
├── pre_deployment/
│   ├── unit/
│   └── integration/
└── post_deployment/
    ├── integration/
    └── e2e/
```

The phase is the top split because two of the four tiers presume a deployment: post-deployment integration asks what shape it came out, and end to end asks what a caller receives from it. Neither can be attempted on a bare checkout. The other two run anywhere. Everything under `test/api/` and `test/www/` is laid out this way, and so is `test/bootstrap/`.

A tier directory appears when a test exists to put in it and not before. An absent directory is the honest answer, not a gap to fill.

What a test drives decides its tier, not how much of the program it strings together. `test/www/paths/home/pre_deployment/integration/test_05_existence.py` reads the Terraform on disk and touches nothing live. `test/www/paths/home/post_deployment/e2e/spa-routing.spec.ts` is end to end because its `playwright.config.ts` sets `baseURL` to `https://10ulabs.com` and it drives the deployed site. A journey against a local stub is pre-deployment integration however end-to-end it looks.

Code under `lib/` deploys nothing of its own and carries no such split, and this is the part that is easy to get wrong because it is the common case. `test/lib/python/` mirrors the package and stops: `test/lib/python/test_boto_mocks/` holds the tests for `lib/python/boto_mocks/`, with no tier directory in between. `test/lib/terraform/` names the module and then the one tier it has, as in `test/lib/terraform/s3_bucket/unit/test_s3_bucket_module.py`. Two of the four directories that owe tests are `lib/python/` and `lib/terraform/` — see [how-issues-are-written](how-issues-are-written.md) — so an issue whose regression section promises `test/lib/python/pre_deployment/unit/` is promising a directory that exists nowhere in the tree, and the session that picks it up will either create it or quietly do something else.

What each tier is required to assert is in `docs/tenets/tests/` — see [read-test-tenets-first](read-test-tenets-first.md).
