def test_stack_creates_lambda_function(cdk_template):
    assert cdk_template.resource_count_is("AWS::Lambda::Function", 1)


def test_stack_creates_api_gateway_resources(cdk_template):
    assert cdk_template.resource_count_is("AWS::ApiGateway::Resource", 1)


def test_stack_creates_api_gateway_methods(cdk_template):
    assert cdk_template.resource_count_is("AWS::ApiGateway::Method", 1)
