"""Unit tests for 10uf.org domain stack"""
import json
from pathlib import Path
import aws_cdk as cdk
from aws_cdk.assertions import Template


def test_hosted_zone_created():
    """Test that hosted zone is created with correct domain name"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain-name" / "10uf.org" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import the stack module
    import sys
    sys.path.insert(0, str(Path(__file__).parents[4] / "src"))
    from domain_name import DomainStack

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

    # Create template
    template = Template.from_stack(stack)

    # Assert hosted zone exists with correct name
    template.has_resource_properties(
        "AWS::Route53::HostedZone",
        {
            "Name": f"{config['domain_name']}."
        }
    )


def test_hosted_zone_outputs():
    """Test that stack exports hosted zone ID and name"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain-name" / "10uf.org" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import the stack module
    import sys
    sys.path.insert(0, str(Path(__file__).parents[4] / "src"))

    # Dynamically import DomainStack
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "domain-name" / "10uf.org" / "stack.py"
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

    # Create template
    template = Template.from_stack(stack)

    # Get all outputs
    outputs = template.find_outputs("*")

    # Assert required outputs exist
    assert "HostedZoneId" in outputs
    assert "HostedZoneName" in outputs
    assert "NameServers" in outputs
