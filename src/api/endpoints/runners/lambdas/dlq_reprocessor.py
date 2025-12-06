"""Lambda handler for reprocessing messages from dead letter queues."""
import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_REPROCESS_ATTEMPTS = 3

_clients: dict[str, Any] = {}


def reset_clients():
    """Clear cached AWS clients."""
    _clients.clear()


def get_sqs_client():
    """Get or create cached SQS client."""
    if 'sqs' not in _clients:
        _clients['sqs'] = boto3.client('sqs')
    return _clients['sqs']


def get_sns_client():
    """Get or create cached SNS client."""
    if 'sns' not in _clients:
        _clients['sns'] = boto3.client('sns')
    return _clients['sns']


def get_ssm_client():
    """Get or create cached SSM client."""
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_github_token() -> str:
    """Retrieve GitHub token from SSM Parameter Store."""
    result = ''
    parameter_name = os.environ.get('GITHUB_TOKEN_PARAMETER_NAME')
    if parameter_name:
        try:
            ssm = get_ssm_client()
            response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
            result = response['Parameter']['Value']
        except ClientError as e:
            logger.error("Failed to get GitHub token: %s", e)
    return result


def check_github_job_status(github_repo: str, job_id: int, github_token: str) -> str:
    """Check the status of a GitHub Actions job."""
    result = 'unknown'
    if not github_token:
        logger.warning("No GitHub token available, cannot check job status")
    else:
        url = f"https://api.github.com/repos/{github_repo}/actions/jobs/{job_id}"
        req = urllib.request.Request(url, headers={
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'TenULabs-DLQ-Reprocessor'
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                result = data.get('status', 'unknown')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.info("Job %s not found in GitHub (may have expired)", job_id)
                result = 'not_found'
            else:
                logger.error("GitHub API error for job %s: %s", job_id, e)
                result = 'error'
        except (urllib.error.URLError, ValueError) as e:
            logger.error("Failed to check GitHub job status: %s", e)
            result = 'error'
    return result


def send_poison_pill_alert(message_body: dict, attempt_count: int, reason: str):
    """Send SNS alert for messages exceeding max retry attempts."""
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    if not sns_topic_arn:
        logger.warning("SNS_TOPIC_ARN not configured, cannot send alert")
    else:
        job_id = message_body.get('job_id', 'unknown')
        github_repo = message_body.get('github_repo', 'unknown')
        dlq_url = os.environ.get('JOB_DLQ_URL')
        dlq_url_display = dlq_url if dlq_url else 'unknown'
        subject = f"DLQ Poison Pill Alert: Job {job_id}"
        message = f"""DLQ message exceeded max reprocess attempts.

Job ID: {job_id}
GitHub Repo: {github_repo}
Reprocess Attempts: {attempt_count}
Reason: {reason}

Message Body:
{json.dumps(message_body, indent=2)}

Action Required:
1. Investigate why this job keeps failing
2. Either fix the underlying issue and manually reprocess, or delete the message from the DLQ

DLQ URL: {dlq_url_display}
"""
        try:
            sns = get_sns_client()
            sns.publish(TopicArn=sns_topic_arn, Subject=subject, Message=message)
            logger.info("Sent poison pill alert for job %s", job_id)
        except ClientError as e:
            logger.error("Failed to send SNS alert: %s", e)


def get_reprocess_attempt_count(message: dict) -> int:
    """Get the reprocess attempt count from message attributes."""
    attrs = message.get('MessageAttributes', {})
    attempt_attr = attrs.get('ReprocessAttempts', {})
    attempt_str = attempt_attr.get('StringValue', '0')
    result = 0
    try:
        result = int(attempt_str)
    except ValueError:
        pass
    return result


def reprocess_dlq_messages(
    dlq_url: str, target_queue_url: str, max_messages: int = 10
) -> dict:
    """Reprocess messages from a dead letter queue."""
    result: dict[str, Any] = {
        'reprocessed': 0, 'skipped_completed': 0, 'skipped_max_retries': 0, 'failed': 0
    }

    try:
        response = get_sqs_client().receive_message(
            QueueUrl=dlq_url, MaxNumberOfMessages=max_messages, WaitTimeSeconds=5,
            MessageAttributeNames=['All'], AttributeNames=['ApproximateReceiveCount']
        )
        messages = response.get('Messages', [])
        logger.info("Found %d messages in DLQ: %s", len(messages), dlq_url)

        for message in messages:
            _process_dlq_message(message, dlq_url, target_queue_url, result)

    except ClientError as e:
        logger.error("Failed to receive messages from DLQ: %s", e)
        result['error'] = str(e)

    return result


def _process_dlq_message(
    message: dict, dlq_url: str, target_queue_url: str, result: dict
):
    """Process a single DLQ message and attempt reprocessing."""
    sqs = get_sqs_client()
    body = None
    try:
        body = json.loads(message['Body'])
    except (json.JSONDecodeError, KeyError):
        logger.error("Invalid message body, skipping: %s", message.get('Body', '')[:200])
        result['failed'] += 1
    if body is not None:
        job_id = body.get('job_id')
        attempt_count = get_reprocess_attempt_count(message) + 1
        if attempt_count > MAX_REPROCESS_ATTEMPTS:
            logger.warning(
                "Job %s exceeded max retries (%d)", job_id, MAX_REPROCESS_ATTEMPTS
            )
            send_poison_pill_alert(body, attempt_count, "Exceeded maximum reprocess attempts")
            result['skipped_max_retries'] += 1
        elif not _should_skip_completed_job(
            body, job_id, dlq_url, message['ReceiptHandle'], result
        ):
            try:
                message_attrs = message.get('MessageAttributes', {})
                message_attrs['ReprocessAttempts'] = {
                    'DataType': 'Number', 'StringValue': str(attempt_count)
                }
                sqs.send_message(
                    QueueUrl=target_queue_url,
                    MessageBody=message['Body'],
                    MessageAttributes=message_attrs
                )
                sqs.delete_message(
                    QueueUrl=dlq_url, ReceiptHandle=message['ReceiptHandle']
                )
                result['reprocessed'] += 1
                logger.info(
                    "Reprocessed job %s (attempt %d/%d)",
                    job_id, attempt_count, MAX_REPROCESS_ATTEMPTS
                )
            except ClientError as e:
                logger.error("Failed to reprocess message for job %s: %s", job_id, e)
                result['failed'] += 1


def _should_skip_completed_job(
    body: dict, job_id: int, dlq_url: str, receipt_handle: str, result: dict
) -> bool:
    """Check if job is already completed and should be skipped."""
    skip = False
    github_repo = body.get('github_repo')
    if github_repo and job_id:
        job_status = check_github_job_status(github_repo, job_id, get_github_token())
        if job_status in ('completed', 'not_found'):
            status_msg = 'already completed' if job_status == 'completed' else 'not found (expired)'
            logger.info("Job %s %s in GitHub, deleting from DLQ", job_id, status_msg)
            get_sqs_client().delete_message(QueueUrl=dlq_url, ReceiptHandle=receipt_handle)
            result['skipped_completed'] += 1
            skip = True
    return skip


def handler(event, context):
    """Main Lambda handler for DLQ reprocessing."""
    del event, context
    webhook_dlq_url = os.environ.get('WEBHOOK_DLQ_URL')
    job_dlq_url = os.environ.get('JOB_DLQ_URL')
    job_queue_url = os.environ.get('JOB_QUEUE_URL')

    results = {}

    if job_dlq_url and job_queue_url:
        logger.info("Processing job queue DLQ")
        results['job_dlq'] = reprocess_dlq_messages(job_dlq_url, job_queue_url)

    if webhook_dlq_url:
        logger.info("Webhook DLQ messages cannot be auto-reprocessed")
        results['webhook_dlq'] = {
            'reprocessed': 0, 'failed': 0, 'note': 'Manual intervention required'
        }

    logger.info("DLQ reprocessing complete: %s", json.dumps(results))

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
