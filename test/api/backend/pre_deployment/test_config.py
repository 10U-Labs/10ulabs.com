from pathlib import Path


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "terraform.tfvars"
    file_exists = config_path.exists()
    assert file_exists


def test_config_has_aws_account_id(config):
    has_aws_account_id = "aws_account_id" in config
    assert has_aws_account_id


def test_config_has_aws_region(config):
    has_aws_region = "aws_region" in config
    assert has_aws_region


def test_shared_module_has_github_org():
    outputs_path = Path(__file__).parent.parent.parent.parent.parent / "lib" / "terraform" / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    has_github_org = 'github_org' in content
    assert has_github_org


def test_shared_module_has_github_repo():
    outputs_path = Path(__file__).parent.parent.parent.parent.parent / "lib" / "terraform" / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    has_github_repo = 'name_for_github_repo' in content
    assert has_github_repo


def test_locals_tf_has_api_fqdn():
    locals_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()
    has_api_fqdn = 'api_fqdn' in content
    assert has_api_fqdn


def test_cloudfront_health_endpoint_path_pattern_exists():
    cloudfront_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "cloudfront_s3.tf"
    with open(cloudfront_file, encoding="utf-8") as f:
        content = f.read()
    has_health_path_pattern = 'path_pattern           = "/health"' in content
    assert has_health_path_pattern


def test_cloudfront_health_endpoint_allows_options():
    cloudfront_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "cloudfront_s3.tf"
    with open(cloudfront_file, encoding="utf-8") as f:
        content = f.read()
    health_section_start = content.find('path_pattern           = "/health"')
    health_section = content[health_section_start:health_section_start + 500]
    allows_options = 'OPTIONS' in health_section
    assert allows_options
