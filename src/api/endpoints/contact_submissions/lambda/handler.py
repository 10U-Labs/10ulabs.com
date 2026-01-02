"""Contact form Lambda handler for 10U Labs API.

Provides endpoints for processing contact form submissions with reCAPTCHA
verification and email notification via SES.
"""
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients: Dict[str, Any] = {}
_test_mode = {'enabled': False}


def is_test_mode() -> bool:
    """Check if test mode is enabled."""
    return _test_mode['enabled']


def set_test_mode(enabled: bool):
    """Set test mode enabled state."""
    _test_mode['enabled'] = enabled


def get_header_case_insensitive(headers: dict, header_name: str) -> str:
    """Get a header value case-insensitively."""
    if not headers:
        return ''
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value or ''
    return ''


def get_ssm_client():
    """Get or create a cached SSM client."""
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_ses_client():
    """Get or create a cached SES client."""
    if 'ses' not in _clients:
        _clients['ses'] = boto3.client('ses')
    return _clients['ses']


def set_client(name: str, client: Any):
    """Set a client for testing purposes."""
    _clients[name] = client


CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a JSON API Gateway response with CORS headers for contact endpoint."""
    return {'statusCode': status_code, 'headers': CORS_HEADERS, 'body': json.dumps(body)}


def error_response(
    status_code: int, error: str, details: str | None = None
) -> Dict[str, Any]:
    """Create an error response for contact endpoint with optional details."""
    response_body: Dict[str, Any] = {'success': False, 'error': error}
    if details is not None:
        response_body['details'] = details
    return json_response(status_code, response_body)


def parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and parse JSON body from Lambda event for contact form processing."""
    raw_body = event.get('body') or '{}'
    return json.loads(raw_body) if isinstance(raw_body, str) else raw_body


def get_recaptcha_secret() -> str:
    """Retrieve reCAPTCHA secret from SSM Parameter Store."""
    parameter_name = os.environ.get('RECAPTCHA_SECRET_PARAMETER_NAME')
    if not parameter_name:
        return ''
    try:
        response = get_ssm_client().get_parameter(
            Name=parameter_name, WithDecryption=True
        )
        secret = response['Parameter']['Value']
        return secret
    except (ClientError, ValueError, KeyError) as e:
        logger.error("Failed to retrieve reCAPTCHA secret: %s", e)
        return ''


def verify_recaptcha(token: str, secret: str) -> bool:
    """Verify a reCAPTCHA token with Google's API."""
    if not token or not secret:
        return False
    try:
        data = urllib.parse.urlencode({
            'secret': secret,
            'response': token
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://www.google.com/recaptcha/api/siteverify',
            data=data,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            success = result.get('success', False)
            score = result.get('score', 0)
            is_valid = success and score >= 0.5
            if not is_valid:
                logger.warning(
                    "reCAPTCHA verification failed: success=%s, score=%s",
                    success, score
                )
            return is_valid
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        logger.error("reCAPTCHA verification error: %s", e)
        return False


def validate_contact_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    result = bool(re.match(pattern, email))
    return result


def send_contact_email(
    recipient: str, sender_name: str, sender_email: str, message: str
) -> bool:
    """Send contact form email via SES."""
    subject = f'Contact Form: Message from {sender_name}'
    body_text = f'Name: {sender_name}\nEmail: {sender_email}\n\nMessage:\n{message}'
    body_html = f'''<html>
<body>
<h2>New Contact Form Submission</h2>
<p><strong>Name:</strong> {sender_name}</p>
<p><strong>Email:</strong> <a href="mailto:{sender_email}">{sender_email}</a></p>
<h3>Message:</h3>
<p>{message.replace(chr(10), '<br>')}</p>
</body>
</html>'''
    try:
        get_ses_client().send_email(
            Source=recipient,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                }
            },
            ReplyToAddresses=[sender_email]
        )
        return True
    except ClientError as e:
        logger.error("Failed to send contact email: %s", e)
        return False


def _validate_contact_fields(fields: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Validate contact form fields and return error response if invalid."""
    validations = [
        (not fields['recaptcha_token'], 'Missing required field: recaptcha_token'),
        (not fields['name'], 'Missing required field: name'),
        (len(fields['name']) > 100, 'Name must be less than 100 characters'),
        (not fields['email'], 'Missing required field: email'),
        (len(fields['email']) > 255, 'Email must be less than 255 characters'),
        (
            fields['email'] and not validate_contact_email(fields['email']),
            'Invalid email address'
        ),
        (not fields['message'], 'Missing required field: message'),
        (len(fields['message']) > 1000, 'Message must be less than 1000 characters'),
    ]
    result = None
    for condition, error_msg in validations:
        if condition and result is None:
            result = error_response(400, error_msg)
    return result


def _process_contact_submission(fields: Dict[str, str]) -> Dict[str, Any]:
    """Process a validated contact form submission."""
    recaptcha_secret = get_recaptcha_secret()
    contact_email = os.environ.get('CONTACT_EMAIL')
    response: Dict[str, Any]
    if not recaptcha_secret:
        logger.error("reCAPTCHA secret not configured")
        response = error_response(500, 'Server configuration error')
    elif not verify_recaptcha(fields['recaptcha_token'], recaptcha_secret):
        response = error_response(400, 'reCAPTCHA verification failed')
    elif not contact_email:
        response = error_response(500, 'Server configuration error')
    elif send_contact_email(
        contact_email, fields['name'], fields['email'], fields['message']
    ):
        logger.info(
            "Contact form submitted: name=%s, email=%s",
            fields['name'], fields['email']
        )
        response = json_response(
            200, {'success': True, 'message': 'Message sent successfully'}
        )
    else:
        response = error_response(500, 'Failed to send message')
    return response


TEST_MODE_MOCK_RESPONSE = {
    'success': True,
    'message': 'Test mode - contact form not submitted',
    'test_mode': True
}


def handle_contact_post(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /v1/contact-submissions request."""
    try:
        body = parse_request_body(event)
        fields = {
            'recaptcha_token': body.get('recaptcha_token', '').strip(),
            'name': body.get('name', '').strip(),
            'email': body.get('email', '').strip(),
            'message': body.get('message', '').strip(),
        }
        validation_error = _validate_contact_fields(fields)
        if validation_error:
            response = validation_error
        elif is_test_mode():
            response = json_response(200, TEST_MODE_MOCK_RESPONSE)
        else:
            response = _process_contact_submission(fields)
    except (ValueError, KeyError) as e:
        logger.error("Error handling contact form: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


ROUTE_MAP = {
    ('/v1/contact-submissions', 'POST'): handle_contact_post,
}


def handler(event, _context):
    """Lambda handler entry point."""
    logger.info("Received contact request: %s", json.dumps(event))

    headers = event.get('headers', {})
    test_mode_header = get_header_case_insensitive(headers, 'x-test-mode')
    set_test_mode(test_mode_header == 'true')

    if is_test_mode():
        logger.info("Test mode enabled - will return mock responses for POST requests")

    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }

    path = event.get('path', '')
    route_handler = ROUTE_MAP.get((path, method))

    if route_handler:
        response = route_handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
