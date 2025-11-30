import json
import os
from typing import Any, Dict, List
import boto3
from botocore.exceptions import ClientError

_clients: Dict[str, Any] = {}


def get_ec2_client():
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def set_client(name: str, client: Any):
    _clients[name] = client


def validate_security_groups(security_group_ids: List[str]) -> Dict[str, Any]:
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


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }


def handle_health(_event: Dict[str, Any]) -> Dict[str, Any]:
    status_data = {
        'status': 'healthy',
        'service': '10U Labs API',
        'version': '1.0.0'
    }
    return json_response(200, status_data)


def handle_dependencies_health(_event: Dict[str, Any]) -> Dict[str, Any]:
    result = validate_all_dependencies()
    if result['valid']:
        response = json_response(200, {
            'status': 'healthy',
            'message': 'All infrastructure dependencies are valid',
            'checked_resources': result['checked_resources']
        })
    else:
        response = json_response(503, {
            'status': 'unhealthy',
            'message': 'Infrastructure dependencies are invalid',
            'errors': result['errors'],
            'checked_resources': result['checked_resources']
        })
    return response


ROUTE_MAP = {
    ('/health', 'GET'): handle_health,
    ('/health/dependencies', 'GET'): handle_dependencies_health,
}


def handler(event, _context):
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    route_key = (path, method)
    route_handler = ROUTE_MAP.get(route_key)
    if route_handler:
        response = route_handler(event)
    else:
        response = json_response(404, {'error': 'Not found'})
    return response
