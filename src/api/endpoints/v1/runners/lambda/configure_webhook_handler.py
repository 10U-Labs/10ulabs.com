import json
import logging
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {'ssm': None}


def get_ssm_client():
    if _clients['ssm'] is None:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_github_pat() -> str:
    parameter_name = os.environ.get('GITHUB_PAT_SECRET_NAME', '/github-runner/credentials')
    try:
        client = get_ssm_client()
        response = client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        logger.error("Failed to retrieve GitHub PAT: %s", e)
        return ''


def get_or_create_webhook_secret() -> str:
    parameter_name = os.environ.get('WEBHOOK_SECRET_NAME', '/api-webhook-secret')
    client = get_ssm_client()

    try:
        response = client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except client.exceptions.ParameterNotFound:
        new_secret = secrets.token_urlsafe(32)
        client.put_parameter(
            Name=parameter_name,
            Value=new_secret,
            Description='GitHub webhook secret for runners endpoint',
            Type='String',
            Tier='Standard'
        )
        logger.info("Created new webhook secret: %s", parameter_name)
        return new_secret
    except ClientError as e:
        logger.error("Failed to get or create webhook secret: %s", e)
        return ''


def list_github_webhooks(
        github_pat: str,
        repo: str
) -> Dict[str, Any]:
    api_endpoint = f'https://api.github.com/repos/{repo}/hooks'

    headers = {
        'Authorization': f'token {github_pat}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        req = urllib.request.Request(
            api_endpoint,
            headers=headers,
            method='GET'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            webhooks = json.loads(response.read())
            return {'success': True, 'webhooks': webhooks}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No error body'
        logger.error("Failed to list webhooks: %s - %s", e.code, error_body)
        return {'success': False, 'error': f'HTTP {e.code}: {error_body}'}
    except (urllib.error.URLError, ValueError) as e:
        logger.error("Failed to list webhooks: %s", e)
        return {'success': False, 'error': str(e)}


def handle_duplicate_webhook(webhook_url: str, github_pat: str, repo: str) -> Dict[str, Any]:
    list_result = list_github_webhooks(github_pat, repo)
    if not list_result['success']:
        return {'success': False, 'error': f'Duplicate exists, list failed: {list_result.get("error")}'}

    for hook in list_result['webhooks']:
        hook_url = hook.get('config', {}).get('url', '')
        if hook_url == webhook_url:
            webhook_id = hook.get('id')
            logger.info("Found existing webhook with ID: %s", webhook_id)
            return {'success': True, 'webhook_id': webhook_id}

    return {'success': False, 'error': 'Duplicate webhook exists but URL not found'}


def create_github_webhook(webhook_url: str, webhook_secret: str, github_pat: str, repo: str) -> Dict[str, Any]:
    api_endpoint = f'https://api.github.com/repos/{repo}/hooks'
    payload = {'name': 'web', 'active': True, 'events': ['workflow_job'], 'config': {'url': webhook_url, 'content_type': 'application/json', 'secret': webhook_secret, 'insecure_ssl': '0'}}
    headers = {'Authorization': f'token {github_pat}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'}

    for attempt in range(4):
        try:
            req = urllib.request.Request(api_endpoint, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read())
                logger.info("Created webhook with ID: %s on attempt %d", response_data.get('id'), attempt + 1)
                return {'success': True, 'webhook_id': response_data.get('id')}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else 'No error body'
            if e.code == 422 and 'hook already exists' in error_body.lower():
                logger.warning("Webhook already exists, attempting to retrieve existing webhook ID")
                return handle_duplicate_webhook(webhook_url, github_pat, repo)
            if 400 <= e.code < 500:
                logger.error("Client error creating webhook (HTTP %d), not retrying", e.code)
                return {'success': False, 'error': f'HTTP {e.code}: {error_body}'}
            if attempt < 3:
                time.sleep(1.0 * (2 ** attempt))
            else:
                logger.error("Failed to create webhook after 4 attempts (HTTP %d)", e.code)
                return {'success': False, 'error': f'HTTP {e.code} after 4 attempts'}
        except (urllib.error.URLError, ValueError) as e:
            if attempt < 3:
                time.sleep(1.0 * (2 ** attempt))
            else:
                logger.error("Failed to create webhook after 4 attempts: %s", e)
                return {'success': False, 'error': f'{str(e)} after 4 attempts'}
    return {'success': False, 'error': 'Max retries exceeded'}


def delete_github_webhook(
        webhook_id: int,
        github_pat: str,
        repo: str
) -> Dict[str, Any]:
    api_endpoint = f'https://api.github.com/repos/{repo}/hooks/{webhook_id}'

    headers = {
        'Authorization': f'token {github_pat}',
        'Accept': 'application/vnd.github.v3+json'
    }

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(
                api_endpoint,
                headers=headers,
                method='DELETE'
            )

            with urllib.request.urlopen(req, timeout=30):
                logger.info("Deleted webhook with ID: %s on attempt %d", webhook_id, attempt + 1)
                return {'success': True}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning(
                    "Webhook %s not found (may already be deleted)",
                    webhook_id
                )
                return {'success': True}

            if 400 <= e.code < 500:
                error_body = e.read().decode('utf-8') if e.fp else 'No error body'
                logger.error("Client error deleting webhook (HTTP %d), not retrying", e.code)
                return {'success': False, 'error': f'HTTP {e.code}: {error_body}'}

            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning("Server error deleting webhook (HTTP %d), retry %d/%d after %ds", e.code, attempt + 1, max_retries, delay)
                time.sleep(delay)
            else:
                error_body = e.read().decode('utf-8') if e.fp else 'No error body'
                logger.error("Failed to delete webhook after %d attempts (HTTP %d)", max_retries + 1, e.code)
                return {'success': False, 'error': f'HTTP {e.code} after {max_retries + 1} attempts'}
        except (urllib.error.URLError, ValueError) as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning("Error deleting webhook, retry %d/%d after %ds: %s", attempt + 1, max_retries, delay, e)
                time.sleep(delay)
            else:
                logger.error("Failed to delete webhook after %d attempts: %s", max_retries + 1, e)
                return {'success': False, 'error': f'{str(e)} after {max_retries + 1} attempts'}

    return {'success': False, 'error': 'Max retries exceeded'}


def send_response(
        event: Dict[str, Any],
        status: str,
        reason: str,
        physical_resource_id: str,
        data: Dict[str, Any]
):
    response_body = {
        'Status': status,
        'Reason': reason,
        'PhysicalResourceId': physical_resource_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': data
    }

    headers = {'Content-Type': 'application/json'}

    try:
        req = urllib.request.Request(
            event['ResponseURL'],
            data=json.dumps(response_body).encode('utf-8'),
            headers=headers,
            method='PUT'
        )

        with urllib.request.urlopen(req, timeout=30):
            logger.info("Sent %s response to CloudFormation", status)
            return True
    except (urllib.error.URLError, ValueError) as e:
        logger.error("Failed to send response to CloudFormation: %s", e)
        return False


def handle_delete_request(event: dict, repo: str) -> dict:
    webhook_id_str = event['ResourceProperties'].get('WebhookId', '')
    if not webhook_id_str:
        return {
            'status_code': 200,
            'response_body': {'message': 'No webhook to delete'},
            'cf_status': 'SUCCESS',
            'cf_reason': 'No webhook to delete',
            'cf_data': {}
        }

    github_pat = get_github_pat()
    if not github_pat:
        return {
            'status_code': 500,
            'response_body': {'error': 'Failed to get GitHub PAT'},
            'cf_status': 'FAILED',
            'cf_reason': 'Failed to get GitHub PAT',
            'cf_data': {}
        }

    result = delete_github_webhook(int(webhook_id_str), github_pat, repo)
    if result['success']:
        return {
            'status_code': 200,
            'response_body': {'message': 'Webhook deleted'},
            'cf_status': 'SUCCESS',
            'cf_reason': 'Webhook deleted',
            'cf_data': {}
        }
    return {
        'status_code': 500,
        'response_body': {'error': result.get('error')},
        'cf_status': 'FAILED',
        'cf_reason': result.get('error', 'Unknown error'),
        'cf_data': {}
    }


def handle_create_update_request(webhook_url: str, repo: str) -> dict:
    github_pat = get_github_pat()
    webhook_secret = get_or_create_webhook_secret()

    if not github_pat or not webhook_secret:
        return {
            'status_code': 500,
            'response_body': {'error': 'Failed to retrieve secrets'},
            'cf_status': 'FAILED',
            'cf_reason': 'Failed to retrieve secrets',
            'cf_data': {}
        }

    result = create_github_webhook(webhook_url, webhook_secret, github_pat, repo)
    if result['success']:
        return {
            'status_code': 200,
            'response_body': {'message': 'Webhook configured', 'webhook_id': result['webhook_id']},
            'cf_status': 'SUCCESS',
            'cf_reason': 'Webhook configured',
            'cf_data': {'WebhookId': str(result['webhook_id']), 'WebhookUrl': webhook_url}
        }
    return {
        'status_code': 500,
        'response_body': {'error': result.get('error')},
        'cf_status': 'FAILED',
        'cf_reason': result.get('error', 'Unknown error'),
        'cf_data': {}
    }


def lambda_handler(event, _context):
    logger.info("Received event: %s", json.dumps(event))

    request_type = event['RequestType']
    webhook_url = event['ResourceProperties'].get('WebhookUrl', '')
    repo = event['ResourceProperties'].get('Repository', '')
    resource_id = event.get('PhysicalResourceId', f'github-webhook-{repo.replace("/", "-")}')

    if request_type == 'Delete':
        result = handle_delete_request(event, repo)
    elif request_type in ['Create', 'Update']:
        result = handle_create_update_request(webhook_url, repo)
    else:
        result = {
            'status_code': 400,
            'response_body': {'error': f'Unsupported request type: {request_type}'},
            'cf_status': 'FAILED',
            'cf_reason': f'Unsupported request type: {request_type}',
            'cf_data': {}
        }

    send_response(event, result['cf_status'], result['cf_reason'], resource_id, result['cf_data'])
    return {'statusCode': result['status_code'], 'body': json.dumps(result['response_body'])}
