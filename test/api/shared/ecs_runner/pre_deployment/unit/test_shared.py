"""Pre-deployment unit tests for api/shared/ecs_runner shared.tf configuration."""


def test_shared_module_source_path(api_shared_ecs_runner_dir):
    """Test that shared module references the correct source path."""
    content = (api_shared_ecs_runner_dir / "shared.tf").read_text()
    assert 'source = "../../../../lib/terraform/modules/shared"' in content
