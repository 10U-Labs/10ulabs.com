from test.health.conftest import HEALTH_SRC

OUTPUTS_FILE = HEALTH_SRC / "outputs.tf"


def test_outputs_terraform_file_exists():
    assert OUTPUTS_FILE.exists()


def test_lambda_function_arn_output_exists():
    with open(OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'output "lambda_function_arn"' in content


def test_lambda_function_name_output_exists():
    with open(OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'output "lambda_function_name"' in content
