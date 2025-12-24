"""Pre-deployment unit tests for api/shared/ecs_runner locals.tf configuration."""


def test_aws_region_references_shared_module(api_shared_ecs_runner_dir):
    """Test that aws_region references module.shared.aws_region."""
    content = (api_shared_ecs_runner_dir / "locals.tf").read_text()
    assert "aws_region = module.shared.aws_region" in content


def test_ecr_repository_name_defined(api_shared_ecs_runner_dir):
    """Test that ecr_repository_name is defined as 'runners'."""
    content = (api_shared_ecs_runner_dir / "locals.tf").read_text()
    assert 'ecr_repository_name = "runners"' in content


def test_common_tags_has_project_key(api_shared_ecs_runner_dir):
    """Test that common_tags includes Project key."""
    content = (api_shared_ecs_runner_dir / "locals.tf").read_text()
    assert "Project" in content


def test_common_tags_has_environment_key(api_shared_ecs_runner_dir):
    """Test that common_tags includes Environment key."""
    content = (api_shared_ecs_runner_dir / "locals.tf").read_text()
    assert "Environment" in content


def test_common_tags_has_managed_by_key(api_shared_ecs_runner_dir):
    """Test that common_tags includes ManagedBy key."""
    content = (api_shared_ecs_runner_dir / "locals.tf").read_text()
    assert "ManagedBy" in content


def test_common_tags_has_component_key(api_shared_ecs_runner_dir):
    """Test that common_tags includes Component key."""
    content = (api_shared_ecs_runner_dir / "locals.tf").read_text()
    assert "Component" in content
