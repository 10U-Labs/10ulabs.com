"""Tests to validate image_for_ecs_runners infrastructure exists."""


def test_terraform_outputs_readable(image_for_ecs_runners_outputs):
    """Verify image_for_ecs_runners terraform outputs are accessible."""
    assert image_for_ecs_runners_outputs.get("lambda_function_arn"), \
        "lambda_function_arn output not found in image_for_ecs_runners"
    assert image_for_ecs_runners_outputs.get("lambda_function_name"), \
        "lambda_function_name output not found in image_for_ecs_runners"
    assert image_for_ecs_runners_outputs.get("lambda_invoke_arn"), \
        "lambda_invoke_arn output not found in image_for_ecs_runners"
