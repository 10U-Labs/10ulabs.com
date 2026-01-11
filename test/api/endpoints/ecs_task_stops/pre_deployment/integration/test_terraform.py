"""Pre-deployment integration tests for ECS task stops Terraform config."""
from pathlib import Path

from test_utils.terraform_assertions import (
    get_missing_terraform_files,
    lambda_handler_exists,
)


def test_ecs_task_stops_terraform_files_exist(terraform_dir: Path):
    """All required ECS task stops Terraform files are present."""
    assert get_missing_terraform_files(terraform_dir) == []


def test_ecs_task_stops_lambda_handler_exists(terraform_dir: Path):
    """ECS task stops Lambda handler.py exists."""
    assert lambda_handler_exists(terraform_dir)


def test_ecs_task_stops_has_backend_config(terraform_dir: Path):
    """ECS task stops has backend.tf for remote state."""
    assert (terraform_dir / "backend.tf").is_file()


def test_ecs_task_stops_has_eventbridge_config(terraform_dir: Path):
    """ECS task stops has eventbridge.tf for event routing."""
    assert (terraform_dir / "eventbridge.tf").is_file()
