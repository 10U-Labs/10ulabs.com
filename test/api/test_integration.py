import json
import boto3


def test_stack_deployed_successfully(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    assert len(stacks['Stacks']) == 1


def test_api_gateway_exists(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_names = [api['name'] for api in apis['items']]
    assert 'TenULabsApi' in api_names


def test_api_gateway_has_health_resource(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/health' in resource_paths


def test_api_gateway_has_v1_echo_resource(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/v1/echo' in resource_paths


def test_api_gateway_health_has_get_method(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    resources = apigw_client.get_resources(restApiId=api_id)
    health_resource = None
    for r in resources['items']:
        if r['path'] == '/health':
            health_resource = r
            break
    assert 'GET' in health_resource['resourceMethods']


def test_api_gateway_echo_has_post_method(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    resources = apigw_client.get_resources(restApiId=api_id)
    echo_resource = None
    for r in resources['items']:
        if r['path'] == '/v1/echo':
            echo_resource = r
            break
    assert 'POST' in echo_resource['resourceMethods']


def test_health_lambda_function_exists(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    matching_functions = [name for name in function_names if 'HealthHandler' in name]
    assert len(matching_functions) > 0


def test_echo_lambda_function_exists(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    matching_functions = [name for name in function_names if 'EchoHandler' in name]
    assert len(matching_functions) > 0


def test_health_lambda_has_correct_runtime(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=health_handler)
    assert function_config['Runtime'].startswith('python3')


def test_echo_lambda_has_correct_runtime(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=echo_handler)
    assert function_config['Runtime'].startswith('python3')


def test_health_lambda_has_timeout_configured(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=health_handler)
    assert function_config['Timeout'] > 0


def test_echo_lambda_has_timeout_configured(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=echo_handler)
    assert function_config['Timeout'] > 0


def test_health_lambda_has_memory_configured(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=health_handler)
    assert function_config['MemorySize'] > 0


def test_echo_lambda_has_memory_configured(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=echo_handler)
    assert function_config['MemorySize'] > 0


def test_health_lambda_has_execution_role(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=health_handler)
    assert 'Role' in function_config


def test_echo_lambda_has_execution_role(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=echo_handler)
    assert 'Role' in function_config


def test_health_lambda_has_cloudwatch_log_group(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    logs_client = boto3.client('logs', region_name=lambda_client.meta.region_name)
    log_groups = logs_client.describe_log_groups(logGroupNamePrefix=f'/aws/lambda/{health_handler}')
    assert len(log_groups['logGroups']) > 0


def test_echo_lambda_has_cloudwatch_log_group(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    logs_client = boto3.client('logs', region_name=lambda_client.meta.region_name)
    log_groups = logs_client.describe_log_groups(logGroupNamePrefix=f'/aws/lambda/{echo_handler}')
    assert len(log_groups['logGroups']) > 0


def test_health_lambda_can_be_invoked(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    response = lambda_client.invoke(
        FunctionName=health_handler,
        InvocationType='RequestResponse',
        Payload='{"path": "/health", "httpMethod": "GET"}'
    )
    assert response['StatusCode'] == 200


def test_echo_lambda_can_be_invoked(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    response = lambda_client.invoke(
        FunctionName=echo_handler,
        InvocationType='RequestResponse',
        Payload='{"path": "/v1/echo", "httpMethod": "POST", "body": "{\\"test\\": \\"data\\"}"}'
    )
    assert response['StatusCode'] == 200


def test_health_lambda_returns_valid_response(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    response = lambda_client.invoke(
        FunctionName=health_handler,
        InvocationType='RequestResponse',
        Payload='{"path": "/health", "httpMethod": "GET"}'
    )
    payload = json.loads(response['Payload'].read())
    assert 'statusCode' in payload


def test_echo_lambda_returns_valid_response(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    response = lambda_client.invoke(
        FunctionName=echo_handler,
        InvocationType='RequestResponse',
        Payload='{"path": "/v1/echo", "httpMethod": "POST", "body": "{\\"test\\": \\"data\\"}"}'
    )
    payload = json.loads(response['Payload'].read())
    assert 'statusCode' in payload


def test_certificate_exists_for_subdomain(acm_client, config):
    subdomain = config['domain_names']['subdomain']
    certificates = acm_client.list_certificates()
    cert_arns = [
        cert['CertificateArn']
        for cert in certificates['CertificateSummaryList']
        if cert['DomainName'] == subdomain
    ]
    assert len(cert_arns) > 0


def test_certificate_status_is_issued(acm_client, config):
    subdomain = config['domain_names']['subdomain']
    certificates = acm_client.list_certificates()
    cert_arn = None
    for cert in certificates['CertificateSummaryList']:
        if cert['DomainName'] == subdomain:
            cert_arn = cert['CertificateArn']
            break
    cert_details = acm_client.describe_certificate(CertificateArn=cert_arn)
    assert cert_details['Certificate']['Status'] == 'ISSUED'


def test_api_has_custom_domain_name(apigw_client, config):
    domain_names = apigw_client.get_domain_names()
    subdomain = config['domain_names']['subdomain']
    domain_name_values = [d['domainName'] for d in domain_names['items']]
    assert subdomain in domain_name_values


def test_stack_has_api_url_output(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])
    output_keys = [o['OutputKey'] for o in outputs]
    assert 'ApiUrl' in output_keys


def test_stack_has_api_endpoint_output(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])
    output_keys = [o['OutputKey'] for o in outputs]
    assert 'ApiEndpoint' in output_keys


def test_stack_has_api_domain_name_output(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])
    output_keys = [o['OutputKey'] for o in outputs]
    assert 'ApiDomainName' in output_keys


def test_s3_bucket_exists_for_api_docs(s3_client, config):
    subdomain = config['domain_names']['subdomain']
    expected_bucket_name = subdomain
    buckets = s3_client.list_buckets()
    bucket_names = [bucket['Name'] for bucket in buckets['Buckets']]
    assert expected_bucket_name in bucket_names


def test_s3_bucket_contains_index_html(s3_client, config):
    bucket_name = config['domain_names']['subdomain']
    objects = s3_client.list_objects_v2(Bucket=bucket_name)
    object_keys = [obj['Key'] for obj in objects.get('Contents', [])]
    assert 'index.html' in object_keys


def test_s3_bucket_contains_openapi_yaml(s3_client, config):
    bucket_name = config['domain_names']['subdomain']
    objects = s3_client.list_objects_v2(Bucket=bucket_name)
    object_keys = [obj['Key'] for obj in objects.get('Contents', [])]
    assert 'openapi.yaml' in object_keys


def test_s3_bucket_versioning_is_disabled(s3_client, config):
    bucket_name = config['domain_names']['subdomain']
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    status = versioning.get('Status', 'Disabled')
    assert status != 'Enabled'


def test_s3_bucket_has_encryption_enabled(s3_client, config):
    bucket_name = config['domain_names']['subdomain']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_cloudfront_distribution_exists(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    stack_resources = cloudformation_client.list_stack_resources(StackName='TenULabsApi')
    resource_types = [r['ResourceType'] for r in stack_resources['StackResourceSummaries']]
    assert 'AWS::CloudFront::Distribution' in resource_types


def test_api_gateway_can_invoke_health_lambda(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    health_handler = [name for name in function_names if 'HealthHandler' in name][0]
    policy = lambda_client.get_policy(FunctionName=health_handler)
    assert 'apigateway.amazonaws.com' in policy['Policy']


def test_api_gateway_can_invoke_echo_lambda(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    echo_handler = [name for name in function_names if 'EchoHandler' in name][0]
    policy = lambda_client.get_policy(FunctionName=echo_handler)
    assert 'apigateway.amazonaws.com' in policy['Policy']
