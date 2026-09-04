from pathlib import Path

from terraform_config import (
    TEST_AWS_REGION,
    packaged_lambda_archives,
    packaged_lambda_sources,
)


class TestTestAwsRegion:
    def test_is_string(self) -> None:
        assert isinstance(TEST_AWS_REGION, str)

    def test_is_valid_region_format(self) -> None:
        assert TEST_AWS_REGION.startswith("us-") or TEST_AWS_REGION.startswith("eu-")


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
