"""Unit tests for 10ulabs.com domain stack"""
import json
from pathlib import Path
import aws_cdk as cdk
from aws_cdk.assertions import Template


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    assert config_path.exists(), f"Config file not found at {config_path}"


def test_config_has_aws_account_id():
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_account_id" in config


def test_config_has_aws_region():
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_region" in config


def test_config_has_domain_name():
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "domain_name" in config


def test_hosted_zone_has_id_output():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

    outputs = template.find_outputs("*")
    assert "HostedZoneId" in outputs


def test_hosted_zone_has_name_output():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

    outputs = template.find_outputs("*")
    assert "HostedZoneName" in outputs


def test_hosted_zone_exports_name_servers():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

    outputs = template.find_outputs("*")

    assert "NameServers" in outputs


def test_domain_registration_lambda_has_python_runtime():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::Lambda::Function",
        {
            "Runtime": "python3.11"
        }
    )


def test_domain_registration_lambda_has_correct_handler():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::Lambda::Function",
        {
            "Handler": "handler.handler"
        }
    )


def test_domain_registration_lambda_has_timeout():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::Lambda::Function",
        {
            "Timeout": 900
        }
    )


def test_domain_registration_lambda_has_description():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack
    stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
    template = Template.from_stack(stack)
    from aws_cdk.assertions import Match
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Description": Match.string_like_regexp("Domain registration handler - Updated .*")
        }
    )


def test_custom_resource_for_domain_registration_count():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    template.resource_count_is("AWS::CloudFormation::CustomResource", 1)


def test_custom_resource_has_domain_name_property():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::CloudFormation::CustomResource",
        {
            "DomainName": config["domain_name"]
        }
    )


def test_lambda_handler_file_exists():
    handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda" / "handler.py"
    assert handler_path.exists(), "Lambda handler.py file must exist"


def test_lambda_handler_is_valid_python():
    handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda" / "handler.py"
    with open(handler_path) as f:
        code = f.read()
        compile(code, str(handler_path), 'exec')


def test_lambda_handler_contains_check_domain_availability():
    handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda" / "handler.py"
    with open(handler_path) as f:
        code = f.read()
    assert "check_domain_availability" in code


def test_lambda_handler_contains_register_domain():
    handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda" / "handler.py"
    with open(handler_path) as f:
        code = f.read()
    assert "register_domain" in code


def test_lambda_handler_contains_get_contact_information():
    handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda" / "handler.py"
    with open(handler_path) as f:
        code = f.read()
    assert "get_contact_information" in code


def test_lambda_handler_contains_describe_organization():
    handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda" / "handler.py"
    with open(handler_path) as f:
        code = f.read()
    assert "describe_organization" in code


def test_lambda_handler_contains_master_account_email():
    handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda" / "handler.py"
    with open(handler_path) as f:
        code = f.read()
    assert "MasterAccountEmail" in code

#
# Lambda Handler Logic Tests
#

import unittest
from unittest.mock import Mock, patch
import sys

# Add fixtures (cfnresponse stub) and handler to path
fixtures_path = Path(__file__).parents[2] / "fixtures"
handler_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda"
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

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_already_registered_calls_cfnresponse_send_once(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_route53 = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': Mock(),
            'organizations': Mock()
        }[service]

        mock_route53domains.get_domain_detail.return_value = {
            'StatusList': ['REGISTERED']
        }

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

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_already_registered_returns_success(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_route53 = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': Mock(),
            'organizations': Mock()
        }[service]

        mock_route53domains.get_domain_detail.return_value = {
            'StatusList': ['REGISTERED']
        }

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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][2] == mock_cfnresponse.SUCCESS

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_already_registered_returns_hosted_zone_id(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_route53 = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': Mock(),
            'organizations': Mock()
        }[service]

        mock_route53domains.get_domain_detail.return_value = {
            'StatusList': ['REGISTERED']
        }

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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][3]['HostedZoneId'] == 'Z1234567890ABC'

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_already_registered_returns_name_servers(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_route53 = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': Mock(),
            'organizations': Mock()
        }[service]

        mock_route53domains.get_domain_detail.return_value = {
            'StatusList': ['REGISTERED']
        }

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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][3]['NameServers'] == 'ns1.example.com,ns2.example.com'

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_already_registered_returns_domain_status(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_route53 = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': Mock(),
            'organizations': Mock()
        }[service]

        mock_route53domains.get_domain_detail.return_value = {
            'StatusList': ['REGISTERED']
        }

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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][3]['DomainStatus'] == 'REGISTERED'


class TestLambdaHandlerMissingContactFields(unittest.TestCase):

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_missing_fields_calls_cfnresponse_send_once(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': Mock(),
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
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

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_missing_fields_returns_failed_status(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': Mock(),
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][2] == mock_cfnresponse.FAILED

    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_missing_fields_returns_error_message(self, mock_cfnresponse, mock_boto3):
        mock_route53domains = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': Mock(),
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
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

        call_args = mock_cfnresponse.send.call_args
        assert 'missing contact fields' in call_args[0][3]['Error']


class TestLambdaHandlerRegistrationFailure(unittest.TestCase):

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_registration_failure_calls_get_operation_detail(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'FAILED',
            'Message': 'Payment method not configured'
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

        mock_route53domains.get_operation_detail.assert_called_once_with(OperationId='op-123')

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_registration_failure_returns_failed_status(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'FAILED',
            'Message': 'Payment method not configured'
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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][2] == mock_cfnresponse.FAILED

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_registration_failure_includes_error_message(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'FAILED',
            'Message': 'Payment method not configured'
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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][3]['Error'] == 'Payment method not configured'

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_registration_failure_includes_operation_id(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'FAILED',
            'Message': 'Payment method not configured'
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

        call_args = mock_cfnresponse.send.call_args
        assert call_args[0][3]['OperationId'] == 'op-123'


class TestDomainRegistrationParameters(unittest.TestCase):

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_includes_billing_contact(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert 'BillingContact' in call_args[1]

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_enables_billing_privacy_protection(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert call_args[1].get('PrivacyProtectBillingContact') is True

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_includes_admin_contact(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert 'AdminContact' in call_args[1]

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_includes_registrant_contact(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert 'RegistrantContact' in call_args[1]

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_includes_tech_contact(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert 'TechContact' in call_args[1]

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_enables_admin_privacy_protection(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert call_args[1].get('PrivacyProtectAdminContact') is True

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_enables_registrant_privacy_protection(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert call_args[1].get('PrivacyProtectRegistrantContact') is True

    @patch('handler.time')
    @patch('handler.boto3')
    @patch('handler.cfnresponse')
    def test_register_domain_enables_tech_privacy_protection(self, mock_cfnresponse, mock_boto3, mock_time):
        mock_route53domains = Mock()
        mock_route53 = Mock()
        mock_account = Mock()
        mock_organizations = Mock()

        InvalidInput = type('InvalidInput', (Exception,), {})
        mock_route53domains.exceptions = Mock()
        mock_route53domains.exceptions.InvalidInput = InvalidInput

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'route53domains': mock_route53domains,
            'route53': mock_route53,
            'account': mock_account,
            'organizations': mock_organizations
        }[service]

        mock_route53domains.get_domain_detail.side_effect = InvalidInput('Not found')

        mock_route53domains.check_domain_availability.return_value = {
            'Availability': 'AVAILABLE'
        }

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'root@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1.2125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        mock_route53domains.register_domain.return_value = {
            'OperationId': 'op-123'
        }

        mock_route53domains.get_operation_detail.return_value = {
            'Status': 'SUCCESSFUL'
        }

        mock_route53.list_hosted_zones_by_name.return_value = {
            'HostedZones': [{
                'Id': '/hostedzone/Z123',
                'Name': '10ulabs.com.'
            }]
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

        call_args = mock_route53domains.register_domain.call_args
        assert call_args[1].get('PrivacyProtectTechContact') is True


class TestPhoneNumberFormatting(unittest.TestCase):

    def test_phone_with_dashes_us(self):
        from handler import get_contact_info
        mock_account = Mock()
        mock_organizations = Mock()

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'test@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '212-555-1234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        contact = get_contact_info(mock_account, mock_organizations)

        assert contact['PhoneNumber'] == '+1.2125551234'

    def test_phone_with_parentheses_us(self):
        from handler import get_contact_info
        mock_account = Mock()
        mock_organizations = Mock()

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'test@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '(212) 555-1234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        contact = get_contact_info(mock_account, mock_organizations)

        assert contact['PhoneNumber'] == '+1.2125551234'

    def test_phone_with_country_code_us(self):
        from handler import get_contact_info
        mock_account = Mock()
        mock_organizations = Mock()

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'test@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '+1 (212) 555-1234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        contact = get_contact_info(mock_account, mock_organizations)

        assert contact['PhoneNumber'] == '+1.2125551234'

    def test_phone_uk_format(self):
        from handler import get_contact_info
        mock_account = Mock()
        mock_organizations = Mock()

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'test@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'Jane Smith',
                'PhoneNumber': '020 7123 4567',
                'AddressLine1': '10 Downing St',
                'City': 'London',
                'StateOrRegion': 'England',
                'CountryCode': 'GB',
                'PostalCode': 'SW1A 2AA'
            }
        }

        contact = get_contact_info(mock_account, mock_organizations)

        assert contact['PhoneNumber'] == '+44.02071234567'

    def test_phone_already_formatted_us(self):
        from handler import get_contact_info
        mock_account = Mock()
        mock_organizations = Mock()

        mock_organizations.describe_organization.return_value = {
            'Organization': {'MasterAccountEmail': 'test@example.com'}
        }

        mock_account.get_contact_information.return_value = {
            'ContactInformation': {
                'FullName': 'John Doe',
                'PhoneNumber': '12125551234',
                'AddressLine1': '123 Main St',
                'City': 'New York',
                'StateOrRegion': 'NY',
                'CountryCode': 'US',
                'PostalCode': '10001'
            }
        }

        contact = get_contact_info(mock_account, mock_organizations)

        assert contact['PhoneNumber'] == '+1.2125551234'


def test_lambda_directory_contains_handler():
    """Test that Lambda directory contains handler.py for deployment"""
    lambda_dir = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda"
    handler_path = lambda_dir / "handler.py"
    assert handler_path.exists(), "handler.py must exist in lambda directory for deployment"


def test_lambda_directory_contains_cfnresponse():
    """Test that Lambda directory contains cfnresponse.py for deployment"""
    lambda_dir = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"
    assert cfnresponse_path.exists(), "cfnresponse.py must exist in lambda directory for deployment"


def test_cfnresponse_contains_send_function():
    """Test that cfnresponse.py contains send() function definition"""
    lambda_dir = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"

    with open(cfnresponse_path) as f:
        content = f.read()
        assert "def send(" in content, "cfnresponse.py must contain send() function definition"


def test_cfnresponse_makes_http_put_request():
    """Test that cfnresponse.py makes HTTP PUT request to CloudFormation"""
    lambda_dir = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"

    with open(cfnresponse_path) as f:
        content = f.read()
        assert "http.request('PUT'" in content, "cfnresponse.py must make HTTP PUT request to CloudFormation presigned URL"


def test_cfnresponse_is_not_empty():
    lambda_dir = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"

    with open(cfnresponse_path) as f:
        content = f.read()
        assert content.strip() != "", "cfnresponse.py must not be empty"


def test_cfnresponse_is_not_pass_stub():
    lambda_dir = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "lambda"
    cfnresponse_path = lambda_dir / "cfnresponse.py"

    with open(cfnresponse_path) as f:
        content = f.read()
        has_pass_only = "pass" in content and "http.request" not in content
        assert not has_pass_only, "cfnresponse.py must have functional implementation, not just 'pass' stub"


def test_cloudtrail_s3_bucket_exists():
    """Test that CloudTrail S3 bucket resource is created"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    template.resource_count_is("AWS::S3::Bucket", 2)


def test_cloudtrail_s3_bucket_has_encryption():
    """Test that CloudTrail S3 bucket has encryption configured"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
            }
        }
    )


def test_cloudtrail_s3_bucket_blocks_public_acls():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True
            }
        }
    )


def test_cloudtrail_s3_bucket_blocks_public_policy():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicPolicy": True
            }
        }
    )


def test_cloudtrail_s3_bucket_ignores_public_acls():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "IgnorePublicAcls": True
            }
        }
    )


def test_cloudtrail_s3_bucket_restricts_public_buckets():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "RestrictPublicBuckets": True
            }
        }
    )


def test_cloudtrail_s3_bucket_with_logging_exists():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

    resources = template.find_resources("AWS::S3::Bucket")
    cloudtrail_bucket_found = False
    for resource_id, resource in resources.items():
        properties = resource.get("Properties", {})
        if "LoggingConfiguration" in properties:
            cloudtrail_bucket_found = True
            break
    assert cloudtrail_bucket_found, "CloudTrail S3 bucket with LoggingConfiguration not found"


def test_cloudtrail_s3_bucket_versioning_disabled():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    versioning_disabled = True
    for resource_id, resource in resources.items():
        properties = resource.get("Properties", {})
        if "LoggingConfiguration" in properties:
            versioning = properties.get("VersioningConfiguration")
            if versioning and versioning.get("Status") == "Enabled":
                versioning_disabled = False
                break
    assert versioning_disabled, "CloudTrail S3 bucket should not have versioning enabled"


def test_cloudtrail_s3_bucket_has_auto_delete():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack
    stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        }
    )
    template.has_resource_properties("Custom::S3AutoDeleteObjects", {})


def test_cloudtrail_log_group_exists():
    """Test that CloudWatch Logs log group resource is created"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    template.resource_count_is("AWS::Logs::LogGroup", 1)


def test_cloudtrail_log_group_has_retention():
    """Test that CloudWatch Logs log group has 1-year retention configured"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    """Test that CloudTrail trail resource is created"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    template.resource_count_is("AWS::CloudTrail::Trail", 1)


def test_cloudtrail_trail_is_logging():
    """Test that CloudTrail trail is configured to log"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::CloudTrail::Trail",
        {
            "IsLogging": True
        }
    )


def test_cloudtrail_trail_is_multi_region():
    """Test that CloudTrail trail is configured as multi-region"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::CloudTrail::Trail",
        {
            "IsMultiRegionTrail": True
        }
    )


def test_cloudtrail_trail_includes_global_events():
    """Test that CloudTrail trail includes global service events"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::CloudTrail::Trail",
        {
            "IncludeGlobalServiceEvents": True
        }
    )


def test_cloudtrail_trail_logs_all_read_write_events():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::CloudTrail::Trail",
        {
            "EventSelectors": [
                {
                    "ReadWriteType": "All"
                }
            ]
        }
    )


def test_cloudtrail_trail_includes_management_events():
    app = cdk.App()
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)
    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
        "AWS::CloudTrail::Trail",
        {
            "EventSelectors": [
                {
                    "IncludeManagementEvents": True
                }
            ]
        }
    )


def test_cloudtrail_trail_sends_to_cloudwatch_logs():
    """Test that CloudTrail trail is configured to send logs to CloudWatch"""
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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


def test_cloudtrail_trail_exists_for_dependency():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    cloudtrail_resources = template.find_resources("AWS::CloudTrail::Trail")
    cloudtrail_ids = list(cloudtrail_resources.keys())

    assert len(cloudtrail_ids) > 0, "CloudTrail trail should exist"


def test_domain_registration_depends_on_cloudtrail():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    import importlib.util
    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

            has_cloudtrail_dependency = any(
                trail_id in depends_on for trail_id in cloudtrail_ids
            )
            assert has_cloudtrail_dependency, "Domain registration should depend on CloudTrail trail"


class TestLambdaIAMPermissions(unittest.TestCase):

    def test_lambda_has_route53domains_check_availability_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["route53domains:CheckDomainAvailability"])}]}})

    def test_lambda_has_route53domains_get_domain_detail_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["route53domains:GetDomainDetail"])}]}})

    def test_lambda_has_route53domains_get_operation_detail_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["route53domains:GetOperationDetail"])}]}})

    def test_lambda_has_route53domains_register_domain_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["route53domains:RegisterDomain"])}]}})

    def test_lambda_has_route53_list_hosted_zones_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["route53:ListHostedZonesByName"])}]}})

    def test_lambda_has_route53_get_hosted_zone_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["route53:GetHostedZone"])}]}})

    def test_lambda_has_route53_create_hosted_zone_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["route53:CreateHostedZone"])}]}})

    def test_lambda_has_account_get_contact_info_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["account:GetContactInformation"])}]}})

    def test_lambda_has_account_get_alternate_contact_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["account:GetAlternateContact"])}]}})

    def test_lambda_has_organizations_describe_org_permission(self):
        from aws_cdk.assertions import Match
        app = cdk.App()
        config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
        with open(config_path) as f:
            config = json.load(f)
        import importlib.util
        stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
        spec = importlib.util.spec_from_file_location("domain_stack", stack_path)
        domain_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(domain_module)
        DomainStack = domain_module.DomainStack
        stack = DomainStack(app, "TestStack", config=config, env=cdk.Environment(account=str(config["aws_account_id"]), region=config["aws_region"]))
        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{"Action": Match.array_with(["organizations:DescribeOrganization"])}]}})


def test_stack_synthesizes_correctly():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

    assert template is not None


def test_stack_exports_required_outputs():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

    outputs = template.find_outputs("*")

    required_outputs = ["HostedZoneId", "HostedZoneName", "NameServers"]
    for output_name in required_outputs:
        assert output_name in outputs, f"Missing required output: {output_name}"


def test_hosted_zone_has_id_output_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    outputs = template.find_outputs("*")
    assert "HostedZoneId" in outputs, "Stack should have HostedZoneId output"


def test_hosted_zone_has_name_output_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    outputs = template.find_outputs("*")
    assert "HostedZoneName" in outputs, "Stack should have HostedZoneName output"


def test_hosted_zone_has_nameservers_output_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    outputs = template.find_outputs("*")
    assert "NameServers" in outputs, "Stack should have NameServers output"


def test_cloudtrail_resources_synthesize():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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

    template.resource_count_is("AWS::S3::Bucket", 2)
    template.resource_count_is("AWS::Logs::LogGroup", 1)
    template.resource_count_is("AWS::CloudTrail::Trail", 1)


def test_cloudtrail_has_exactly_one_trail_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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


def test_cloudtrail_is_multi_region_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    for trail_id, trail in trail_resources.items():
        properties = trail.get("Properties", {})
        assert properties.get("IsMultiRegionTrail") is True, "CloudTrail should be multi-region"


def test_cloudtrail_includes_global_service_events_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    for trail_id, trail in trail_resources.items():
        properties = trail.get("Properties", {})
        assert properties.get("IncludeGlobalServiceEvents") is True, "CloudTrail should include global service events"


def test_cloudtrail_trail_exists_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    cloudtrail_resources = template.find_resources("AWS::CloudTrail::Trail")
    assert len(cloudtrail_resources) > 0, "CloudTrail trail should exist"


def test_domain_registration_custom_resource_exists_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
    assert len(custom_resources) > 0, "Custom resource for domain registration should exist"


def test_domain_registration_depends_on_cloudtrail_in_template():
    app = cdk.App()

    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[4] / "src" / "cloudtrail_and_domain_name" / "stack.py"
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
