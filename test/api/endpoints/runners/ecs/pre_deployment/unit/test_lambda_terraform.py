"""Unit tests for ECS runner lambda.tf configuration."""


def test_lambda_file_exists(ecs_runner_src_dir):
    """Verify lambda.tf file exists."""
    assert (ecs_runner_src_dir / "lambda.tf").exists()


def test_lambda_function_resource_exists(ecs_runner_src_dir):
    """Verify Lambda function resource is defined."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_lambda_function" "handler"' in content


def test_lambda_function_uses_local_name(ecs_runner_src_dir):
    """Verify Lambda function name uses local."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "function_name    = local.lambda_function_name" in content


def test_lambda_function_uses_local_handler(ecs_runner_src_dir):
    """Verify Lambda function handler uses local."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "handler          = local.lambda_handler" in content


def test_lambda_function_references_iam_role(ecs_runner_src_dir):
    """Verify Lambda function references IAM role."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "role             = aws_iam_role.lambda_execution.arn" in content


def test_lambda_function_uses_local_runtime(ecs_runner_src_dir):
    """Verify Lambda function runtime uses local."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "runtime          = local.lambda_runtime" in content


def test_lambda_function_architecture_is_arm64(ecs_runner_src_dir):
    """Verify Lambda function uses ARM64 architecture."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert 'architectures    = ["arm64"]' in content


def test_lambda_function_has_timeout(ecs_runner_src_dir):
    """Verify Lambda function has timeout configured."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "timeout          = local.lambda_timeout" in content


def test_lambda_function_has_memory_size(ecs_runner_src_dir):
    """Verify Lambda function has memory size configured."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "memory_size      = local.lambda_memory_size" in content


def test_lambda_function_has_environment_block(ecs_runner_src_dir):
    """Verify Lambda function has environment block."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "environment {" in content


def test_lambda_function_env_container_name(ecs_runner_src_dir):
    """Verify Lambda function has CONTAINER_NAME env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "CONTAINER_NAME           = var.container_name" in content


def test_lambda_function_env_ecr_repository(ecs_runner_src_dir):
    """Verify Lambda function has ECR_REPOSITORY env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "ECR_REPOSITORY" in content


def test_lambda_function_env_ecs_cluster(ecs_runner_src_dir):
    """Verify Lambda function has ECS_CLUSTER env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "ECS_CLUSTER              = aws_ecs_cluster.runner.name" in content


def test_lambda_function_env_github_token_secret(ecs_runner_src_dir):
    """Verify Lambda function has GITHUB_TOKEN_SECRET_NAME env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "GITHUB_TOKEN_SECRET_NAME" in content


def test_lambda_function_env_api_fqdn(ecs_runner_src_dir):
    """Verify Lambda function has API_FQDN env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "API_FQDN" in content


def test_lambda_function_env_security_groups(ecs_runner_src_dir):
    """Verify Lambda function has SECURITY_GROUPS env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "SECURITY_GROUPS" in content


def test_lambda_function_env_subnets(ecs_runner_src_dir):
    """Verify Lambda function has SUBNETS env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "SUBNETS" in content


def test_lambda_function_env_task_definition(ecs_runner_src_dir):
    """Verify Lambda function has TASK_DEFINITION env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "TASK_DEFINITION          = aws_ecs_task_definition.runner.arn" in content


def test_lambda_function_env_use_spot(ecs_runner_src_dir):
    """Verify Lambda function has USE_SPOT env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "USE_SPOT" in content


def test_lambda_function_env_vpc_id(ecs_runner_src_dir):
    """Verify Lambda function has VPC_ID env var."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "VPC_ID" in content


def test_lambda_function_depends_on_log_group(ecs_runner_src_dir):
    """Verify Lambda function depends on CloudWatch log group."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "aws_cloudwatch_log_group.lambda" in content


def test_lambda_function_has_lifecycle_block(ecs_runner_src_dir):
    """Verify Lambda function has lifecycle block."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "lifecycle {" in content


def test_lambda_cloudwatch_log_group_exists(ecs_runner_src_dir):
    """Verify CloudWatch log group resource for Lambda is defined."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_cloudwatch_log_group" "lambda"' in content


def test_lambda_cloudwatch_log_group_retention_14_days(ecs_runner_src_dir):
    """Verify Lambda log group has 14 day retention."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert "retention_in_days = 14" in content


def test_lambda_permission_resource_exists(ecs_runner_src_dir):
    """Verify Lambda permission resource is defined."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_lambda_permission" "api_gateway"' in content


def test_lambda_permission_principal_is_api_gateway(ecs_runner_src_dir):
    """Verify Lambda permission principal is API Gateway."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert 'principal     = "apigateway.amazonaws.com"' in content


def test_lambda_permission_statement_id(ecs_runner_src_dir):
    """Verify Lambda permission has correct statement ID."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert 'statement_id  = "AllowAPIGatewayInvoke"' in content


def test_lambda_permission_action(ecs_runner_src_dir):
    """Verify Lambda permission uses correct action."""
    content = (ecs_runner_src_dir / "lambda.tf").read_text()
    assert 'action        = "lambda:InvokeFunction"' in content
