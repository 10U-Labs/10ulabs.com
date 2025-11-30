from pathlib import Path


def test_outputs_terraform_file_exists():
    outputs_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "outputs.tf"
    assert outputs_file.exists()


def test_lambda_function_arn_output_exists():
    outputs_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "outputs.tf"
    with open(outputs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'output "lambda_function_arn"' in content


def test_lambda_function_name_output_exists():
    outputs_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "outputs.tf"
    with open(outputs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'output "lambda_function_name"' in content
