import json
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


class TestValidateSecurityGroupsReturnsValid:

    def test_returns_valid_when_security_group_exists(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-123'])

        assert result['valid'] is True

    def test_returns_empty_missing_when_security_group_exists(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-123'])

        assert result['missing'] == []

    def test_returns_valid_when_empty_list_provided(self, health_handler):
        result = health_handler.validate_security_groups([])

        assert result['valid'] is True


class TestValidateSecurityGroupsReturnsInvalid:

    def test_returns_invalid_when_security_group_not_found(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-missing'])

        assert result['valid'] is False

    def test_returns_missing_list_when_security_group_not_found(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-missing'])

        assert result['missing'] == ['sg-missing']

    def test_returns_invalid_on_other_client_error(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeSecurityGroups'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_security_groups(['sg-123'])

        assert result['valid'] is False


class TestValidateSubnetsReturnsValid:

    def test_returns_valid_when_subnet_exists(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'SubnetId': 'subnet-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_subnets(['subnet-123'])

        assert result['valid'] is True

    def test_returns_empty_missing_when_subnet_exists(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'SubnetId': 'subnet-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_subnets(['subnet-123'])

        assert result['missing'] == []

    def test_returns_valid_when_empty_list_provided(self, health_handler):
        result = health_handler.validate_subnets([])

        assert result['valid'] is True


class TestValidateSubnetsReturnsInvalid:

    def test_returns_invalid_when_subnet_not_found(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {'Error': {'Code': 'InvalidSubnetID.NotFound', 'Message': 'Not found'}},
            'DescribeSubnets'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_subnets(['subnet-missing'])

        assert result['valid'] is False

    def test_returns_missing_list_when_subnet_not_found(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {'Error': {'Code': 'InvalidSubnetID.NotFound', 'Message': 'Not found'}},
            'DescribeSubnets'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_subnets(['subnet-missing'])

        assert result['missing'] == ['subnet-missing']


class TestValidateVpcReturnsValid:

    def test_returns_valid_when_vpc_exists(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {
            'Vpcs': [{'VpcId': 'vpc-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-123')

        assert result['valid'] is True

    def test_returns_no_error_when_vpc_exists(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {
            'Vpcs': [{'VpcId': 'vpc-123'}]
        }
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-123')

        assert result['error'] is None


class TestValidateVpcReturnsInvalid:

    def test_returns_invalid_when_vpc_not_found(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {'Error': {'Code': 'InvalidVpcID.NotFound', 'Message': 'Not found'}},
            'DescribeVpcs'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-missing')

        assert result['valid'] is False

    def test_returns_error_when_vpc_not_found(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {'Error': {'Code': 'InvalidVpcID.NotFound', 'Message': 'Not found'}},
            'DescribeVpcs'
        )
        health_handler.set_client('ec2', mock_ec2)

        result = health_handler.validate_vpc('vpc-missing')

        assert 'vpc-missing' in result['error']

    def test_returns_invalid_when_vpc_not_configured(self, health_handler):
        result = health_handler.validate_vpc('')

        assert result['valid'] is False


class TestValidateAllDependencies:

    def test_returns_valid_when_all_dependencies_exist(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            result = health_handler.validate_all_dependencies()

        assert result['valid'] is True

    def test_returns_empty_errors_when_all_dependencies_exist(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            result = health_handler.validate_all_dependencies()

        assert result['errors'] == []

    def test_returns_invalid_when_security_group_missing(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            result = health_handler.validate_all_dependencies()

        assert result['valid'] is False

    def test_returns_error_details_when_security_group_missing(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            result = health_handler.validate_all_dependencies()

        assert result['errors'][0]['type'] == 'security_group'

    def test_returns_checked_resources(self, health_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            result = health_handler.validate_all_dependencies()

        assert 'checked_resources' in result


class TestHandleDependenciesHealthReturnsHealthy:

    def test_returns_200_when_dependencies_valid(self, health_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            response = health_handler.handler(health_dependencies_get_event, lambda_context)

        assert response['statusCode'] == 200

    def test_returns_healthy_status_when_dependencies_valid(self, health_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            response = health_handler.handler(health_dependencies_get_event, lambda_context)
        body = json.loads(response['body'])

        assert body['status'] == 'healthy'


class TestHandleDependenciesHealthReturnsUnhealthy:

    def test_returns_503_when_security_group_missing(self, health_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            response = health_handler.handler(health_dependencies_get_event, lambda_context)

        assert response['statusCode'] == 503

    def test_returns_unhealthy_status_when_security_group_missing(self, health_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            response = health_handler.handler(health_dependencies_get_event, lambda_context)
        body = json.loads(response['body'])

        assert body['status'] == 'unhealthy'

    def test_returns_errors_when_security_group_missing(self, health_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        health_handler.set_client('ec2', mock_ec2)
        env_vars = {
            'SECURITY_GROUPS': 'sg-test',
            'SUBNETS': 'subnet-test1,subnet-test2',
            'VPC_ID': 'vpc-test'
        }

        with patch.dict('os.environ', env_vars):
            response = health_handler.handler(health_dependencies_get_event, lambda_context)
        body = json.loads(response['body'])

        assert len(body['errors']) > 0
