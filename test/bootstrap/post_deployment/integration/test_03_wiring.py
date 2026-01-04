"""Layer 3: Wiring tests for bootstrap post-deployment.

These tests verify that components are connected properly.
Tests assume Layer 1 existence and Layer 2 configuration tests have passed.
"""



# =============================================================================
# CloudTrail Wiring
# =============================================================================


def test_cloudtrail_writes_logs_to_s3(s3_client, cloudtrail_client):
    """Test that CloudTrail writes logs to S3."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    objects = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
    key_count = objects['KeyCount']
    assert key_count > 0


def test_cloudtrail_writes_logs_to_cloudwatch(logs_client, cloudtrail_client):
    """Test that CloudTrail writes logs to CloudWatch."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]
    streams = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    assert len(streams['logStreams']) > 0


# =============================================================================
# Central Logs Wiring
# =============================================================================


def test_central_logs_write_policy_exists(iam_client):
    """Test that central logs write policy exists."""
    policy_name = 'central-logs-write-policy'
    response = iam_client.list_policies(Scope='Local')
    policy_names = [p['PolicyName'] for p in response['Policies']]
    assert policy_name in policy_names
