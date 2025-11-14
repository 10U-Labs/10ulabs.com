def test_api_gateway_exists(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_names = [api['name'] for api in apis['items']]
    assert 'TenULabsApi' in api_names


def test_lambda_function_exists(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    matching_functions = [name for name in function_names if 'ApiHandler' in name]
    assert len(matching_functions) > 0


def test_api_has_custom_domain_name(apigw_client, config):
    domain_names = apigw_client.get_domain_names()
    subdomain = config['domain_names']['subdomain']
    domain_name_values = [d['domainName'] for d in domain_names['items']]
    assert subdomain in domain_name_values


def test_stack_deployed_successfully(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    assert len(stacks['Stacks']) == 1


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


def test_api_gateway_has_proxy_plus_resource(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/{proxy+}' in resource_paths


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


def test_lambda_function_can_be_invoked(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    api_handler = [name for name in function_names if 'ApiHandler' in name][0]
    response = lambda_client.invoke(
        FunctionName=api_handler,
        InvocationType='RequestResponse',
        Payload='{"path": "/health", "httpMethod": "GET"}'
    )
    assert response['StatusCode'] == 200


def test_lambda_function_returns_valid_response(lambda_client):
    import json
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    api_handler = [name for name in function_names if 'ApiHandler' in name][0]
    response = lambda_client.invoke(
        FunctionName=api_handler,
        InvocationType='RequestResponse',
        Payload='{"path": "/health", "httpMethod": "GET"}'
    )
    payload = json.loads(response['Payload'].read())
    assert 'statusCode' in payload


def test_lambda_function_has_cloudwatch_log_group(lambda_client):
    import boto3
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    api_handler = [name for name in function_names if 'ApiHandler' in name][0]
    logs_client = boto3.client('logs', region_name=lambda_client.meta.region_name)
    log_groups = logs_client.describe_log_groups(logGroupNamePrefix=f'/aws/lambda/{api_handler}')
    assert len(log_groups['logGroups']) > 0


def test_lambda_function_has_execution_role(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    api_handler = [name for name in function_names if 'ApiHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=api_handler)
    assert 'Role' in function_config


def test_lambda_function_has_correct_runtime(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    api_handler = [name for name in function_names if 'ApiHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=api_handler)
    assert function_config['Runtime'].startswith('python3')


def test_lambda_function_has_timeout_configured(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    api_handler = [name for name in function_names if 'ApiHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=api_handler)
    assert function_config['Timeout'] > 0


def test_lambda_function_has_memory_configured(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    api_handler = [name for name in function_names if 'ApiHandler' in name][0]
    function_config = lambda_client.get_function_configuration(FunctionName=api_handler)
    assert function_config['MemorySize'] > 0


def test_poll_api_can_connect_to_real_endpoint():
    import requests
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    import poll_api_until_it_has_propagated
    result = poll_api_until_it_has_propagated.poll_until_propagated(
        'https://httpbin.org/status/404',
        max_attempts=1
    )
    assert result is True


def test_poll_api_handles_network_errors():
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    import poll_api_until_it_has_propagated
    result = poll_api_until_it_has_propagated.poll_until_propagated(
        'https://invalid-domain-that-does-not-exist-12345.com',
        max_attempts=1
    )
    assert result is False


def test_poll_api_handles_ssl_endpoints():
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    import poll_api_until_it_has_propagated
    result = poll_api_until_it_has_propagated.poll_until_propagated(
        'https://httpbin.org/status/404',
        max_attempts=1
    )
    assert result is True
