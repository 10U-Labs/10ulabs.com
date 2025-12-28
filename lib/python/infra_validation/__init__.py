"""Infrastructure validation for AWS resources."""
import logging
import os
from typing import Any, Dict, List

from botocore.exceptions import ClientError

from aws_clients import get_ec2_client, get_ssm_client

logger = logging.getLogger()

_api_key_cache: Dict[str, str] = {'value': ''}
_dependencies_validated: Dict[str, Any] = {'checked': False, 'valid': False, 'errors': []}


def reset_api_key_cache():
    """Clear the API key cache for testing purposes."""
    _api_key_cache['value'] = ''


def get_api_key() -> str:
    """Get the API key from SSM Parameter Store, with caching."""
    api_key = _api_key_cache['value']
    if api_key:
        return api_key
    parameter_name = os.environ.get('API_KEY_PARAMETER_NAME', '')
    if not parameter_name:
        logger.error("API_KEY_PARAMETER_NAME not set")
        return ''
    ssm = get_ssm_client()
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    api_key = response['Parameter']['Value']
    _api_key_cache['value'] = api_key
    return api_key


def validate_security_groups(security_group_ids: List[str]) -> Dict[str, Any]:
    """Validate that security groups exist in AWS."""
    if not security_group_ids:
        return {'valid': True, 'missing': []}
    try:
        response = get_ec2_client().describe_security_groups(GroupIds=security_group_ids)
        found_ids = {sg['GroupId'] for sg in response.get('SecurityGroups', [])}
        missing = [sg_id for sg_id in security_group_ids if sg_id not in found_ids]
        return {'valid': len(missing) == 0, 'missing': missing}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidGroup.NotFound':
            return {'valid': False, 'missing': security_group_ids, 'error': str(e)}
        return {'valid': False, 'missing': [], 'error': str(e)}


def validate_subnets(subnet_ids: List[str]) -> Dict[str, Any]:
    """Validate that subnets exist in AWS."""
    if not subnet_ids:
        return {'valid': True, 'missing': []}
    try:
        response = get_ec2_client().describe_subnets(SubnetIds=subnet_ids)
        found_ids = {subnet['SubnetId'] for subnet in response.get('Subnets', [])}
        missing = [subnet_id for subnet_id in subnet_ids if subnet_id not in found_ids]
        return {'valid': len(missing) == 0, 'missing': missing}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidSubnetID.NotFound':
            return {'valid': False, 'missing': subnet_ids, 'error': str(e)}
        return {'valid': False, 'missing': [], 'error': str(e)}


def validate_vpc(vpc_id: str | None) -> Dict[str, Any]:
    """Validate that a VPC exists in AWS."""
    if not vpc_id:
        return {'valid': False, 'error': 'VPC ID not configured'}
    try:
        response = get_ec2_client().describe_vpcs(VpcIds=[vpc_id])
        found = len(response.get('Vpcs', [])) > 0
        return {'valid': found, 'error': None if found else f'VPC {vpc_id} not found'}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidVpcID.NotFound':
            return {'valid': False, 'error': f'VPC {vpc_id} not found'}
        return {'valid': False, 'error': str(e)}


def validate_all_dependencies() -> Dict[str, Any]:
    """Validate all infrastructure dependencies (SGs, subnets, VPC)."""
    errors = []
    security_groups_env = os.environ.get('SECURITY_GROUPS')
    security_group_ids = security_groups_env.split(',') if security_groups_env else []
    security_group_ids = [sg.strip() for sg in security_group_ids if sg.strip()]
    sg_result = validate_security_groups(security_group_ids)
    if not sg_result['valid']:
        errors.append({'type': 'security_group', 'details': sg_result})

    subnets_env = os.environ.get('SUBNETS')
    subnet_ids = subnets_env.split(',') if subnets_env else []
    subnet_ids = [s.strip() for s in subnet_ids if s.strip()]
    subnet_result = validate_subnets(subnet_ids)
    if not subnet_result['valid']:
        errors.append({'type': 'subnet', 'details': subnet_result})

    vpc_id = os.environ.get('VPC_ID')
    vpc_result = validate_vpc(vpc_id)
    if not vpc_result['valid']:
        errors.append({'type': 'vpc', 'details': vpc_result})

    all_valid = len(errors) == 0
    return {
        'valid': all_valid,
        'errors': errors,
        'checked_resources': {
            'security_groups': security_group_ids,
            'subnets': subnet_ids,
            'vpc': vpc_id
        }
    }


def ensure_dependencies_valid():
    """Ensure infrastructure dependencies are valid, raising if not."""
    if _dependencies_validated['checked']:
        if not _dependencies_validated['valid']:
            errors = _dependencies_validated['errors']
            raise RuntimeError(f"Infrastructure dependencies are invalid: {errors}")
        return

    result = validate_all_dependencies()
    _dependencies_validated['checked'] = True
    _dependencies_validated['valid'] = result['valid']
    _dependencies_validated['errors'] = result['errors']

    if not result['valid']:
        logger.error("Infrastructure dependency validation failed: %s", result['errors'])
        raise RuntimeError(f"Infrastructure dependencies are invalid: {result['errors']}")

    logger.info("Infrastructure dependencies validated successfully")


def reset_dependency_validation():
    """Reset the dependency validation cache."""
    _dependencies_validated['checked'] = False
    _dependencies_validated['valid'] = False
    _dependencies_validated['errors'] = []


def get_dependencies_status():
    """Get the current dependency validation status."""
    return {
        'checked': _dependencies_validated['checked'],
        'valid': _dependencies_validated['valid'],
        'errors': list(_dependencies_validated['errors'])
    }


def set_dependencies_status(checked, valid, errors):
    """Set the dependency validation status for testing."""
    _dependencies_validated['checked'] = checked
    _dependencies_validated['valid'] = valid
    _dependencies_validated['errors'] = errors
