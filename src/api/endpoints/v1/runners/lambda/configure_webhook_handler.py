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

_clients = {'secretsmanager': None}


def get_secretsmanager_client():
    if _clients['secretsmanager'] is None:
        _clients['secretsmanager'] = boto3.client('secretsmanager')
    return _clients['secretsmanager']


def get_github_pat() -> str:
    secret_name = os.environ.get('GITHUB_PAT_SECRET_NAME', 'github-pat')
    try:
        client = get_secretsmanager_client()
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        logger.error("Failed to retrieve GitHub PAT: %s", e)
        return ''


def get_or_create_webhook_secret() -> str:
    secret_name = os.environ.get('WEBHOOK_SECRET_NAME', 'api-webhook-secret')
    client = get_secretsmanager_client()

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except client.exceptions.ResourceNotFoundException:
        new_secret = secrets.token_urlsafe(32)
        client.create_secret(
            Name=secret_name,
            SecretString=new_secret,
            Description='GitHub webhook secret for runners endpoint'
        )
        logger.info("Created new webhook secret: %s", secret_name)
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


def create_github_webhook(
        webhook_url: str,
        webhook_secret: str,
        github_pat: str,
        repo: str
) -> Dict[str, Any]:
    api_endpoint = f'https://api.github.com/repos/{repo}/hooks'

    payload = {
        'name': 'web',
        'active': True,
        'events': ['workflow_job'],
        'config': {
            'url': webhook_url,
            'content_type': 'application/json',
            'secret': webhook_secret,
            'insecure_ssl': '0'
        }
    }

    headers = {
        'Authorization': f'token {github_pat}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(
                api_endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read())
                logger.info("Created webhook with ID: %s on attempt %d", response_data.get('id'), attempt + 1)
                return {'success': True, 'webhook_id': response_data.get('id')}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else 'No error body'

            if e.code == 422 and 'hook already exists' in error_body.lower():
                logger.warning("Webhook already exists, attempting to retrieve existing webhook ID")
                list_result = list_github_webhooks(github_pat, repo)

                if list_result['success']:
                    for hook in list_result['webhooks']:
                        hook_url = hook.get('config', {}).get('url', '')
                        if hook_url == webhook_url:
                            webhook_id = hook.get('id')
                            logger.info("Found existing webhook with ID: %s", webhook_id)
                            return {'success': True, 'webhook_id': webhook_id}

                    logger.error("Duplicate webhook exists but could not find matching URL")
                    return {'success': False, 'error': 'Duplicate webhook exists but URL not found'}

                logger.error("Failed to list webhooks after duplicate detection")
                return {'success': False, 'error': f'Duplicate exists, list failed: {list_result.get("error")}'}

            if 400 <= e.code < 500:
                logger.error("Client error creating webhook (HTTP %d), not retrying", e.code)
                return {'success': False, 'error': f'HTTP {e.code}: {error_body}'}

            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning("Server error creating webhook (HTTP %d), retry %d/%d after %ds", e.code, attempt + 1, max_retries, delay)
                time.sleep(delay)
            else:
                logger.error("Failed to create webhook after %d attempts (HTTP %d)", max_retries + 1, e.code)
                return {'success': False, 'error': f'HTTP {e.code} after {max_retries + 1} attempts'}
        except (urllib.error.URLError, ValueError) as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning("Error creating webhook, retry %d/%d after %ds: %s", attempt + 1, max_retries, delay, e)
                time.sleep(delay)
            else:
                logger.error("Failed to create webhook after %d attempts: %s", max_retries + 1, e)
                return {'success': False, 'error': f'{str(e)} after {max_retries + 1} attempts'}

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


def lambda_handler(event, _context):
    logger.info("Received event: %s", json.dumps(event))

    request_type = event['RequestType']
    webhook_url = event['ResourceProperties'].get('WebhookUrl', '')
    repo = event['ResourceProperties'].get('Repository', '')

    resource_id = event.get(
        'PhysicalResourceId',
        f'github-webhook-{repo.replace("/", "-")}'
    )

    status_code = 200
    response_body = {}
    cf_status = 'SUCCESS'
    cf_reason = ''
    cf_data = {}

    if request_type == 'Delete':
        webhook_id_str = event['ResourceProperties'].get('WebhookId', '')
        if webhook_id_str:
            github_pat = get_github_pat()
            if github_pat:
                result = delete_github_webhook(
                    int(webhook_id_str),
                    github_pat,
                    repo
                )
                if result['success']:
                    cf_reason = 'Webhook deleted'
                    response_body = {'message': 'Webhook deleted'}
                else:
                    status_code = 500
                    cf_status = 'FAILED'
                    cf_reason = result.get('error', 'Unknown error')
                    response_body = {'error': result.get('error')}
            else:
                status_code = 500
                cf_status = 'FAILED'
                cf_reason = 'Failed to get GitHub PAT'
                response_body = {'error': 'Failed to get GitHub PAT'}
        else:
            cf_reason = 'No webhook to delete'
            response_body = {'message': 'No webhook to delete'}
    elif request_type in ['Create', 'Update']:
        github_pat = get_github_pat()
        webhook_secret = get_or_create_webhook_secret()

        if not github_pat or not webhook_secret:
            status_code = 500
            cf_status = 'FAILED'
            cf_reason = 'Failed to retrieve secrets'
            response_body = {'error': 'Failed to retrieve secrets'}
        else:
            result = create_github_webhook(
                webhook_url,
                webhook_secret,
                github_pat,
                repo
            )

            if result['success']:
                cf_reason = 'Webhook configured'
                cf_data = {
                    'WebhookId': str(result['webhook_id']),
                    'WebhookUrl': webhook_url
                }
                response_body = {
                    'message': 'Webhook configured',
                    'webhook_id': result['webhook_id']
                }
            else:
                status_code = 500
                cf_status = 'FAILED'
                cf_reason = result.get('error', 'Unknown error')
                response_body = {'error': result.get('error')}
    else:
        status_code = 400
        cf_status = 'FAILED'
        cf_reason = f'Unsupported request type: {request_type}'
        response_body = {'error': cf_reason}

    send_response(event, cf_status, cf_reason, resource_id, cf_data)
    return {'statusCode': status_code, 'body': json.dumps(response_body)}
