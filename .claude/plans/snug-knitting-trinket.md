# Remove Orphaned WAF Resources

WAF was removed in commit `b4433b87` but cleanup was incomplete.

## Files to Modify

### Terraform

**`src/api/common/routing/log_subscriptions.tf`**
- Delete lines 17-26 (`aws_cloudwatch_log_subscription_filter.waf`)

**`src/api/common/routing/firehose.tf`**
- Delete `aws_kinesis_firehose_delivery_stream.waf_logs`
- Delete `aws_iam_role.firehose_waf_logs`
- Delete `aws_iam_role_policy.firehose_waf_s3_access`
- Delete `aws_iam_role.cloudwatch_logs_firehose_waf`
- Delete `aws_iam_role_policy.cloudwatch_logs_firehose_waf_access`

### Tests

**`test/api/common/routing/post_deployment/integration/conftest.py`**
- Delete `waf_logging_config_fixture`

**`test/api/common/routing/post_deployment/integration/test_01_existence.py`**
- Delete `test_waf_web_acl_exists`
- Delete `test_waf_log_group_exists`
- Delete `test_waf_firehose_delivery_stream_exists`

**`test/api/common/routing/post_deployment/integration/test_03_wiring.py`**
- Delete `test_cloudfront_waf_web_acl_association`
- Delete `test_waf_subscription_filter_exists`
- Delete `test_waf_firehose_s3_policy_has_all_required_actions`
- Delete `test_waf_logging_configuration_exists`
- Delete `test_waf_logging_destinations_cloudwatch_logs`

## Verification

1. Run `terraform plan` in `src/api/common/routing/` - should show resource deletions only
2. Run pre-deployment tests locally
3. Push and let workflowctl run
