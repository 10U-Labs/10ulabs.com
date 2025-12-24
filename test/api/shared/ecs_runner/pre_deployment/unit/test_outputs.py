"""Pre-deployment unit tests for api/shared/ecs_runner outputs.tf configuration."""
import re


def test_ecr_repository_arn_output_exists(api_shared_ecs_runner_dir):
    """Test that ecr_repository_arn output is defined."""
    content = (api_shared_ecs_runner_dir / "outputs.tf").read_text()
    pattern = r'output\s+"ecr_repository_arn"'
    assert re.search(pattern, content) is not None


def test_ecr_repository_arn_references_runners(api_shared_ecs_runner_dir):
    """Test that ecr_repository_arn references aws_ecr_repository.runners.arn."""
    content = (api_shared_ecs_runner_dir / "outputs.tf").read_text()
    assert "aws_ecr_repository.runners.arn" in content


def test_ecr_repository_name_output_exists(api_shared_ecs_runner_dir):
    """Test that ecr_repository_name output is defined."""
    content = (api_shared_ecs_runner_dir / "outputs.tf").read_text()
    pattern = r'output\s+"ecr_repository_name"'
    assert re.search(pattern, content) is not None


def test_ecr_repository_name_references_runners(api_shared_ecs_runner_dir):
    """Test that ecr_repository_name references aws_ecr_repository.runners.name."""
    content = (api_shared_ecs_runner_dir / "outputs.tf").read_text()
    assert "aws_ecr_repository.runners.name" in content


def test_ecr_repository_url_output_exists(api_shared_ecs_runner_dir):
    """Test that ecr_repository_url output is defined."""
    content = (api_shared_ecs_runner_dir / "outputs.tf").read_text()
    pattern = r'output\s+"ecr_repository_url"'
    assert re.search(pattern, content) is not None


def test_ecr_repository_url_references_runners(api_shared_ecs_runner_dir):
    """Test that ecr_repository_url references aws_ecr_repository.runners.repository_url."""
    content = (api_shared_ecs_runner_dir / "outputs.tf").read_text()
    assert "aws_ecr_repository.runners.repository_url" in content
