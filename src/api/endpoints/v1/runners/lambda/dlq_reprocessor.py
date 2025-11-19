import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def reprocess_dlq_messages(dlq_url: str, target_queue_url: str, max_messages: int = 10) -> dict:
    sqs = boto3.client('sqs')
    reprocessed = 0
    failed = 0

    try:
        response = sqs.receive_message(
            QueueUrl=dlq_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=5,
            MessageAttributeNames=['All']
        )

        messages = response.get('Messages', [])
        logger.info("Found %d messages in DLQ: %s", len(messages), dlq_url)

        for message in messages:
            try:
                sqs.send_message(
                    QueueUrl=target_queue_url,
                    MessageBody=message['Body'],
                    MessageAttributes=message.get('MessageAttributes', {})
                )

                sqs.delete_message(
                    QueueUrl=dlq_url,
                    ReceiptHandle=message['ReceiptHandle']
                )

                reprocessed += 1
                logger.info("Reprocessed message from DLQ to target queue")

            except ClientError as e:
                logger.error("Failed to reprocess message: %s", e)
                failed += 1

    except ClientError as e:
        logger.error("Failed to receive messages from DLQ: %s", e)
        return {'reprocessed': 0, 'failed': 0, 'error': str(e)}

    return {'reprocessed': reprocessed, 'failed': failed}


def handler(event, context):
    del event, context
    webhook_dlq_url = os.environ.get('WEBHOOK_DLQ_URL')
    job_dlq_url = os.environ.get('JOB_DLQ_URL')
    job_queue_url = os.environ.get('JOB_QUEUE_URL')

    results = {}

    if job_dlq_url and job_queue_url:
        logger.info("Processing job queue DLQ")
        results['job_dlq'] = reprocess_dlq_messages(job_dlq_url, job_queue_url)

    if webhook_dlq_url:
        logger.info("Webhook DLQ messages cannot be automatically reprocessed (require API Gateway)")
        results['webhook_dlq'] = {'reprocessed': 0, 'failed': 0, 'note': 'Manual intervention required'}

    logger.info("DLQ reprocessing complete: %s", json.dumps(results))

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
