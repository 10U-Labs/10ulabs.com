from typing import Optional

from botocore.exceptions import ClientError


def create_client_error(
    error_code: str,
    operation_name: str = 'TestOperation',
    message: Optional[str] = None
) -> ClientError:
    return ClientError(
        {
            'Error': {
                'Code': error_code,
                'Message': message or f'Test error: {error_code}'
            },
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 400,
                'HTTPHeaders': {},
                'RetryAttempts': 0,
                'HostId': ''
            }
        },
        operation_name
    )
