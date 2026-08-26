import pytest

from test_fixtures.aws import iam_role_exists


def test_lambda_catchall_handler_exists(lambda_client, shared_config):
    function_name = shared_config['lambda_handler_names']['catchall']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_catchall_handler_role_exists(iam_client, shared_config):
    role_name = f"{shared_config['resource_prefix']}CatchAllHandlerServiceRole"
    assert iam_role_exists(iam_client, role_name), f"IAM role '{role_name}' not found"


def test_api_gateway_api_key_exists(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_api_keys()
    assert len(response['items']) > 0


def test_api_gateway_usage_plan_exists(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_usage_plans()
    assert len(response['items']) > 0


def test_api_gateway_usage_plan_key_exists(apigateway_client, usage_plan_id):
    if usage_plan_id is None:
        pytest.skip("Usage plan not found")
    response = apigateway_client.get_usage_plan_keys(usagePlanId=usage_plan_id)
    assert len(response['items']) > 0


def test_s3_docs_bucket_exists(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_index_html_exists_in_s3(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_json_exists_in_s3(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.json")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_404_html_exists_in_s3(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="404.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_policy_exists(s3_client, config):
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_policy(Bucket=bucket_name)
    assert 'Policy' in response


def test_cloudfront_distribution_exists(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions['DistributionList']
    assert distribution_list['Quantity'] > 0


def test_acm_certificate_exists(acm_client):
    certificates = acm_client.list_certificates()
    assert certificates['CertificateSummaryList']


def test_cloudfront_origin_access_control_exists(cloudfront_client):
    response = cloudfront_client.list_origin_access_controls()
    oac_list = response['OriginAccessControlList'].get('Items', [])
    assert len(oac_list) > 0


def test_route53_api_record_exists(api_route53_records, config):
    if api_route53_records is None:
        pytest.skip("Hosted zone not found")
    record_names = [r['Name'].rstrip('.') for r in api_route53_records]
    assert config['api_fqdn'] in record_names


def test_firehose_delivery_stream_exists(firehose_client, config):
    stream_name = config['firehose_delivery_stream_name']
    response = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
    assert response['DeliveryStreamDescription']['DeliveryStreamName'] == stream_name


def test_firehose_role_exists(iam_client, config):
    response = iam_client.get_role(RoleName=config['firehose_role_name'])
    assert response['Role']['RoleName'] == config['firehose_role_name']


def test_cloudwatch_logs_firehose_role_exists(iam_client, config):
    role_name = config['cloudwatch_logs_firehose_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_api_audit_log_table_exists(dynamodb_client, shared_config):
    table_name = f"{shared_config['resource_prefix']}ApiAuditLog"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableName'] == table_name


def test_api_key_ssm_parameter_exists(ssm_client, config):
    param_name = config['ssm_parameter_name_for_api_key']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=False)
    assert response['Parameter']['Name'] == param_name


def test_api_gateway_rest_api_exists(apigateway_client, config):
    apis = apigateway_client.get_rest_apis()
    api_names = [api['name'] for api in apis['items']]
    assert config['api_gateway_name'] in api_names


def test_api_gateway_stage_exists(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        pytest.skip("API Gateway not found")
    response = apigateway_client.get_stage(restApiId=api_gateway_id, stageName='prod')
    assert response['stageName'] == 'prod'


def test_api_gateway_cloudwatch_role_exists(iam_client, config):
    role_name = config['api_gateway_cloudwatch_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_cloudfront_url_rewrite_function_exists(cloudfront_client):
    response = cloudfront_client.list_functions()
    function_names = [f['Name'] for f in response['FunctionList'].get('Items', [])]
    assert 'RootUrlRewriteFunction' in function_names
