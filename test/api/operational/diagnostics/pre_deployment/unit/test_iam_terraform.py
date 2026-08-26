def test_iam_file_exists(diagnostics_src_dir):
    assert (diagnostics_src_dir / "iam.tf").exists()


def test_iam_role_resource_exists(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role" "lambda_diagnostics_handler"' in content


def test_iam_role_uses_local_name(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "name = local.diagnostics_handler_role_name" in content


def test_iam_role_assume_role_policy_is_lambda(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert 'Service = "lambda.amazonaws.com"' in content


def test_iam_role_assume_action_is_sts(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert '"sts:AssumeRole"' in content


def test_iam_basic_execution_policy_attachment_resource(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_diagnostics_handler_basic"' in content


def test_iam_basic_execution_policy_arn(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "AWSLambdaBasicExecutionRole" in content


def test_iam_role_has_tags(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "tags = merge(local.common_tags" in content


def test_iam_role_uses_jsonencode(diagnostics_src_dir):
    content = (diagnostics_src_dir / "iam.tf").read_text()
    assert "assume_role_policy = jsonencode" in content
