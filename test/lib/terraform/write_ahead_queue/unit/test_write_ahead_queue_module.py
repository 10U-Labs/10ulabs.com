"""Tests for write_ahead_queue Terraform module."""


def test_module_files_exist(module_path):
    """Test that required module files exist."""
    assert (module_path / "main.tf").exists()


def test_module_variables_file_exists(module_path):
    """Test that variables file exists."""
    assert (module_path / "variables.tf").exists()


def test_module_outputs_file_exists(module_path):
    """Test that outputs file exists."""
    assert (module_path / "outputs.tf").exists()


def test_main_queue_resource_exists(main_tf_content):
    """Test that main SQS queue resource exists."""
    assert 'resource "aws_sqs_queue" "main"' in main_tf_content


def test_dlq_resource_exists(main_tf_content):
    """Test that DLQ SQS queue resource exists."""
    assert 'resource "aws_sqs_queue" "dlq"' in main_tf_content


def test_main_queue_uses_queue_name_variable(main_tf_content):
    """Test that main queue uses queue_name variable."""
    assert "var.queue_name" in main_tf_content


def test_main_queue_has_visibility_timeout(main_tf_content):
    """Test that main queue has visibility timeout configured."""
    assert "visibility_timeout_seconds" in main_tf_content


def test_main_queue_has_message_retention(main_tf_content):
    """Test that main queue has message retention configured."""
    assert "message_retention_seconds" in main_tf_content


def test_main_queue_has_redrive_policy(main_tf_content):
    """Test that main queue has redrive policy for DLQ."""
    assert "redrive_policy" in main_tf_content


def test_redrive_policy_references_dlq(main_tf_content):
    """Test that redrive policy references the DLQ."""
    assert "aws_sqs_queue.dlq.arn" in main_tf_content


def test_redrive_policy_has_max_receive_count(main_tf_content):
    """Test that redrive policy has max receive count."""
    assert "maxReceiveCount" in main_tf_content


def test_dlq_has_14_day_retention(main_tf_content):
    """Test that DLQ has 14-day message retention."""
    assert "1209600" in main_tf_content


def test_dlq_name_has_suffix(main_tf_content):
    """Test that DLQ name has Dlq suffix."""
    assert '${var.queue_name}Dlq' in main_tf_content


def test_queue_name_variable_exists(variables_tf_content):
    """Test that queue_name variable exists."""
    assert 'variable "queue_name"' in variables_tf_content


def test_visibility_timeout_variable_exists(variables_tf_content):
    """Test that visibility_timeout_seconds variable exists."""
    assert 'variable "visibility_timeout_seconds"' in variables_tf_content


def test_message_retention_variable_exists(variables_tf_content):
    """Test that message_retention_seconds variable exists."""
    assert 'variable "message_retention_seconds"' in variables_tf_content


def test_max_receive_count_variable_exists(variables_tf_content):
    """Test that max_receive_count variable exists."""
    assert 'variable "max_receive_count"' in variables_tf_content


def test_tags_variable_exists(variables_tf_content):
    """Test that tags variable exists."""
    assert 'variable "tags"' in variables_tf_content


def test_queue_url_output_exists(outputs_tf_content):
    """Test that queue_url output exists."""
    assert 'output "queue_url"' in outputs_tf_content


def test_queue_arn_output_exists(outputs_tf_content):
    """Test that queue_arn output exists."""
    assert 'output "queue_arn"' in outputs_tf_content


def test_queue_name_output_exists(outputs_tf_content):
    """Test that queue_name output exists."""
    assert 'output "queue_name"' in outputs_tf_content


def test_dlq_url_output_exists(outputs_tf_content):
    """Test that dlq_url output exists."""
    assert 'output "dlq_url"' in outputs_tf_content


def test_dlq_arn_output_exists(outputs_tf_content):
    """Test that dlq_arn output exists."""
    assert 'output "dlq_arn"' in outputs_tf_content


def test_dlq_name_output_exists(outputs_tf_content):
    """Test that dlq_name output exists."""
    assert 'output "dlq_name"' in outputs_tf_content
