from pathlib import Path


def test_terraform_files_exist():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    assert (gmail_dir / "main.tf").exists()


def test_backend_configuration_exists():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    assert (gmail_dir / "backend.tf").exists()


def test_providers_configuration_exists():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    assert (gmail_dir / "providers.tf").exists()


def test_variables_configuration_exists():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    assert (gmail_dir / "variables.tf").exists()


def test_outputs_configuration_exists():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    assert (gmail_dir / "outputs.tf").exists()


def test_data_configuration_exists():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    assert (gmail_dir / "data.tf").exists()


def test_tfvars_file_exists():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    assert (gmail_dir / "terraform.tfvars").exists()


def test_config_file_exists(gmail_config_path):
    assert gmail_config_path.exists()


def test_config_has_domain_name(config):
    assert "domain_name" in config


def test_config_has_google_site_verification(config):
    assert "google_site_verification" in config


def test_config_has_aws_account_id(config):
    assert "aws" in config and "account_id" in config["aws"]


def test_config_has_aws_region(config):
    assert "aws" in config and "region" in config["aws"]


def test_terraform_has_google_verification_output():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    outputs_file = gmail_dir / "outputs.tf"

    with open(outputs_file) as f:
        content = f.read()

    assert "google_verification_record" in content


def test_terraform_has_google_verification_value_output():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    outputs_file = gmail_dir / "outputs.tf"

    with open(outputs_file) as f:
        content = f.read()

    assert "google_verification_value" in content


def test_terraform_has_gmail_mx_output():
    gmail_dir = Path(__file__).parent.parent.parent / "src" / "gmail"
    outputs_file = gmail_dir / "outputs.tf"

    with open(outputs_file) as f:
        content = f.read()

    assert "gmail_mx_record" in content
