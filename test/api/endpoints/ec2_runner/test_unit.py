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


def test_config_has_ec2_ami_id(config):
    assert "ami_id" in config["ec2"]


def test_config_has_ec2_instance_types(config):
    assert "instance_types" in config["ec2"]


def test_config_has_ec2_max_price(config):
    assert "max_price" in config["ec2"]


def test_handler_file_exists(handler_path):
    assert handler_path.exists()


def test_stack_file_exists(stack_path):
    assert stack_path.exists()


def test_handler_has_get_latest_ami_function(handler_module):
    assert hasattr(handler_module, 'get_latest_ami')


def test_handler_has_get_github_token_function(handler_module):
    assert hasattr(handler_module, 'get_github_token')


def test_handler_has_launch_ec2_spot_runner_function(handler_module):
    assert hasattr(handler_module, 'launch_ec2_spot_runner')


def test_handler_has_lambda_handler_function(handler_module):
    assert hasattr(handler_module, 'lambda_handler')
