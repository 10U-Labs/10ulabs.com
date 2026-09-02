from pathlib import Path
def test_iam_file_exists(health_src_dir: Path) -> None:
    assert (health_src_dir / "iam.tf").exists()


def test_iam_role_resource_exists(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role" "lambda_health_handler"' in content


def test_iam_role_uses_local_name(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert "name = local.lambda_role_name" in content


def test_iam_role_assume_role_policy_is_lambda(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert 'Service = "lambda.amazonaws.com"' in content


def test_iam_role_assume_action_is_sts(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert '"sts:AssumeRole"' in content


def test_iam_basic_execution_policy_attachment_resource(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_health_handler_basic"' in content


def test_iam_basic_execution_policy_arn(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert "AWSLambdaBasicExecutionRole" in content


def test_iam_kms_inline_policy_resource(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert 'resource "aws_iam_role_policy" "lambda_health_handler_kms"' in content


def test_iam_kms_inline_policy_name(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert 'name = "KMSDecryptPermissions"' in content


def test_iam_kms_policy_decrypt_action(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert '"kms:Decrypt"' in content


def test_iam_kms_policy_describe_key_action(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert '"kms:DescribeKey"' in content


def test_iam_kms_policy_references_common_module(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert "module.common.kms_lambda_key_arn" in content


def test_iam_role_has_tags(health_src_dir: Path) -> None:
    content = (health_src_dir / "iam.tf").read_text()
    assert "tags = merge(local.common_tags" in content
