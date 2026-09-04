from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from terraform_config import (
    TEST_AWS_REGION,
    _parse_map_block,
    get_resource_prefix,
    get_shared_config,
    packaged_lambda_archives,
    packaged_lambda_sources,
    parse_lambda_handler_names,
    _parse_locals,
    _parse_outputs,
)


class TestParseMapBlock:
    def test_parses_simple_map(self) -> None:
        content = '''
        my_map = {
            key1 = "value1"
            key2 = "value2"
        }
        '''
        result = _parse_map_block(content, "my_map")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_returns_empty_dict_when_map_not_found(self) -> None:
        content = '''
        other_map = {
            key1 = "value1"
        }
        '''
        result = _parse_map_block(content, "my_map")
        assert not result

    def test_handles_nested_braces(self) -> None:
        content = '''
        lambda_handler_names = {
            webhook = "${local.resource_prefix}WebhookHandler"
            runner  = "${local.resource_prefix}RunnerHandler"
        }
        '''
        result = _parse_map_block(content, "lambda_handler_names")
        assert result == {
            "webhook": "${local.resource_prefix}WebhookHandler",
            "runner": "${local.resource_prefix}RunnerHandler",
        }

    def test_handles_empty_map(self) -> None:
        content = '''
        empty_map = {
        }
        '''
        result = _parse_map_block(content, "empty_map")
        assert not result


class TestParseLocals:
    def test_returns_dict(self) -> None:
        result = _parse_locals()
        assert isinstance(result, dict)

    def test_contains_aws_region(self) -> None:
        result = _parse_locals()
        assert "aws_region" in result

    def test_contains_resource_prefix(self) -> None:
        result = _parse_locals()
        assert "resource_prefix" in result


class TestParseLambdaHandlerNames:
    def test_returns_dict(self) -> None:
        result = parse_lambda_handler_names()
        assert isinstance(result, dict)

    def test_values_do_not_contain_unresolved_local_resource_prefix(self) -> None:
        result = parse_lambda_handler_names()
        unresolved_values = [v for v in result.values() if "${local.resource_prefix}" in v]
        assert not unresolved_values


def test_parse_outputs_returns_dict() -> None:
    result = _parse_outputs()
    assert isinstance(result, dict)


class TestGetSharedConfig:
    def test_returns_dict(self) -> None:
        result = get_shared_config()
        assert isinstance(result, dict)

    def test_contains_lambda_handler_names_key(self) -> None:
        result = get_shared_config()
        assert "lambda_handler_names" in result

    def test_lambda_handler_names_is_dict(self) -> None:
        result = get_shared_config()
        assert isinstance(result["lambda_handler_names"], dict)

    def test_omits_aws_account_id(self) -> None:
        result = get_shared_config()
        assert "aws_account_id" not in result


class TestTestAwsRegion:
    def test_is_string(self) -> None:
        assert isinstance(TEST_AWS_REGION, str)

    def test_is_valid_region_format(self) -> None:
        assert TEST_AWS_REGION.startswith("us-") or TEST_AWS_REGION.startswith("eu-")


class TestGetResourcePrefix:
    def test_returns_string(self) -> None:
        result = get_resource_prefix()
        assert isinstance(result, str)

    def test_returns_non_empty(self) -> None:
        result = get_resource_prefix()
        assert len(result) > 0


class TestGetSharedConfigDomainName:
    @patch('terraform_config._parse_locals')
    @patch('terraform_config._parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_sets_api_fqdn_when_domain_name_present(
        self, mock_handlers: MagicMock, mock_outputs: MagicMock, mock_locals: MagicMock
    ) -> None:
        mock_locals.return_value = {"domain_name": "example.com"}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert result.get("api_fqdn") == "api.example.com"

    @patch('terraform_config._parse_locals')
    @patch('terraform_config._parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_no_api_fqdn_when_domain_name_empty(
        self, mock_handlers: MagicMock, mock_outputs: MagicMock, mock_locals: MagicMock
    ) -> None:
        mock_locals.return_value = {"domain_name": ""}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert "api_fqdn" not in result

    @patch('terraform_config._parse_locals')
    @patch('terraform_config._parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_no_api_fqdn_when_domain_name_missing(
        self, mock_handlers: MagicMock, mock_outputs: MagicMock, mock_locals: MagicMock
    ) -> None:
        mock_locals.return_value = {}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert "api_fqdn" not in result


def test_packaged_lambda_sources_reads_a_single_packaged_file(tmp_path: Path) -> None:
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
}
""")
    assert packaged_lambda_sources(tf_file) == ["lambda/handler.py"]


def test_packaged_lambda_sources_reads_a_named_archive_entry(tmp_path: Path) -> None:
    tf_file = tmp_path / "analytics.tf"
    tf_file.write_text("""
data "archive_file" "export" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/exporter/handler.py")
    filename = "handler.py"
  }
}
""")
    assert packaged_lambda_sources(tf_file) == ["lambda/exporter/handler.py"]


def test_packaged_lambda_sources_omits_a_file_from_outside_the_stack(tmp_path: Path) -> None:
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/../../../../lib/python/lambda_http/__init__.py")
    filename = "lambda_http.py"
  }
}
""")
    assert packaged_lambda_sources(tf_file) == ["lambda/handler.py"]


def test_packaged_lambda_archives_reads_the_archive_a_package_is_written_to(tmp_path: Path) -> None:
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}
""")
    assert packaged_lambda_archives(tf_file) == [
        ".terraform/lambda_packages/handler.zip"
    ]


def test_packaged_lambda_archives_reads_every_package_a_file_declares(tmp_path: Path) -> None:
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "tracker" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/tracker.zip"
}

data "archive_file" "exporter" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/exporter.zip"
}
""")
    assert packaged_lambda_archives(tf_file) == [
        ".terraform/lambda_packages/tracker.zip",
        ".terraform/lambda_packages/exporter.zip",
    ]


def test_packaged_lambda_archives_reads_nothing_from_a_file_that_packages_nothing(
    tmp_path: Path,
) -> None:
    tf_file = tmp_path / "dynamodb.tf"
    tf_file.write_text("""
resource "aws_dynamodb_table" "sessions" {
  name = "sessions"
}
""")
    assert not packaged_lambda_archives(tf_file)
