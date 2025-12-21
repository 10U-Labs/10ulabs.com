"""Unit tests for health endpoint dependency validation."""
import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError


class TestValidateSecurityGroupsReturnsValid:
    """Tests for validate_security_groups returning valid."""

    def test_returns_valid_when_security_group_exists(self, health_handler):
        """Verify valid when security group exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-123'])

        assert result['valid'] is True

    def test_returns_empty_missing_when_security_group_exists(self, health_handler):
        """Verify empty missing list when security group exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-123'])

        assert result['missing'] == []

    def test_returns_valid_when_empty_list_provided(self, health_handler):
        """Verify valid when empty list provided."""
        result = health_handler.validate_security_groups([])

        assert result['valid'] is True


class TestValidateSecurityGroupsReturnsInvalid:
    """Tests for validate_security_groups returning invalid."""

    def test_returns_invalid_when_security_group_not_found(
        self, health_handler, mock_ec2_sg_not_found
    ):
        """Verify invalid when security group not found."""
        health_handler.set_client('ec2', mock_ec2_sg_not_found)

        result = health_handler.validate_security_groups(['sg-missing'])

        assert result['valid'] is False

    def test_returns_missing_list_when_security_group_not_found(
        self, health_handler, mock_ec2_sg_not_found
    ):
        """Verify missing list contains ID when not found."""
        health_handler.set_client('ec2', mock_ec2_sg_not_found)

        result = health_handler.validate_security_groups(['sg-missing'])

        assert result['missing'] == ['sg-missing']

    def test_returns_invalid_on_other_client_error(self, health_handler):
        """Verify invalid on other ClientError."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeSecurityGroups'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-123'])

        assert result['valid'] is False


class TestValidateSubnetsReturnsValid:
    """Tests for validate_subnets returning valid."""

    def test_returns_valid_when_subnet_exists(self, health_handler):
        """Verify valid when subnet exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'SubnetId': 'subnet-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_subnets(['subnet-123'])

        assert result['valid'] is True

    def test_returns_empty_missing_when_subnet_exists(self, health_handler):
        """Verify empty missing list when subnet exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'SubnetId': 'subnet-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_subnets(['subnet-123'])

        assert result['missing'] == []

    def test_returns_valid_when_empty_list_provided(self, health_handler):
        """Verify valid when empty list provided."""
        result = health_handler.validate_subnets([])

        assert result['valid'] is True


class TestValidateSubnetsReturnsInvalid:
    """Tests for validate_subnets returning invalid."""

    def test_returns_invalid_when_subnet_not_found(
        self, health_handler, mock_ec2_subnet_not_found
    ):
        """Verify invalid when subnet not found."""
        health_handler.set_client('ec2', mock_ec2_subnet_not_found)

        result = health_handler.validate_subnets(['subnet-missing'])

        assert result['valid'] is False

    def test_returns_missing_list_when_subnet_not_found(
        self, health_handler, mock_ec2_subnet_not_found
    ):
        """Verify missing list contains ID when not found."""
        health_handler.set_client('ec2', mock_ec2_subnet_not_found)

        result = health_handler.validate_subnets(['subnet-missing'])

        assert result['missing'] == ['subnet-missing']


class TestValidateVpcReturnsValid:
    """Tests for validate_vpc returning valid."""

    def test_returns_valid_when_vpc_exists(self, health_handler):
        """Verify valid when VPC exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {
            'Vpcs': [{'VpcId': 'vpc-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-123')

        assert result['valid'] is True

    def test_returns_no_error_when_vpc_exists(self, health_handler):
        """Verify no error when VPC exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {
            'Vpcs': [{'VpcId': 'vpc-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-123')

        assert result['error'] is None


class TestValidateVpcReturnsInvalid:
    """Tests for validate_vpc returning invalid."""

    def test_returns_invalid_when_vpc_not_found(self, health_handler):
        """Verify invalid when VPC not found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {'Error': {'Code': 'InvalidVpcID.NotFound', 'Message': 'Not found'}},
            'DescribeVpcs'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-missing')

        assert result['valid'] is False

    def test_returns_error_when_vpc_not_found(self, health_handler):
        """Verify error message when VPC not found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {'Error': {'Code': 'InvalidVpcID.NotFound', 'Message': 'Not found'}},
            'DescribeVpcs'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-missing')

        assert 'vpc-missing' in result['error']

    def test_returns_invalid_when_vpc_not_configured(self, health_handler):
        """Verify invalid when VPC not configured."""
        result = health_handler.validate_vpc('')

        assert result['valid'] is False


@pytest.mark.usefixtures('patched_dependency_env')
class TestValidateAllDependencies:
    """Tests for validate_all_dependencies."""

    def test_returns_valid_when_all_dependencies_exist(
        self, health_handler, mock_ec2_valid_deps
    ):
        """Verify valid when all dependencies exist."""
        health_handler.set_client('ec2', mock_ec2_valid_deps)

        result = health_handler.validate_all_dependencies()

        assert result['valid'] is True

    def test_returns_empty_errors_when_all_dependencies_exist(
        self, health_handler, mock_ec2_valid_deps
    ):
        """Verify empty errors when all dependencies exist."""
        health_handler.set_client('ec2', mock_ec2_valid_deps)

        result = health_handler.validate_all_dependencies()

        assert result['errors'] == []

    def test_returns_invalid_when_security_group_missing(
        self, health_handler, mock_ec2_missing_sg
    ):
        """Verify invalid when security group missing."""
        health_handler.set_client('ec2', mock_ec2_missing_sg)

        result = health_handler.validate_all_dependencies()

        assert result['valid'] is False

    def test_returns_error_details_when_security_group_missing(
        self, health_handler, mock_ec2_missing_sg
    ):
        """Verify error details when security group missing."""
        health_handler.set_client('ec2', mock_ec2_missing_sg)

        result = health_handler.validate_all_dependencies()

        assert result['errors'][0]['type'] == 'security_group'

    def test_returns_checked_resources(
        self, health_handler, mock_ec2_valid_deps
    ):
        """Verify checked_resources returned."""
        health_handler.set_client('ec2', mock_ec2_valid_deps)

        result = health_handler.validate_all_dependencies()

        assert 'checked_resources' in result


@pytest.mark.usefixtures('patched_dependency_env')
class TestHandleDependenciesHealthReturnsHealthy:
    """Tests for handle_dependencies_health returning healthy."""

    def test_returns_200_when_dependencies_valid(
        self, health_handler, lambda_context, health_dependencies_get_event,
        mock_ec2_valid_deps
    ):
        """Verify HTTP 200 when dependencies valid."""
        health_handler.set_client('ec2', mock_ec2_valid_deps)

        response = health_handler.handler(
            health_dependencies_get_event, lambda_context
        )

        assert response['statusCode'] == 200

    def test_returns_healthy_status_when_dependencies_valid(
        self, health_handler, lambda_context, health_dependencies_get_event,
        mock_ec2_valid_deps
    ):
        """Verify healthy status when dependencies valid."""
        health_handler.set_client('ec2', mock_ec2_valid_deps)

        response = health_handler.handler(
            health_dependencies_get_event, lambda_context
        )
        body = json.loads(response['body'])

        assert body['status'] == 'healthy'


@pytest.mark.usefixtures('patched_dependency_env')
class TestHandleDependenciesHealthReturnsUnhealthy:
    """Tests for handle_dependencies_health returning unhealthy."""

    def test_returns_503_when_security_group_missing(
        self, health_handler, lambda_context, health_dependencies_get_event,
        mock_ec2_missing_sg
    ):
        """Verify HTTP 503 when security group missing."""
        health_handler.set_client('ec2', mock_ec2_missing_sg)

        response = health_handler.handler(
            health_dependencies_get_event, lambda_context
        )

        assert response['statusCode'] == 503

    def test_returns_unhealthy_status_when_security_group_missing(
        self, health_handler, lambda_context, health_dependencies_get_event,
        mock_ec2_missing_sg
    ):
        """Verify unhealthy status when security group missing."""
        health_handler.set_client('ec2', mock_ec2_missing_sg)

        response = health_handler.handler(
            health_dependencies_get_event, lambda_context
        )
        body = json.loads(response['body'])

        assert body['status'] == 'unhealthy'

    def test_returns_errors_when_security_group_missing(
        self, health_handler, lambda_context, health_dependencies_get_event,
        mock_ec2_missing_sg
    ):
        """Verify errors list when security group missing."""
        health_handler.set_client('ec2', mock_ec2_missing_sg)

        response = health_handler.handler(
            health_dependencies_get_event, lambda_context
        )
        body = json.loads(response['body'])

        assert len(body['errors']) > 0
