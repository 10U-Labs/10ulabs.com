import json
from unittest.mock import MagicMock
from botocore.exceptions import ClientError


class TestValidateSecurityGroupsReturnsValid:

    def test_returns_valid_when_security_group_exists(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123'}]
        }
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_security_groups(['sg-123'])

        assert result['valid'] is True

    def test_returns_empty_missing_when_security_group_exists(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123'}]
        }
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_security_groups(['sg-123'])

        assert result['missing'] == []

    def test_returns_valid_when_empty_list_provided(self, v1_handler):
        result = v1_handler.validate_security_groups([])

        assert result['valid'] is True


class TestValidateSecurityGroupsReturnsInvalid:

    def test_returns_invalid_when_security_group_not_found(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_security_groups(['sg-missing'])

        assert result['valid'] is False

    def test_returns_missing_list_when_security_group_not_found(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_security_groups(['sg-missing'])

        assert result['missing'] == ['sg-missing']

    def test_returns_invalid_on_other_client_error(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeSecurityGroups'
        )
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_security_groups(['sg-123'])

        assert result['valid'] is False


class TestValidateSubnetsReturnsValid:

    def test_returns_valid_when_subnet_exists(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'SubnetId': 'subnet-123'}]
        }
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_subnets(['subnet-123'])

        assert result['valid'] is True

    def test_returns_empty_missing_when_subnet_exists(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'SubnetId': 'subnet-123'}]
        }
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_subnets(['subnet-123'])

        assert result['missing'] == []

    def test_returns_valid_when_empty_list_provided(self, v1_handler):
        result = v1_handler.validate_subnets([])

        assert result['valid'] is True


class TestValidateSubnetsReturnsInvalid:

    def test_returns_invalid_when_subnet_not_found(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {'Error': {'Code': 'InvalidSubnetID.NotFound', 'Message': 'Not found'}},
            'DescribeSubnets'
        )
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_subnets(['subnet-missing'])

        assert result['valid'] is False

    def test_returns_missing_list_when_subnet_not_found(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {'Error': {'Code': 'InvalidSubnetID.NotFound', 'Message': 'Not found'}},
            'DescribeSubnets'
        )
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_subnets(['subnet-missing'])

        assert result['missing'] == ['subnet-missing']


class TestValidateVpcReturnsValid:

    def test_returns_valid_when_vpc_exists(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {
            'Vpcs': [{'VpcId': 'vpc-123'}]
        }
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_vpc('vpc-123')

        assert result['valid'] is True

    def test_returns_no_error_when_vpc_exists(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {
            'Vpcs': [{'VpcId': 'vpc-123'}]
        }
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_vpc('vpc-123')

        assert result['error'] is None


class TestValidateVpcReturnsInvalid:

    def test_returns_invalid_when_vpc_not_found(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {'Error': {'Code': 'InvalidVpcID.NotFound', 'Message': 'Not found'}},
            'DescribeVpcs'
        )
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_vpc('vpc-missing')

        assert result['valid'] is False

    def test_returns_error_when_vpc_not_found(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {'Error': {'Code': 'InvalidVpcID.NotFound', 'Message': 'Not found'}},
            'DescribeVpcs'
        )
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_vpc('vpc-missing')

        assert 'vpc-missing' in result['error']

    def test_returns_invalid_when_vpc_not_configured(self, v1_handler):
        result = v1_handler.validate_vpc('')

        assert result['valid'] is False


class TestValidateAllDependencies:

    def test_returns_valid_when_all_dependencies_exist(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_all_dependencies()

        assert result['valid'] is True

    def test_returns_empty_errors_when_all_dependencies_exist(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_all_dependencies()

        assert result['errors'] == []

    def test_returns_invalid_when_security_group_missing(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_all_dependencies()

        assert result['valid'] is False

    def test_returns_error_details_when_security_group_missing(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_all_dependencies()

        assert result['errors'][0]['type'] == 'security_group'

    def test_returns_checked_resources(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        result = v1_handler.validate_all_dependencies()

        assert 'checked_resources' in result


class TestEnsureDependenciesValid:

    def test_raises_runtime_error_when_dependencies_invalid(self, v1_handler):
        v1_handler.reset_dependency_validation()
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        try:
            v1_handler.ensure_dependencies_valid()
            raised = False
        except RuntimeError:
            raised = True

        assert raised is True

    def test_does_not_raise_when_dependencies_valid(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        try:
            v1_handler.ensure_dependencies_valid()
            raised = False
        except RuntimeError:
            raised = True

        assert raised is False

    def test_caches_validation_result(self, v1_handler):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)
        v1_handler.ensure_dependencies_valid()
        mock_ec2.describe_security_groups.reset_mock()

        v1_handler.ensure_dependencies_valid()

        mock_ec2.describe_security_groups.assert_not_called()

    def test_raises_on_second_call_if_invalid(self, v1_handler):
        v1_handler.reset_dependency_validation()
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)
        try:
            v1_handler.ensure_dependencies_valid()
        except RuntimeError:
            pass
        mock_ec2.describe_security_groups.reset_mock()

        try:
            v1_handler.ensure_dependencies_valid()
            raised = False
        except RuntimeError:
            raised = True

        assert raised is True


class TestResetDependencyValidation:

    def test_clears_checked_flag(self, v1_handler):
        v1_handler.set_dependencies_status(True, True, [])

        v1_handler.reset_dependency_validation()

        assert v1_handler.get_dependencies_status()['checked'] is False

    def test_clears_valid_flag(self, v1_handler):
        v1_handler.set_dependencies_status(True, True, [])

        v1_handler.reset_dependency_validation()

        assert v1_handler.get_dependencies_status()['valid'] is False

    def test_clears_errors_list(self, v1_handler):
        v1_handler.set_dependencies_status(True, True, [{'type': 'test'}])

        v1_handler.reset_dependency_validation()

        assert v1_handler.get_dependencies_status()['errors'] == []


class TestHandleDependenciesHealthReturnsHealthy:

    def test_returns_200_when_dependencies_valid(self, v1_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        response = v1_handler.lambda_handler(health_dependencies_get_event, lambda_context)

        assert response['statusCode'] == 200

    def test_returns_healthy_status_when_dependencies_valid(self, v1_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {'SecurityGroups': [{'GroupId': 'sg-test'}]}
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        response = v1_handler.lambda_handler(health_dependencies_get_event, lambda_context)
        body = json.loads(response['body'])

        assert body['status'] == 'healthy'


class TestHandleDependenciesHealthReturnsUnhealthy:

    def test_returns_503_when_security_group_missing(self, v1_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        response = v1_handler.lambda_handler(health_dependencies_get_event, lambda_context)

        assert response['statusCode'] == 503

    def test_returns_unhealthy_status_when_security_group_missing(self, v1_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        response = v1_handler.lambda_handler(health_dependencies_get_event, lambda_context)
        body = json.loads(response['body'])

        assert body['status'] == 'unhealthy'

    def test_returns_errors_when_security_group_missing(self, v1_handler, lambda_context, health_dependencies_get_event):
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
            'DescribeSecurityGroups'
        )
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]}
        mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
        v1_handler.set_client('ec2', mock_ec2)

        response = v1_handler.lambda_handler(health_dependencies_get_event, lambda_context)
        body = json.loads(response['body'])

        assert len(body['errors']) > 0
