from pathlib import Path


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    assert config_path.exists()


def test_config_has_aws_account_id(cfg):
    assert "account_id" in cfg["aws"]


def test_config_has_aws_region(cfg):
    assert "region" in cfg["aws"]


def test_config_has_vpc_name(cfg):
    assert "vpc_name" in cfg["naming"]


def test_config_has_github_runner_version(cfg):
    assert "runner_version" in cfg["github"]


def test_terraform_tfvars_has_github_repo():
    tfvars_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_path, encoding="utf-8") as f:
        content = f.read()
    assert 'github_repo' in content


def test_terraform_tfvars_github_repo_format():
    tfvars_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith('github_repo'):
                value = line.split('=')[1].strip().strip('"')
                assert '/' in value


def test_terraform_tfvars_has_domain_subdomain():
    tfvars_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_path, encoding="utf-8") as f:
        content = f.read()
    assert 'domain_subdomain' in content


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
