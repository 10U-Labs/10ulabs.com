import json
import os
import re

import boto3


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    result = bool(re.match(pattern, email))
    return result


def validate_request_body(body):
    if not isinstance(body, dict):
        return False, 'Invalid request format'
    name = body.get('name', '')
    email = body.get('email', '')
    message = body.get('message', '')
    if not name or not isinstance(name, str):
        return False, 'Name is required'
    if len(name) > 100:
        return False, 'Name must be less than 100 characters'
    if not email or not isinstance(email, str):
        return False, 'Email is required'
    if len(email) > 255:
        return False, 'Email must be less than 255 characters'
    if not validate_email(email):
        return False, 'Invalid email address'
    if not message or not isinstance(message, str):
        return False, 'Message is required'
    if len(message) > 1000:
        return False, 'Message must be less than 1000 characters'
    return True, None


def build_response(status_code, body):
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }
    return response


def send_email(ses_client, recipient, sender_name, sender_email, message):
    subject = f'Contact Form: Message from {sender_name}'
    body_text = f'Name: {sender_name}\nEmail: {sender_email}\n\nMessage:\n{message}'
    body_html = f'''
<html>
<body>
<h2>New Contact Form Submission</h2>
<p><strong>Name:</strong> {sender_name}</p>
<p><strong>Email:</strong> <a href="mailto:{sender_email}">{sender_email}</a></p>
<h3>Message:</h3>
<p>{message.replace(chr(10), '<br>')}</p>
</body>
</html>
'''
    ses_client.send_email(
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
    return None


def handler(event, _context):
    if event.get('httpMethod') == 'OPTIONS':
        return build_response(200, {'message': 'OK'})
    recipient = os.environ.get('CONTACT_EMAIL')
    if not recipient:
        return build_response(500, {'error': 'Server configuration error'})
    body_str = event.get('body', '')
    if not body_str:
        return build_response(400, {'error': 'Request body is required'})
    try:
        body = json.loads(body_str)
    except json.JSONDecodeError:
        return build_response(400, {'error': 'Invalid JSON'})
    is_valid, error_message = validate_request_body(body)
    if not is_valid:
        return build_response(400, {'error': error_message})
    ses_client = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    try:
        send_email(ses_client, recipient, body['name'], body['email'], body['message'])
    except Exception:
        return build_response(500, {'error': 'Failed to send message'})
    return build_response(200, {'message': 'Message sent successfully'})
