import json
from pathlib import Path
import importlib.util
import aws_cdk as cdk
from aws_cdk.assertions import Template


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    assert config_path.exists()


def test_config_has_aws_account_id():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_account_id" in config


def test_config_has_aws_region():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_region" in config


def test_config_has_subdomain_name():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "subdomain_name" in config


def test_config_has_parent_domain():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "parent_domain" in config


def test_api_has_lambda_function():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    resources = template.find_resources("AWS::Lambda::Function")
    assert len(resources) >= 1


def test_api_has_api_gateway():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_api_has_certificate():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_api_has_route53_record():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Route53::RecordSet", 1)


def test_api_has_url_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiUrl" in outputs


def test_api_has_domain_name_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiDomainName" in outputs


def test_api_has_endpoint_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiEndpoint" in outputs
