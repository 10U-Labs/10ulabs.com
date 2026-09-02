import re
from pathlib import Path


def test_locals_names_no_account_number(locals_tf_content: str) -> None:
    assert not re.search(r"\b\d{12}\b", locals_tf_content)


def test_locals_file_exists(module_path: Path) -> None:
    assert (module_path / "locals.tf").exists()


def test_outputs_file_exists(module_path: Path) -> None:
    assert (module_path / "outputs.tf").exists()


def test_aws_region_local_exists(locals_tf_content: str) -> None:
    assert "aws_region" in locals_tf_content


def test_aws_account_id_local_exists(locals_tf_content: str) -> None:
    assert "aws_account_id" in locals_tf_content


def test_resource_prefix_local_exists(locals_tf_content: str) -> None:
    assert "resource_prefix" in locals_tf_content


def test_ssm_github_pat_name_local_exists(locals_tf_content: str) -> None:
    assert "ssm_github_pat_name" in locals_tf_content


def test_github_app_local_exists(locals_tf_content: str) -> None:
    assert "github_app" in locals_tf_content


def test_lambda_handler_names_local_exists(locals_tf_content: str) -> None:
    assert "lambda_handler_names" in locals_tf_content


def test_admin_iam_user_output_exists(outputs_tf_content: str) -> None:
    assert 'output "admin_iam_user"' in outputs_tf_content


def test_aws_account_id_output_exists(outputs_tf_content: str) -> None:
    assert 'output "aws_account_id"' in outputs_tf_content


def test_aws_region_output_exists(outputs_tf_content: str) -> None:
    assert 'output "aws_region"' in outputs_tf_content


def test_domain_name_output_exists(outputs_tf_content: str) -> None:
    assert 'output "domain_name"' in outputs_tf_content


def test_github_org_output_exists(outputs_tf_content: str) -> None:
    assert 'output "github_org"' in outputs_tf_content


def test_name_for_central_logs_bucket_output_exists(outputs_tf_content: str) -> None:
    assert 'output "name_for_central_logs_bucket"' in outputs_tf_content


def test_name_for_github_repo_output_exists(outputs_tf_content: str) -> None:
    assert 'output "name_for_github_repo"' in outputs_tf_content


def test_name_for_terraform_state_bucket_output_exists(outputs_tf_content: str) -> None:
    assert 'output "name_for_terraform_state_bucket"' in outputs_tf_content


def test_resource_prefix_output_exists(outputs_tf_content: str) -> None:
    assert 'output "resource_prefix"' in outputs_tf_content


def test_lambda_handler_names_output_exists(outputs_tf_content: str) -> None:
    assert 'output "lambda_handler_names"' in outputs_tf_content


def test_ssm_github_pat_name_output_exists(outputs_tf_content: str) -> None:
    assert 'output "ssm_github_pat_name"' in outputs_tf_content


def test_github_app_output_exists(outputs_tf_content: str) -> None:
    assert 'output "github_app"' in outputs_tf_content


def test_kms_lambda_key_arn_output_exists(outputs_tf_content: str) -> None:
    assert 'output "kms_lambda_key_arn"' in outputs_tf_content
