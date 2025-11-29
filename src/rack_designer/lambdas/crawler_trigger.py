import os
import boto3


def lambda_handler(_event, _context):
    glue = boto3.client('glue')
    crawler_name = os.environ['CRAWLER_NAME']
    glue.start_crawler(Name=crawler_name)
    result = {
        'statusCode': 200,
        'body': {'crawler_name': crawler_name, 'status': 'started'}
    }
    return result
