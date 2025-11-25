import boto3


def test_waf_web_acl_exists():
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    acl_names = [acl['Name'] for acl in response['WebACLs']]
    assert 'ApiWafWebAcl' in acl_names


def test_waf_web_acl_has_cloudwatch_metrics_enabled():
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    acl_found = False
    metrics_enabled = False
    if response['WebACLs']:
        acl_found = True
        acl = response['WebACLs'][0]
        acl_detail = waf_client.get_web_acl(Name=acl['Name'], Scope='CLOUDFRONT', Id=acl['Id'])
        metrics_enabled = acl_detail['WebACL']['VisibilityConfig']['CloudWatchMetricsEnabled']
    assert acl_found
    assert metrics_enabled


def test_waf_log_group_exists():
    logs_client = boto3.client('logs', region_name='us-east-1')
    response = logs_client.describe_log_groups(logGroupNamePrefix='aws-waf-logs-api')
    log_groups = [lg['logGroupName'] for lg in response['logGroups']]
    assert 'aws-waf-logs-api' in log_groups


def test_waf_log_group_retention_is_30_days():
    logs_client = boto3.client('logs', region_name='us-east-1')
    response = logs_client.describe_log_groups(logGroupNamePrefix='aws-waf-logs-api')
    retention_correct = False
    if response['logGroups']:
        retention_correct = response['logGroups'][0].get('retentionInDays') == 30
    assert retention_correct


def test_waf_logging_configuration_exists():
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    logging_configured = False
    if response['WebACLs']:
        acl = response['WebACLs'][0]
        acl_arn = acl['ARN']
        logging_config = waf_client.get_logging_configuration(ResourceArn=acl_arn)
        logging_configured = 'LoggingConfiguration' in logging_config
    assert logging_configured


def test_waf_logging_destinations_cloudwatch_logs():
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    destination_correct = False
    if response['WebACLs']:
        acl = response['WebACLs'][0]
        acl_arn = acl['ARN']
        logging_config = waf_client.get_logging_configuration(ResourceArn=acl_arn)
        destinations = logging_config['LoggingConfiguration']['LogDestinationConfigs']
        destination_correct = 'aws-waf-logs-api' in destinations[0]
    assert destination_correct
