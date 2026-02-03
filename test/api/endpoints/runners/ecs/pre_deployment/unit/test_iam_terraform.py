"""Unit tests for ECS runner iam.tf configuration."""


def test_iam_file_exists(ecs_runner_src_dir):
    """Verify iam.tf file exists."""
    assert (ecs_runner_src_dir / "iam.tf").exists()


def test_iam_lambda_execution_role_exists(ecs_runner_src_dir):
    """Verify Lambda execution IAM role resource is defined."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role" "lambda_execution"' in content


def test_iam_lambda_role_uses_local_name(ecs_runner_src_dir):
    """Verify IAM role name references local."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert "name = local.lambda_execution_role_name" in content


def test_iam_lambda_role_assume_policy_is_lambda(ecs_runner_src_dir):
    """Verify Lambda IAM role trust policy allows Lambda service."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert 'Service = "lambda.amazonaws.com"' in content


def test_iam_lambda_role_assume_action_is_sts(ecs_runner_src_dir):
    """Verify Lambda IAM role trust policy uses sts:AssumeRole action."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"sts:AssumeRole"' in content


def test_iam_lambda_policy_resource_exists(ecs_runner_src_dir):
    """Verify Lambda execution policy resource is defined."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role_policy" "lambda_execution"' in content


def test_iam_lambda_policy_allows_cloudwatch_logs(ecs_runner_src_dir):
    """Verify Lambda policy allows CloudWatch Logs actions."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"logs:CreateLogGroup"' in content


def test_iam_lambda_policy_allows_create_log_stream(ecs_runner_src_dir):
    """Verify Lambda policy allows logs:CreateLogStream."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"logs:CreateLogStream"' in content


def test_iam_lambda_policy_allows_put_log_events(ecs_runner_src_dir):
    """Verify Lambda policy allows logs:PutLogEvents."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"logs:PutLogEvents"' in content


def test_iam_lambda_policy_allows_ecs_run_task(ecs_runner_src_dir):
    """Verify Lambda policy allows ecs:RunTask."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"ecs:RunTask"' in content


def test_iam_lambda_policy_allows_ecs_describe_tasks(ecs_runner_src_dir):
    """Verify Lambda policy allows ecs:DescribeTasks."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"ecs:DescribeTasks"' in content


def test_iam_lambda_policy_allows_ecs_list_tasks(ecs_runner_src_dir):
    """Verify Lambda policy allows ecs:ListTasks."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"ecs:ListTasks"' in content


def test_iam_lambda_policy_allows_ecs_stop_task(ecs_runner_src_dir):
    """Verify Lambda policy allows ecs:StopTask."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"ecs:StopTask"' in content


def test_iam_lambda_policy_allows_ecs_tag_resource(ecs_runner_src_dir):
    """Verify Lambda policy allows ecs:TagResource."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"ecs:TagResource"' in content


def test_iam_lambda_policy_allows_ecr_describe_images(ecs_runner_src_dir):
    """Verify Lambda policy allows ecr:DescribeImages."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"ecr:DescribeImages"' in content


def test_iam_lambda_policy_allows_ssm_get_parameter(ecs_runner_src_dir):
    """Verify Lambda policy allows ssm:GetParameter."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"ssm:GetParameter"' in content


def test_iam_lambda_policy_allows_iam_pass_role(ecs_runner_src_dir):
    """Verify Lambda policy allows iam:PassRole."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert '"iam:PassRole"' in content


def test_iam_lambda_policy_has_ecs_cluster_condition(ecs_runner_src_dir):
    """Verify Lambda policy has ECS cluster condition."""
    content = (ecs_runner_src_dir / "iam.tf").read_text()
    assert 'ecs:cluster' in content
