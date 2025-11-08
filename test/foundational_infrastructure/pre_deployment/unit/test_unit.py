"""Unit tests for 10ulabs.com domain stack"""
import json
from pathlib import Path
import aws_cdk as cdk
from aws_cdk.assertions import Template


def test_hosted_zone_created():
    """Test that stack references a hosted zone (imported from domain registration)"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Import stack dynamically
    import importlib.util
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
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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

    # Create template
    template = Template.from_stack(stack)

    # Assert Lambda function exists with correct properties
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Runtime": "python3.11",
            "Handler": "handler.handler",
            "Timeout": 900
        }
    )


def test_domain_registration_lambda_has_correct_permissions():
    """Test that domain registration Lambda has all required IAM permissions"""
    app = cdk.App()

    # Load config
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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
                            "route53:CreateHostedZone",
                            "account:GetContactInformation",
                            "organizations:DescribeOrganization"
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
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # Dynamically import DomainStack
    import importlib.util
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


def test_lambda_handler_file_exists():
    """Test that Lambda handler file exists and is valid Python"""
    handler_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "lambda" / "handler.py"
    assert handler_path.exists(), "Lambda handler.py file must exist"

    # Verify it's valid Python by attempting to compile it
    with open(handler_path) as f:
        code = f.read()
        compile(code, str(handler_path), 'exec')

    # Verify it contains required logic
    assert "check_domain_availability" in code
    assert "register_domain" in code
    assert "get_contact_information" in code
    assert "describe_organization" in code
    assert "MasterAccountEmail" in code

#
# Lambda Handler Logic Tests
#

import unittest
from unittest.mock import Mock, patch
import sys

# Add fixtures (cfnresponse stub) and handler to path
fixtures_path = Path(__file__).parents[2] / "fixtures"
handler_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "lambda"
sys.path.insert(0, str(fixtures_path))
sys.path.insert(0, str(handler_path))
import handler as lambda_handler


class TestLambdaHandlerDelete(unittest.TestCase):
    """Test Lambda handler DELETE operations"""

    @patch('handler.cfnresponse')
    def test_delete_request_succeeds_without_action(self, mock_cfnresponse):
        """DELETE requests should succeed without deleting the domain"""
        event = {
            'RequestType': 'Delete',
            'ResourceProperties': {'DomainName': '10ulabs.com'},
            'ResponseURL': 'https://example.com',
            'StackId': 'stack-123',
            'RequestId': 'req-123',
            'LogicalResourceId': 'Domain'
        }
        context = Mock()
        context.log_stream_name = 'log-stream'

        lambda_handler.handler(event, context)

        mock_cfnresponse.send.assert_called_once_with(
            event, context, mock_cfnresponse.SUCCESS, {}
        )


class TestLambdaHandlerAlreadyRegistered(unittest.TestCase):
    """Test Lambda handler when domain is already registered"""

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_already_registered_returns_zone_info(self, mock_cfnresponse, mock_boto3):
        """Already registered domain should return existing hosted zone info"""
        # Mock clients
        mock_route53domains = Mock()
        mock_route53 = Mock()

        # Create exceptions
        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': Mock(),
            'organizations': Mock()
        }[service]

        # Domain already registered
        mock_route53domains.get_domain_detail.return_value = {
            'StatusList': ['REGISTERED']
        }

        # Hosted zone exists
        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [
                {'Name': '10ulabs.com.', 'Id': '/hostedzone/Z1234567890ABC'}
            ]
        }
        mock_route53.get_hosted_zone.return_value = {
            'DelegationSet': {
                'NameServers': ['ns1.example.com', 'ns2.example.com']
            }
        }

        event = {
            'RequestType': 'Create',
            'ResourceProperties': {'DomainName': '10ulabs.com'},
            'ResponseURL': 'https://example.com',
            'StackId': 'stack-123',
            'RequestId': 'req-123',
            'LogicalResourceId': 'Domain'
        }
        context = Mock()
        context.log_stream_name = 'log-stream'

        lambda_handler.handler(event, context)

        mock_cfnresponse.send.assert_called_once()
        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][2] == mock_cfnresponse.SUCCESS
        assert call_args[0][3]['HostedZoneId'] == 'Z1234567890ABC'
        assert call_args[0][3]['NameServers'] == 'ns1.example.com,ns2.example.com'
        assert call_args[0][3]['DomainStatus'] == 'REGISTERED'


class TestLambdaHandlerMissingContactFields(unittest.TestCase):
    """Test Lambda handler with missing contact fields"""

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_missing_fields_returns_error(self, mock_cfnresponse, mock_boto3):
        """Missing contact fields should return FAILED with error"""
        mock_route53domains = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        # Create exceptions
        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': Mock(),
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        # Domain not registered
        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        # Domain available
        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        # Organizations returns email
        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        # Missing fields
        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                # Missing other required fields
            }
        }

        event = {
            'RequestType': 'Create',
            'ResourceProperties': {'DomainName': '10ulabs.com'},
            'ResponseURL': 'https://example.com',
            'StackId': 'stack-123',
            'RequestId': 'req-123',
            'LogicalResourceId': 'Domain'
        }
        context = Mock()
        context.log_stream_name = 'log-stream'

        lambda_handler.handler(event, context)

        mock_cfnresponse.send.assert_called_once()
        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][2] == mock_cfnresponse.FAILED
        assert 'missing contact fields' in call_args[0][3]['Error']


def test_lambda_directory_contains_handler():
    """Test that Lambda directory contains handler.py for deployment"""
    lambda_dir = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "lambda"
    handler_path = lambda_dir / "handler.py"
    assert handler_path.exists(), "handler.py must exist in lambda directory for deployment"


def test_lambda_directory_contains_cfnresponse():
    """Test that Lambda directory contains cfnresponse.py for deployment"""
    lambda_dir = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"
    assert cfnresponse_path.exists(), "cfnresponse.py must exist in lambda directory for deployment"


def test_cfnresponse_contains_send_function():
    """Test that cfnresponse.py contains send() function definition"""
    lambda_dir = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"

    with open(cfnresponse_path) as f:
        content = f.read()
        assert "def send(" in content, "cfnresponse.py must contain send() function definition"


def test_cfnresponse_makes_http_put_request():
    """Test that cfnresponse.py makes HTTP PUT request to CloudFormation"""
    lambda_dir = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"

    with open(cfnresponse_path) as f:
        content = f.read()
        assert "http.request('PUT'" in content, "cfnresponse.py must make HTTP PUT request to CloudFormation presigned URL"


def test_cfnresponse_is_not_empty_stub():
    """Test that cfnresponse.py has functional implementation, not just empty stub"""
    lambda_dir = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"

    with open(cfnresponse_path) as f:
        content = f.read()
        assert content.strip() != "", "cfnresponse.py must not be empty"

        has_pass_only = "pass" in content and "http.request" not in content
        assert not has_pass_only, "cfnresponse.py must have functional implementation, not just 'pass' stub"


def test_cloudtrail_s3_bucket_exists():
    """Test that CloudTrail S3 bucket is created with correct properties"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
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

    from aws_cdk.assertions import Match
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            },
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        }
    )


def test_cloudtrail_s3_bucket_versioning_disabled():
    """Test that CloudTrail S3 bucket has versioning disabled as specified"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
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

    from aws_cdk.assertions import Match
    resources = template.find_resources("AWS::S3::Bucket")
    for resource_id, resource in resources.items():
        properties = resource.get("Properties", {})
        versioning = properties.get("VersioningConfiguration")
        if versioning:
            assert versioning.get("Status") != "Enabled", "S3 bucket should not have versioning enabled"


def test_cloudtrail_log_group_exists():
    """Test that CloudWatch Logs log group for CloudTrail is created"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
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

    template.has_resource_properties(
        "AWS::Logs::LogGroup",
        {
            "RetentionInDays": 365
        }
    )


def test_cloudtrail_trail_exists():
    """Test that CloudTrail trail is created with correct configuration"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
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

    from aws_cdk.assertions import Match
    template.has_resource_properties(
        "AWS::CloudTrail::Trail",
        {
            "IsLogging": True,
            "IsMultiRegionTrail": True,
            "IncludeGlobalServiceEvents": True,
            "EventSelectors": [
                {
                    "ReadWriteType": "All",
                    "IncludeManagementEvents": True
                }
            ]
        }
    )


def test_cloudtrail_sends_to_cloudwatch_logs():
    """Test that CloudTrail is configured to send logs to CloudWatch"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
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

    from aws_cdk.assertions import Match
    template.has_resource_properties(
        "AWS::CloudTrail::Trail",
        {
            "CloudWatchLogsLogGroupArn": Match.any_value()
        }
    )


def test_domain_registration_depends_on_cloudtrail():
    """Test that domain registration has explicit dependency on CloudTrail"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
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

    from aws_cdk.assertions import Match
    resources = template.find_resources("AWS::CloudFormation::CustomResource")

    for resource_id, resource in resources.items():
        properties = resource.get("Properties", {})
        if "DomainName" in properties:
            depends_on = resource.get("DependsOn", [])
            if not isinstance(depends_on, list):
                depends_on = [depends_on]

            cloudtrail_resources = template.find_resources("AWS::CloudTrail::Trail")
            cloudtrail_ids = list(cloudtrail_resources.keys())

            assert len(cloudtrail_ids) > 0, "CloudTrail trail should exist"

            has_cloudtrail_dependency = any(
                trail_id in depends_on for trail_id in cloudtrail_ids
            )
            assert has_cloudtrail_dependency, "Domain registration should depend on CloudTrail trail"
