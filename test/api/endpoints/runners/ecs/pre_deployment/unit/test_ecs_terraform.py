"""Unit tests for ECS runner ecs.tf configuration."""


def test_ecs_file_exists(ecs_runner_src_dir):
    """Verify ecs.tf file exists."""
    assert (ecs_runner_src_dir / "ecs.tf").exists()


def test_ecs_cluster_resource_exists(ecs_runner_src_dir):
    """Verify ECS cluster resource is defined."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'resource "aws_ecs_cluster" "runner"' in content


def test_ecs_cluster_has_name_variable(ecs_runner_src_dir):
    """Verify ECS cluster uses variable for name."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "name = var.cluster_name" in content


def test_ecs_cluster_has_container_insights_enabled(ecs_runner_src_dir):
    """Verify ECS cluster has Container Insights enabled."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'name  = "containerInsights"' in content


def test_ecs_cluster_container_insights_value_enabled(ecs_runner_src_dir):
    """Verify Container Insights value is enabled."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'value = "enabled"' in content


def test_ecs_capacity_providers_resource_exists(ecs_runner_src_dir):
    """Verify ECS cluster capacity providers resource is defined."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'resource "aws_ecs_cluster_capacity_providers" "runner"' in content


def test_ecs_capacity_providers_has_fargate(ecs_runner_src_dir):
    """Verify FARGATE capacity provider is included."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert '"FARGATE"' in content


def test_ecs_capacity_providers_has_fargate_spot(ecs_runner_src_dir):
    """Verify FARGATE_SPOT capacity provider is included."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert '"FARGATE_SPOT"' in content


def test_ecs_capacity_providers_default_strategy_uses_spot(ecs_runner_src_dir):
    """Verify default capacity provider strategy uses FARGATE_SPOT."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'capacity_provider = "FARGATE_SPOT"' in content


def test_ecs_task_definition_resource_exists(ecs_runner_src_dir):
    """Verify ECS task definition resource is defined."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'resource "aws_ecs_task_definition" "runner"' in content


def test_ecs_task_definition_family_uses_variable(ecs_runner_src_dir):
    """Verify task definition family uses variable."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "family                   = var.task_family" in content


def test_ecs_task_definition_network_mode_awsvpc(ecs_runner_src_dir):
    """Verify task definition uses awsvpc network mode."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'network_mode             = "awsvpc"' in content


def test_ecs_task_definition_requires_fargate(ecs_runner_src_dir):
    """Verify task definition requires FARGATE compatibility."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'requires_compatibilities = ["FARGATE"]' in content


def test_ecs_task_definition_has_task_role(ecs_runner_src_dir):
    """Verify task definition references task role."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "task_role_arn            = aws_iam_role.ecs_task_role.arn" in content


def test_ecs_task_definition_has_execution_role(ecs_runner_src_dir):
    """Verify task definition references execution role."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "execution_role_arn       = aws_iam_role.ecs_execution_role.arn" in content


def test_ecs_task_definition_has_ephemeral_storage(ecs_runner_src_dir):
    """Verify task definition has ephemeral storage configured."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "ephemeral_storage {" in content


def test_ecs_task_definition_ephemeral_storage_size(ecs_runner_src_dir):
    """Verify ephemeral storage is 128 GiB."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "size_in_gib = 128" in content


def test_ecs_task_definition_has_runtime_platform(ecs_runner_src_dir):
    """Verify task definition has runtime platform block."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "runtime_platform {" in content


def test_ecs_task_definition_cpu_architecture_variable(ecs_runner_src_dir):
    """Verify CPU architecture uses variable."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "cpu_architecture        = var.fargate_cpu_architecture" in content


def test_ecs_task_definition_operating_system_variable(ecs_runner_src_dir):
    """Verify operating system family uses variable."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "operating_system_family = var.fargate_operating_system_family" in content


def test_ecs_task_definition_has_volume(ecs_runner_src_dir):
    """Verify task definition has volume configuration."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'name = "runner-diag"' in content


def test_ecs_task_definition_has_container_definitions(ecs_runner_src_dir):
    """Verify task definition has container definitions."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "container_definitions = jsonencode([" in content


def test_ecs_task_definition_uses_awslogs_driver(ecs_runner_src_dir):
    """Verify task definition uses awslogs log driver."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'logDriver = "awslogs"' in content


def test_ecs_cloudwatch_log_group_exists(ecs_runner_src_dir):
    """Verify CloudWatch log group resource for ECS is defined."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert 'resource "aws_cloudwatch_log_group" "ecs_runner"' in content


def test_ecs_cloudwatch_log_group_retention_7_days(ecs_runner_src_dir):
    """Verify ECS log group has 7 day retention."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "retention_in_days = 7" in content


def test_ecs_cloudwatch_log_group_name_pattern(ecs_runner_src_dir):
    """Verify ECS log group uses /ecs/ prefix in name."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert '"/ecs/${var.task_family}"' in content


def test_ecs_task_definition_has_cloudwatch_agent_container(ecs_runner_src_dir):
    """Verify task definition includes CloudWatch agent container."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert '"cloudwatch-agent"' in content


def test_ecs_cloudwatch_agent_not_essential(ecs_runner_src_dir):
    """Verify CloudWatch agent container is not essential."""
    content = (ecs_runner_src_dir / "ecs.tf").read_text()
    assert "essential = false" in content
