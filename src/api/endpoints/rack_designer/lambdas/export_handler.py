"""Lambda handler for exporting DynamoDB table to S3."""
import os
from datetime import datetime, timezone
import boto3


def lambda_handler(_event, _context):
    """Export DynamoDB table to S3 at point in time."""
    dynamodb = boto3.client('dynamodb')
    table_arn = os.environ['DYNAMODB_TABLE_ARN']
    s3_bucket = os.environ['S3_BUCKET']
    s3_prefix = os.environ['S3_PREFIX']
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')
    s3_path = f's3://{s3_bucket}/{s3_prefix}/{timestamp}'
    response = dynamodb.export_table_to_point_in_time(
        TableArn=table_arn,
        S3Bucket=s3_bucket,
        S3Prefix=f'{s3_prefix}/{timestamp}',
        ExportFormat='DYNAMODB_JSON'
    )
    export_arn = response['ExportDescription']['ExportArn']
    result = {
        'statusCode': 200,
        'body': {
            'export_arn': export_arn,
            's3_path': s3_path,
            'timestamp': timestamp
        }
    }
    return result
