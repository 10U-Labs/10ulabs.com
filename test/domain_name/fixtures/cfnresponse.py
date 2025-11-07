"""CloudFormation custom resource response helper

This module is provided by AWS Lambda for custom resources.
This file is included for local testing compatibility.
"""
import json
import urllib3

SUCCESS = "SUCCESS"
FAILED = "FAILED"

http = urllib3.PoolManager()


def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    """
    Send a response to CloudFormation for a custom resource.

    Args:
        event: The Lambda event dict
        context: The Lambda context object
        responseStatus: SUCCESS or FAILED
        responseData: dict of custom resource response data
        physicalResourceId: Physical resource ID (optional)
        noEcho: Whether to mask output from CloudFormation logs (optional)
        reason: Failure reason (optional)
    """
    responseUrl = event['ResponseURL']

    responseBody = {
        'Status': responseStatus,
        'Reason': reason or f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
        'PhysicalResourceId': physicalResourceId or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': noEcho,
        'Data': responseData
    }

    json_responseBody = json.dumps(responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = http.request('PUT', responseUrl, headers=headers, body=json_responseBody)
        print(f"Status code: {response.status}")
    except Exception as e:
        print(f"send(..) failed executing http.request(..): {e}")
