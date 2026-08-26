def test_module_files_exist(module_path):
    assert (module_path / "main.tf").exists()


def test_module_variables_file_exists(module_path):
    assert (module_path / "variables.tf").exists()


def test_module_outputs_file_exists(module_path):
    assert (module_path / "outputs.tf").exists()


def test_main_queue_resource_exists(main_tf_content):
    assert 'resource "aws_sqs_queue" "main"' in main_tf_content


def test_dlq_resource_exists(main_tf_content):
    assert 'resource "aws_sqs_queue" "dlq"' in main_tf_content


def test_main_queue_uses_queue_name_variable(main_tf_content):
    assert "var.queue_name" in main_tf_content


def test_main_queue_has_visibility_timeout(main_tf_content):
    assert "visibility_timeout_seconds" in main_tf_content


def test_main_queue_has_message_retention(main_tf_content):
    assert "message_retention_seconds" in main_tf_content


def test_main_queue_has_redrive_policy(main_tf_content):
    assert "redrive_policy" in main_tf_content


def test_redrive_policy_references_dlq(main_tf_content):
    assert "aws_sqs_queue.dlq.arn" in main_tf_content


def test_redrive_policy_has_max_receive_count(main_tf_content):
    assert "maxReceiveCount" in main_tf_content


def test_dlq_has_14_day_retention(main_tf_content):
    assert "1209600" in main_tf_content


def test_dlq_name_has_suffix(main_tf_content):
    assert '${var.queue_name}Dlq' in main_tf_content


def test_queue_name_variable_exists(variables_tf_content):
    assert 'variable "queue_name"' in variables_tf_content


def test_visibility_timeout_variable_exists(variables_tf_content):
    assert 'variable "visibility_timeout_seconds"' in variables_tf_content


def test_message_retention_variable_exists(variables_tf_content):
    assert 'variable "message_retention_seconds"' in variables_tf_content


def test_max_receive_count_variable_exists(variables_tf_content):
    assert 'variable "max_receive_count"' in variables_tf_content


def test_tags_variable_exists(variables_tf_content):
    assert 'variable "tags"' in variables_tf_content


def test_queue_url_output_exists(outputs_tf_content):
    assert 'output "queue_url"' in outputs_tf_content


def test_queue_arn_output_exists(outputs_tf_content):
    assert 'output "queue_arn"' in outputs_tf_content


def test_queue_name_output_exists(outputs_tf_content):
    assert 'output "queue_name"' in outputs_tf_content


def test_dlq_url_output_exists(outputs_tf_content):
    assert 'output "dlq_url"' in outputs_tf_content


def test_dlq_arn_output_exists(outputs_tf_content):
    assert 'output "dlq_arn"' in outputs_tf_content


def test_dlq_name_output_exists(outputs_tf_content):
    assert 'output "dlq_name"' in outputs_tf_content
