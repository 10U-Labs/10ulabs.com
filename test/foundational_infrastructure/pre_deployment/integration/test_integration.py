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
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    stack_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "stack.py"
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
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    stack_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "stack.py"
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
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    stack_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "stack.py"
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

    # Note: We import the hosted zone (created by AWS during domain registration)
    # so there won't be an AWS::Route53::HostedZone resource in CloudFormation
    # Instead, verify that the stack has outputs for the hosted zone
    outputs = template.find_outputs("*")
    assert "HostedZoneId" in outputs, "Stack should have HostedZoneId output"
    assert "HostedZoneName" in outputs, "Stack should have HostedZoneName output"
    assert "NameServers" in outputs, "Stack should have NameServers output"


def test_cloudtrail_resources_synthesize():
    """Test that CloudTrail resources synthesize correctly"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    stack = DomainStack(
        app,
        "TestDomainStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::Logs::LogGroup", 1)
    template.resource_count_is("AWS::CloudTrail::Trail", 1)


def test_cloudtrail_multi_region_configuration():
    """Test that CloudTrail is configured as multi-region trail"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    stack = DomainStack(
        app,
        "TestDomainStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    trail_resources = template.find_resources("AWS::CloudTrail::Trail")
    assert len(trail_resources) == 1, "Should have exactly one CloudTrail trail"

    for trail_id, trail in trail_resources.items():
        properties = trail.get("Properties", {})
        assert properties.get("IsMultiRegionTrail") is True, "CloudTrail should be multi-region"
        assert properties.get("IncludeGlobalServiceEvents") is True, "CloudTrail should include global service events"


def test_cloudtrail_dependency_chain():
    """Test that CloudFormation dependency chain ensures CloudTrail deploys before domain registration"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    stack = DomainStack(
        app,
        "TestDomainStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    custom_resources = template.find_resources("AWS::CloudFormation::CustomResource")
    cloudtrail_resources = template.find_resources("AWS::CloudTrail::Trail")

    assert len(cloudtrail_resources) > 0, "CloudTrail trail should exist"
    assert len(custom_resources) > 0, "Custom resource for domain registration should exist"

    cloudtrail_ids = set(cloudtrail_resources.keys())

    for resource_id, resource in custom_resources.items():
        properties = resource.get("Properties", {})
        if "DomainName" in properties:
            depends_on = resource.get("DependsOn", [])
            if not isinstance(depends_on, list):
                depends_on = [depends_on]

            depends_on_set = set(depends_on)
            has_cloudtrail_dep = bool(cloudtrail_ids & depends_on_set)

            assert has_cloudtrail_dep, f"Domain registration custom resource should depend on CloudTrail, but DependsOn is {depends_on}"
