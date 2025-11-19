def test_config_file_exists_in_correct_location(config_path):
    assert config_path.exists()


def test_config_has_aws_account_id(config):
    assert "account_id" in config["aws"]


def test_config_has_aws_region(config):
    assert "region" in config["aws"]


def test_config_has_lambda_function_name(config):
    assert "lambda_function_name" in config["naming"]


def test_config_has_lambda_timeout(config):
    assert "timeout_seconds" in config["lambda"]


def test_config_has_lambda_memory(config):
    assert "memory_mb" in config["lambda"]


def test_config_has_packer_builder_ami_id(config):
    assert "builder_ami_id" in config["packer"]


def test_config_has_packer_instance_types(config):
    assert "instance_types" in config["packer"]


def test_config_has_packer_iam_instance_profile(config):
    assert "iam_instance_profile" in config["packer"]


def test_config_has_packer_config_bucket(config):
    assert "config_bucket" in config["packer"]


def test_handler_file_exists(handler_path):
    assert handler_path.exists()


def test_stack_file_exists(stack_path):
    assert stack_path.exists()


def test_handler_has_get_latest_ami_function(handler_module):
    assert hasattr(handler_module, 'get_latest_ami')


def test_handler_has_list_amis_function(handler_module):
    assert hasattr(handler_module, 'list_amis')


def test_handler_has_deregister_ami_function(handler_module):
    assert hasattr(handler_module, 'deregister_ami')


def test_handler_has_launch_packer_builder_function(handler_module):
    assert hasattr(handler_module, 'launch_packer_builder')


def test_handler_has_lambda_handler_function(handler_module):
    assert hasattr(handler_module, 'lambda_handler')


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
