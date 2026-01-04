"""Lambda handler for triggering AWS Glue crawlers."""
import os
import boto3


def lambda_handler(_event, _context):
    """Trigger the configured Glue crawler and return status."""
    glue = boto3.client('glue')
    crawler_name = os.environ['CRAWLER_NAME']
    glue.start_crawler(Name=crawler_name)
    result = {
        'statusCode': 200,
        'body': {'crawler_name': crawler_name, 'status': 'started'}
    }
    return result
