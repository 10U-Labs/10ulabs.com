def test_config_file_exists_in_correct_location(config_path):
    assert config_path.exists()


def test_stack_synthesizes_successfully(cdk_template):
    assert cdk_template is not None


def test_lambda_function_exists(cdk_template):
    cdk_template.resource_count_is("AWS::Lambda::Function", 1)


def test_api_gateway_resources_exist(cdk_template):
    cdk_template.resource_count_is("AWS::ApiGateway::Resource", 3)


def test_api_gateway_methods_exist(cdk_template):
    cdk_template.resource_count_is("AWS::ApiGateway::Method", 4)


def test_log_group_exists(cdk_template):
    cdk_template.resource_count_is("AWS::Logs::LogGroup", 1)
