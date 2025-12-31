"""Pre-deployment unit tests for api/common/docker_repository shared.tf configuration."""


def test_shared_module_source_path(api_common_docker_repository_dir):
    """Test that shared module references the correct source path."""
    content = (api_common_docker_repository_dir / "shared.tf").read_text()
    assert 'source = "../../../../lib/terraform/common"' in content
