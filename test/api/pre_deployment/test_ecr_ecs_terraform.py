from pathlib import Path


def test_ecr_ecs_terraform_file_exists():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    assert ecr_ecs_file.exists()


def test_ecr_repository_resource_exists():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_ecr_repository" "runner"' in content


def test_ecr_repository_has_image_scanning_enabled():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'scan_on_push = true' in content


def test_ecr_repository_has_encryption_configuration():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'encryption_configuration' in content


def test_ecr_lifecycle_policy_exists():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_ecr_lifecycle_policy" "runner"' in content


def test_ecs_cluster_resource_exists():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_ecs_cluster" "runner"' in content


def test_ecs_cluster_has_container_insights_enabled():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'containerInsights' in content


def test_ecs_cluster_capacity_providers_resource_exists():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_ecs_cluster_capacity_providers" "runner"' in content


def test_ecs_cluster_uses_fargate_spot_capacity_provider():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'capacity_providers = ["FARGATE_SPOT"]' in content


def test_ecs_task_definition_resource_exists():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_ecs_task_definition" "runner"' in content


def test_ecs_task_definition_has_network_mode_awsvpc():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'network_mode             = "awsvpc"' in content


def test_ecs_task_definition_requires_fargate():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'requires_compatibilities = ["FARGATE"]' in content


def test_ecs_task_definition_has_runtime_platform_block():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'runtime_platform {' in content


def test_ecs_task_definition_runtime_platform_has_cpu_architecture():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cpu_architecture        = var.fargate_cpu_architecture' in content


def test_ecs_task_definition_runtime_platform_has_operating_system_family():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'operating_system_family = var.fargate_operating_system_family' in content


def test_ecs_task_definition_has_task_role_arn():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'task_role_arn            = aws_iam_role.ecs_task_role.arn' in content


def test_ecs_task_definition_has_execution_role_arn():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'execution_role_arn       = aws_iam_role.ecs_execution_role.arn' in content


def test_ecs_task_definition_has_log_configuration():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'logConfiguration' in content


def test_cloudwatch_log_group_resource_exists():
    ecr_ecs_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "ecr_ecs.tf"
    with open(ecr_ecs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "runner"' in content


def test_terraform_tfvars_has_fargate_cpu_architecture():
    tfvars_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_file, encoding="utf-8") as f:
        content = f.read()
    assert 'fargate_cpu_architecture' in content


def test_terraform_tfvars_fargate_cpu_architecture_is_arm64():
    tfvars_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_file, encoding="utf-8") as f:
        content = f.read()
    assert 'fargate_cpu_architecture        = "ARM64"' in content


def test_terraform_tfvars_has_fargate_operating_system_family():
    tfvars_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_file, encoding="utf-8") as f:
        content = f.read()
    assert 'fargate_operating_system_family' in content


def test_terraform_tfvars_fargate_operating_system_family_is_linux():
    tfvars_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "terraform.tfvars"
    with open(tfvars_file, encoding="utf-8") as f:
        content = f.read()
    assert 'fargate_operating_system_family = "LINUX"' in content


def test_variables_tf_has_fargate_cpu_architecture():
    variables_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "variables.tf"
    with open(variables_file, encoding="utf-8") as f:
        content = f.read()
    assert 'variable "fargate_cpu_architecture"' in content


def test_variables_tf_has_fargate_operating_system_family():
    variables_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "variables.tf"
    with open(variables_file, encoding="utf-8") as f:
        content = f.read()
    assert 'variable "fargate_operating_system_family"' in content


def test_variables_tf_fargate_cpu_architecture_has_no_default():
    variables_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "variables.tf"
    with open(variables_file, encoding="utf-8") as f:
        lines = f.readlines()
    in_cpu_arch_block = False
    for line in lines:
        if 'variable "fargate_cpu_architecture"' in line:
            in_cpu_arch_block = True
        if in_cpu_arch_block and line.strip().startswith('}'):
            break
        if in_cpu_arch_block:
            assert 'default' not in line


def test_variables_tf_fargate_operating_system_family_has_no_default():
    variables_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "variables.tf"
    with open(variables_file, encoding="utf-8") as f:
        lines = f.readlines()
    in_os_family_block = False
    for line in lines:
        if 'variable "fargate_operating_system_family"' in line:
            in_os_family_block = True
        if in_os_family_block and line.strip().startswith('}'):
            break
        if in_os_family_block:
            assert 'default' not in line
