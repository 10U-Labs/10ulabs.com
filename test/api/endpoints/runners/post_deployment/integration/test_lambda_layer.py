"""Integration tests for Lambda Layer deployment.

These atomic tests verify the Lambda Layer is correctly deployed and attached.
They run before higher-level tests to provide fast failure diagnosis.
"""
import boto3


def test_lambda_layer_exists(config):
    """Verify TenULabsRunnersLayer exists in AWS."""
    lambda_client = boto3.client("lambda", region_name=config["aws_region"])
    layer_name = "TenULabsRunnersLayer"

    response = lambda_client.list_layer_versions(LayerName=layer_name, MaxItems=1)

    assert len(response["LayerVersions"]) > 0


def test_webhook_handler_has_layer_attached(config):
    """Verify TenULabsWebhookHandler has the runners layer attached."""
    lambda_client = boto3.client("lambda", region_name=config["aws_region"])
    function_name = "TenULabsWebhookHandler"

    response = lambda_client.get_function_configuration(FunctionName=function_name)
    layers = response.get("Layers", [])
    layer_arns = [layer["Arn"] for layer in layers]

    assert any("TenULabsRunnersLayer" in arn for arn in layer_arns)


def test_sqs_handler_has_layer_attached(config):
    """Verify TenULabsSqsHandler has the runners layer attached."""
    lambda_client = boto3.client("lambda", region_name=config["aws_region"])
    function_name = "TenULabsSqsHandler"

    response = lambda_client.get_function_configuration(FunctionName=function_name)
    layers = response.get("Layers", [])
    layer_arns = [layer["Arn"] for layer in layers]

    assert any("TenULabsRunnersLayer" in arn for arn in layer_arns)


def test_layer_contains_runner_labels_js(layer_contents):
    """Verify layer contains runner_labels.js module."""
    assert "nodejs/runners-layer/runner_labels.js" in layer_contents


def test_layer_contains_webhook_ingress_js(layer_contents):
    """Verify layer contains webhook_ingress.js module."""
    assert "nodejs/runners-layer/webhook_ingress.js" in layer_contents


def test_layer_contains_runners_json(layer_contents):
    """Verify layer contains etc/runners.json configuration."""
    assert "nodejs/runners-layer/etc/runners.json" in layer_contents


def test_layer_contains_index_js(layer_contents):
    """Verify layer contains index.js entry point."""
    assert "nodejs/runners-layer/index.js" in layer_contents


def test_layer_contains_package_json(layer_contents):
    """Verify layer contains package.json."""
    assert "nodejs/runners-layer/package.json" in layer_contents
