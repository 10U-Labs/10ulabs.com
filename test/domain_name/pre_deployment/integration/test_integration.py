"""Pre-deployment integration tests for domain stack"""
import json
from pathlib import Path
import aws_cdk as cdk
from aws_cdk.assertions import Template
import importlib.util


def test_stack_synthesizes_correctly():
    """Test that the domain stack synthesizes without errors"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    stack_path = Path(__file__).parents[4] / "src" / "domain_name" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    # Create stack
    stack = DomainStack(
        app,
        "TestDomainStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    # Synthesize and get template
    template = Template.from_stack(stack)

    # Basic sanity checks
    assert template is not None


def test_stack_exports_required_outputs():
    """Test that stack exports all required outputs for other stacks"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    stack_path = Path(__file__).parents[4] / "src" / "domain_name" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    # Create stack
    stack = DomainStack(
        app,
        "TestDomainStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    # Get template
    template = Template.from_stack(stack)

    # Check that required outputs exist
    outputs = template.find_outputs("*")

    required_outputs = ["HostedZoneId", "HostedZoneName", "NameServers"]
    for output_name in required_outputs:
        assert output_name in outputs, f"Missing required output: {output_name}"


def test_hosted_zone_configuration():
    """Test that hosted zone is configured correctly"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    stack_path = Path(__file__).parents[4] / "src" / "domain_name" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    # Create stack
    stack = DomainStack(
        app,
        "TestDomainStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    # Get template
    template = Template.from_stack(stack)

    # Verify hosted zone properties
    template.has_resource_properties(
        "AWS::Route53::HostedZone",
        {
            "Name": f"{config['domain_name']}."
        }
    )
