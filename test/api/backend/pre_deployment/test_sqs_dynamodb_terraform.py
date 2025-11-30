from pathlib import Path


def test_sqs_dynamodb_terraform_file_exists():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    assert sqs_ddb_file.exists()


def test_webhook_dlq_exists():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "webhook_dlq"' in content


def test_job_queue_dlq_exists():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "job_queue_dlq"' in content


def test_job_queue_exists():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sqs_queue" "job_queue"' in content


def test_job_queue_has_redrive_policy():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'redrive_policy' in content


def test_idempotency_table_exists():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_dynamodb_table" "idempotency"' in content


def test_incidents_table_exists():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_dynamodb_table" "incidents"' in content


def test_circuit_breaker_state_table_exists():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_dynamodb_table" "circuit_breaker_state"' in content


def test_dynamodb_tables_have_ttl():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'ttl' in content


def test_dynamodb_tables_have_billing_mode():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'billing_mode' in content


def test_dynamodb_tables_use_pay_per_request():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'PAY_PER_REQUEST' in content


def test_circuit_breaker_state_table_has_streams_enabled():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'stream_enabled   = true' in content


def test_circuit_breaker_state_table_stream_has_new_and_old_images():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'stream_view_type = "NEW_AND_OLD_IMAGES"' in content


def test_circuit_breaker_state_table_stream_config_in_correct_table():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    cb_table_start = content.find('resource "aws_dynamodb_table" "circuit_breaker_state"')
    cb_table_section = content[cb_table_start:cb_table_start + 800]
    assert 'stream_enabled' in cb_table_section


def test_idempotency_table_does_not_have_streams():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    idempotency_start = content.find('resource "aws_dynamodb_table" "idempotency"')
    idempotency_end = content.find('resource "aws_dynamodb_table" "incidents"')
    idempotency_section = content[idempotency_start:idempotency_end]
    assert 'stream_enabled' not in idempotency_section


def test_incidents_table_does_not_have_streams():
    sqs_ddb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "sqs_dynamodb.tf"
    with open(sqs_ddb_file, encoding="utf-8") as f:
        content = f.read()
    incidents_start = content.find('resource "aws_dynamodb_table" "incidents"')
    incidents_end = content.find('resource "aws_dynamodb_table" "circuit_breaker_state"')
    incidents_section = content[incidents_start:incidents_end]
    assert 'stream_enabled' not in incidents_section
