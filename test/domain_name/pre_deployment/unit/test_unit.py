"""Unit tests for 10uf.org domain stack"""
import json
from pathlib import Path
import aws_cdk as cdk
from aws_cdk.assertions import Template


def test_hosted_zone_created():
    """Test that stack references a hosted zone (imported from domain registration)"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    import importlib.util
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

    # Create template
    template = Template.from_stack(stack)

    # Note: We import the hosted zone from AWS (created during domain registration)
    # so there won't be an AWS::Route53::HostedZone resource in CloudFormation
    # Instead, verify the stack has outputs referencing the hosted zone
    outputs = template.find_outputs("*")
    assert "HostedZoneId" in outputs
    assert "HostedZoneName" in outputs


def test_hosted_zone_outputs():
    """Test that stack exports hosted zone ID and name"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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

    # Create template
    template = Template.from_stack(stack)

    # Get all outputs
    outputs = template.find_outputs("*")

    # Assert required outputs exist
    assert "HostedZoneId" in outputs
    assert "HostedZoneName" in outputs
    assert "NameServers" in outputs


def test_domain_registration_lambda_exists():
    """Test that domain registration Lambda function is created"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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

    # Create template
    template = Template.from_stack(stack)

    # Assert Lambda function exists with correct properties
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Runtime": "python3.11",
            "Handler": "index.handler",
            "Timeout": 900
        }
    )


def test_domain_registration_lambda_has_correct_permissions():
    """Test that domain registration Lambda has all required IAM permissions"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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

    # Create template
    template = Template.from_stack(stack)

    # Check for IAM role with required permissions
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": [
                    {
                        "Action": [
                            "route53domains:CheckDomainAvailability",
                            "route53domains:GetDomainDetail",
                            "route53domains:RegisterDomain",
                            "route53:ListHostedZonesByName",
                            "route53:GetHostedZone",
                            "account:GetContactInformation"
                        ],
                        "Effect": "Allow",
                        "Resource": "*"
                    }
                ]
            }
        }
    )


def test_custom_resource_for_domain_registration_exists():
    """Test that custom resource for domain registration is created"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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

    # Create template
    template = Template.from_stack(stack)

    # Assert custom resource exists
    template.resource_count_is("AWS::CloudFormation::CustomResource", 1)

    # Verify custom resource has correct properties
    from aws_cdk.assertions import Match
    template.has_resource_properties(
        "AWS::CloudFormation::CustomResource",
        {
            "DomainName": config["domain_name"]
        }
    )


def test_lambda_code_contains_domain_registration_logic():
    """Test that Lambda code contains required domain registration logic"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "domain_name" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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

    # Create template
    template = Template.from_stack(stack)

    # Get the Lambda function code
    from aws_cdk.assertions import Match
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Code": {
                "ZipFile": Match.string_like_regexp(".*check_domain_availability.*")
            }
        }
    )

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Code": {
                "ZipFile": Match.string_like_regexp(".*register_domain.*")
            }
        }
    )

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Code": {
                "ZipFile": Match.string_like_regexp(".*get_contact_information.*")
            }
        }
    )
