"""Unit tests for iam.tf configuration."""


class TestIamConfiguration:
    """Tests for iam.tf Terraform configuration."""

    def test_iam_file_exists(self, retries_src_path):
        """Iam.tf file exists."""
        assert (retries_src_path / "iam.tf").exists()

    def test_lambda_role_resource_exists(self, retries_src_path):
        """Lambda IAM role resource is defined."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_iam_role" "lambda"' in content

    def test_lambda_role_has_assume_role_policy(self, retries_src_path):
        """Lambda role has assume_role_policy."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "assume_role_policy" in content

    def test_lambda_role_trusts_lambda_service(self, retries_src_path):
        """Lambda role trusts lambda.amazonaws.com."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "lambda.amazonaws.com" in content

    def test_basic_execution_role_attachment_exists(self, retries_src_path):
        """Basic execution role attachment exists."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_iam_role_policy_attachment" "lambda_basic"' in content

    def test_basic_execution_role_uses_aws_managed_policy(self, retries_src_path):
        """Basic execution role uses AWS managed policy."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "AWSLambdaBasicExecutionRole" in content

    def test_ssm_access_policy_exists(self, retries_src_path):
        """SSM access policy exists."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_iam_role_policy" "ssm_access"' in content

    def test_ssm_policy_allows_get_parameter(self, retries_src_path):
        """SSM policy allows GetParameter action."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "ssm:GetParameter" in content

    def test_ssm_policy_references_github_pat(self, retries_src_path):
        """SSM policy references GitHub PAT ARN from common module."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "module.common.ssm_github_pat_arn" in content

    def test_kms_access_policy_exists(self, retries_src_path):
        """KMS access policy exists."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_iam_role_policy" "kms_access"' in content

    def test_kms_policy_allows_decrypt(self, retries_src_path):
        """KMS policy allows Decrypt action."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "kms:Decrypt" in content

    def test_kms_policy_allows_describe_key(self, retries_src_path):
        """KMS policy allows DescribeKey action."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "kms:DescribeKey" in content

    def test_sqs_access_policy_exists(self, retries_src_path):
        """SQS access policy exists."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_iam_role_policy" "sqs_access"' in content

    def test_sqs_policy_allows_receive_message(self, retries_src_path):
        """SQS policy allows ReceiveMessage action."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "sqs:ReceiveMessage" in content

    def test_sqs_policy_allows_delete_message(self, retries_src_path):
        """SQS policy allows DeleteMessage action."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "sqs:DeleteMessage" in content

    def test_sqs_policy_allows_get_queue_attributes(self, retries_src_path):
        """SQS policy allows GetQueueAttributes action."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "sqs:GetQueueAttributes" in content

    def test_sqs_policy_references_main_queue(self, retries_src_path):
        """SQS policy references main queue ARN."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_sqs_queue.main.arn" in content

    def test_lambda_role_has_tags(self, retries_src_path):
        """Lambda role has tags."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "tags" in content

    def test_lambda_role_uses_common_tags(self, retries_src_path):
        """Lambda role uses common_tags from locals."""
        with open(retries_src_path / "iam.tf", encoding="utf-8") as f:
            content = f.read()
        assert "local.common_tags" in content
