def test_contact_form_terraform_file_exists(website_src_path):
    assert (website_src_path / "contact_form.tf").exists()


def test_ses_email_identity_exists(contact_form_tf_content):
    assert 'resource "aws_ses_email_identity" "contact"' in contact_form_tf_content


def test_ses_email_identity_uses_domain(contact_form_tf_content):
    assert 'local.domain_name' in contact_form_tf_content


def test_archive_file_contact_handler_exists(contact_form_tf_content):
    assert 'data "archive_file" "contact_handler"' in contact_form_tf_content


def test_iam_role_contact_lambda_exists(contact_form_tf_content):
    assert 'resource "aws_iam_role" "contact_lambda"' in contact_form_tf_content


def test_iam_role_attachment_basic_execution_exists(contact_form_tf_content):
    assert 'resource "aws_iam_role_policy_attachment" "contact_lambda_basic"' in contact_form_tf_content


def test_iam_role_policy_ses_exists(contact_form_tf_content):
    assert 'resource "aws_iam_role_policy" "contact_lambda_ses"' in contact_form_tf_content


def test_iam_role_policy_ses_allows_send_email(contact_form_tf_content):
    assert 'ses:SendEmail' in contact_form_tf_content


def test_cloudwatch_log_group_contact_handler_exists(contact_form_tf_content):
    assert 'resource "aws_cloudwatch_log_group" "contact_handler"' in contact_form_tf_content


def test_cloudwatch_log_group_retention_7_days(contact_form_tf_content):
    assert 'retention_in_days = 7' in contact_form_tf_content


def test_lambda_function_contact_handler_exists(contact_form_tf_content):
    assert 'resource "aws_lambda_function" "contact_handler"' in contact_form_tf_content


def test_lambda_function_uses_python313(contact_form_tf_content):
    assert 'runtime          = "python3.13"' in contact_form_tf_content


def test_lambda_function_has_contact_email_env_var(contact_form_tf_content):
    assert 'CONTACT_EMAIL' in contact_form_tf_content


def test_lambda_function_url_exists(contact_form_tf_content):
    assert 'resource "aws_lambda_function_url" "contact_handler"' in contact_form_tf_content


def test_lambda_function_url_has_no_auth(contact_form_tf_content):
    assert 'authorization_type = "NONE"' in contact_form_tf_content


def test_lambda_function_url_has_cors_config(contact_form_tf_content):
    assert 'cors {' in contact_form_tf_content


def test_lambda_function_url_allows_post_method(contact_form_tf_content):
    assert 'POST' in contact_form_tf_content


def test_lambda_handler_file_exists(website_src_path):
    assert (website_src_path / "lambdas" / "contact.py").exists()
