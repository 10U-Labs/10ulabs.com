"""Unit tests for diagnostics endpoint iam.tf configuration."""


def test_iam_file_exists(diagnostics_src_dir):
    """Verify iam.tf file exists."""
    assert (diagnostics_src_dir / "iam.tf").exists()


def test_iam_role_resource_exists(diagnostics_src_dir):
    """Verify IAM role resource is defined."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role" "lambda_diagnostics_handler"' in content


def test_iam_role_uses_local_name(diagnostics_src_dir):
    """Verify IAM role name references local.diagnostics_handler_role_name."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "name = local.diagnostics_handler_role_name" in content


def test_iam_role_assume_role_policy_is_lambda(diagnostics_src_dir):
    """Verify IAM role trust policy allows Lambda service."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert 'Service = "lambda.amazonaws.com"' in content


def test_iam_role_assume_action_is_sts(diagnostics_src_dir):
    """Verify IAM role trust policy uses sts:AssumeRole action."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert '"sts:AssumeRole"' in content


def test_iam_basic_execution_policy_attachment_resource(diagnostics_src_dir):
    """Verify basic execution policy attachment resource exists."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_diagnostics_handler_basic"' in content


def test_iam_basic_execution_policy_arn(diagnostics_src_dir):
    """Verify AWSLambdaBasicExecutionRole policy is attached."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "AWSLambdaBasicExecutionRole" in content


def test_iam_role_has_tags(diagnostics_src_dir):
    """Verify IAM role has tags configured."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "tags = merge(local.common_tags" in content


def test_iam_role_uses_jsonencode(diagnostics_src_dir):
    """Verify IAM role policy uses jsonencode."""
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "assume_role_policy = jsonencode" in content
