from pathlib import Path


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    assert config_path.exists()


def test_config_has_aws_account_id(config):
    assert "aws_account_id" in config


def test_config_has_aws_region(config):
    assert "aws_region" in config


def test_config_has_vpc_name(config):
    assert "vpc_name" in config


def test_shared_module_has_github_org():
    outputs_path = Path(__file__).parent.parent.parent.parent / "src" / "modules" / "shared" / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    assert 'github_org' in content


def test_shared_module_has_github_repo():
    outputs_path = Path(__file__).parent.parent.parent.parent / "src" / "modules" / "shared" / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    assert 'name_for_github_repo' in content


def test_locals_tf_has_api_fqdn():
    locals_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()
    assert 'api_fqdn' in content


def test_github_webhook_resource_exists():
    webhook_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "github_webhook.tf"
    assert webhook_file.exists()


def test_github_webhook_resource_has_workflow_job_event():
    webhook_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "github_webhook.tf"
    with open(webhook_file, encoding="utf-8") as f:
        content = f.read()
    assert 'workflow_job' in content


def test_github_webhook_resource_uses_runners_endpoint():
    webhook_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "github_webhook.tf"
    with open(webhook_file, encoding="utf-8") as f:
        content = f.read()
    assert '/v1/runners' in content


def test_webhook_secret_uses_random_password():
    webhook_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "github_webhook.tf"
    with open(webhook_file, encoding="utf-8") as f:
        content = f.read()
    assert 'random_password.webhook_secret' in content


def test_ssm_parameter_webhook_secret_uses_random_password():
    ssm_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ssm.tf"
    with open(ssm_file, encoding="utf-8") as f:
        content = f.read()
    assert 'random_password.webhook_secret.result' in content


def test_lambda_uses_bootstrap_github_token_parameter():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'GITHUB_TOKEN_SECRET_NAME        = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat' in content


def test_cloudfront_health_endpoint_path_pattern_exists():
    cloudfront_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cloudfront_file, encoding="utf-8") as f:
        content = f.read()
    assert 'path_pattern           = "/health"' in content


def test_cloudfront_health_endpoint_allows_options():
    cloudfront_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cloudfront_file, encoding="utf-8") as f:
        content = f.read()
    health_section_start = content.find('path_pattern           = "/health"')
    health_section = content[health_section_start:health_section_start + 500]
    assert 'OPTIONS' in health_section
