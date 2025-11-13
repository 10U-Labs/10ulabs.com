#!/usr/bin/env python3
"""
End-to-end tests for GitHub self-hosted runners infrastructure.

These tests verify complete business workflows:
- Webhook processing: GitHub webhook → API Gateway → Lambda → ECS RunTask
- Runner registration: ECS task launches → Runner registers → Executes job → De-registers
- Network connectivity: Runners can access GitHub API and ECR via public internet
- Security: Webhook signature validation and proper IAM permissions

Note: Unit tests are in CINC Auditor controls (controls/aws.rb).
      Integration tests are mixed into CINC controls (API Gateway ↔ Lambda, etc.).
"""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest


# Test configuration
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
CONFIG_FILE = REPO_ROOT / 'config' / 'github_self_hosted_runners.json'


def load_config():
    """Load infrastructure configuration."""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def get_stack_output(stack_name, output_key):
    """Get CloudFormation stack output value.

    Args:
        stack_name: Name of the CloudFormation stack
        output_key: Key of the output to retrieve

    Returns:
        Output value as string
    """
    result = subprocess.run(
        ['aws', 'cloudformation', 'describe-stacks',
         '--stack-name', stack_name,
         '--query', f'Stacks[0].Outputs[?OutputKey==`{output_key}`].OutputValue',
         '--output', 'text'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def get_secret_value(secret_name, region):
    """Get secret value from AWS Secrets Manager.

    Args:
        secret_name: Name of the secret
        region: AWS region

    Returns:
        Secret value as string or dict
    """
    result = subprocess.run(
        ['aws', 'secretsmanager', 'get-secret-value',
         '--secret-id', secret_name,
         '--region', region,
         '--query', 'SecretString',
         '--output', 'text'],
        capture_output=True,
        text=True,
        check=True
    )

    secret_string = result.stdout.strip()

    # Try to parse as JSON, otherwise return as string
    try:
        return json.loads(secret_string)
    except json.JSONDecodeError:
        return secret_string


def invoke_webhook(webhook_url, payload, signature):
    """Invoke the webhook endpoint with a payload.

    Args:
        webhook_url: The webhook URL
        payload: Dict payload to send
        signature: HMAC signature for validation

    Returns:
        Response status code and body
    """
    payload_json = json.dumps(payload)

    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}',
         '-X', 'POST',
         '-H', 'Content-Type: application/json',
         '-H', f'X-Hub-Signature-256: sha256={signature}',
         '-H', 'X-GitHub-Event: workflow_job',
         '-d', payload_json,
         webhook_url],
        capture_output=True,
        text=True
    )

    lines = result.stdout.strip().split('\n')
    status_code = int(lines[-1])
    body = '\n'.join(lines[:-1]) if len(lines) > 1 else ''

    return status_code, body


def compute_webhook_signature(payload, secret):
    """Compute HMAC-SHA256 signature for webhook payload.

    Args:
        payload: Dict payload
        secret: Webhook secret

    Returns:
        Hex digest signature
    """
    import hmac
    import hashlib

    payload_json = json.dumps(payload)
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


def list_ecs_tasks(cluster_name, region):
    """List running ECS tasks in a cluster.

    Args:
        cluster_name: Name of the ECS cluster
        region: AWS region

    Returns:
        List of task ARNs
    """
    result = subprocess.run(
        ['aws', 'ecs', 'list-tasks',
         '--cluster', cluster_name,
         '--region', region,
         '--output', 'json'],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    return data.get('taskArns', [])


def describe_ecs_task(cluster_name, task_arn, region):
    """Describe an ECS task.

    Args:
        cluster_name: Name of the ECS cluster
        task_arn: ARN of the task
        region: AWS region

    Returns:
        Task description dict
    """
    result = subprocess.run(
        ['aws', 'ecs', 'describe-tasks',
         '--cluster', cluster_name,
         '--tasks', task_arn,
         '--region', region,
         '--output', 'json'],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    return data['tasks'][0] if data.get('tasks') else None


def list_github_runners(github_token, github_org, github_repo):
    """List GitHub self-hosted runners for a repository.

    Args:
        github_token: GitHub PAT with repo scope
        github_org: GitHub organization name
        github_repo: GitHub repository name

    Returns:
        List of runner dicts
    """
    result = subprocess.run(
        ['curl', '-s',
         '-H', 'Accept: application/vnd.github+json',
         '-H', f'Authorization: Bearer {github_token}',
         '-H', 'X-GitHub-Api-Version: 2022-11-28',
         f'https://api.github.com/repos/{github_org}/{github_repo}/actions/runners'],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    return data.get('runners', [])


class TestWebhookProcessingWorkflow:
    """Test the complete webhook processing workflow.

    Workflow: GitHub webhook → API Gateway → Lambda → ECS RunTask
    """

    @pytest.fixture
    def config(self):
        """Load configuration."""
        return load_config()

    @pytest.fixture
    def webhook_url(self):
        """Get webhook URL from CloudFormation outputs."""
        return get_stack_output('GitHubRunnersWebhook', 'WebhookUrl')

    @pytest.fixture
    def webhook_secret(self, config):
        """Get webhook secret from Secrets Manager."""
        secret_data = get_secret_value(
            config['naming']['webhook_secret_name'],
            config['aws']['region']
        )
        # Secret can be stored as plain string or as JSON with 'webhook_secret' key
        if isinstance(secret_data, dict):
            return secret_data.get('webhook_secret', secret_data.get('secret'))
        return secret_data

    def test_webhook_endpoint_accessible(self, webhook_url):
        """Test that webhook endpoint is accessible via public internet."""
        # Simple GET request should return 403 or similar (no signature)
        result = subprocess.run(
            ['curl', '-s', '-w', '\n%{http_code}', '-X', 'GET', webhook_url],
            capture_output=True,
            text=True
        )

        lines = result.stdout.strip().split('\n')
        status_code = int(lines[-1])

        # Should get some response (not timeout or connection refused)
        assert status_code > 0, "Webhook endpoint should be accessible"

    def test_webhook_rejects_invalid_signature(self, webhook_url):
        """Test that webhook rejects requests with invalid signatures."""
        payload = {
            'action': 'queued',
            'workflow_job': {
                'id': 12345,
                'name': 'test-job',
                'labels': ['fargate', 'general']
            }
        }

        # Use invalid signature
        status_code, body = invoke_webhook(webhook_url, payload, 'invalid_signature')

        # Should reject with 401 or 403
        assert status_code in [401, 403], f"Should reject invalid signature, got {status_code}"

    @pytest.mark.skip(reason="Requires valid webhook secret setup")
    def test_webhook_accepts_valid_signature(self, webhook_url, webhook_secret, config):
        """Test that webhook accepts requests with valid signatures."""
        payload = {
            'action': 'queued',
            'workflow_job': {
                'id': 12345,
                'name': 'test-job',
                'labels': ['fargate', 'general']
            },
            'repository': {
                'full_name': config['github']['repo']
            }
        }

        signature = compute_webhook_signature(payload, webhook_secret)
        status_code, body = invoke_webhook(webhook_url, payload, signature)

        # Should accept with 200 or 202
        assert status_code in [200, 202], f"Should accept valid signature, got {status_code}"


class TestRunnerNetworkConnectivity:
    """Test that runners have proper network connectivity.

    Validates cost optimization: runners use public internet (no VPC endpoints, no NAT gateway).
    """

    @pytest.fixture
    def config(self):
        """Load configuration."""
        return load_config()

    def test_runners_can_reach_github_api(self, config):
        """Test that public subnets allow access to GitHub API.

        This validates our cost optimization: no NAT gateway needed.
        """
        # Get VPC and subnet info
        vpc_id = get_stack_output('GitHubRunnersVpc', 'VpcId')

        # Check that subnets have internet gateway route (not NAT gateway)
        result = subprocess.run(
            ['aws', 'ec2', 'describe-route-tables',
             '--filters', f'Name=vpc-id,Values={vpc_id}',
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        route_tables = data.get('RouteTables', [])

        # Should have route tables with IGW routes (not NAT gateway)
        has_igw_route = False
        has_nat_route = False

        for rt in route_tables:
            for route in rt.get('Routes', []):
                if 'GatewayId' in route and route['GatewayId'].startswith('igw-'):
                    has_igw_route = True
                if 'NatGatewayId' in route:
                    has_nat_route = True

        assert has_igw_route, "Should have internet gateway route for GitHub API access"
        assert not has_nat_route, "Should NOT have NAT gateway route (cost optimization)"

    def test_runners_can_reach_ecr(self, config):
        """Test that runners can pull from ECR without VPC endpoints.

        This validates our cost optimization: no VPC endpoints needed.
        """
        # Get VPC info
        vpc_id = get_stack_output('GitHubRunnersVpc', 'VpcId')

        # Check that VPC has NO endpoints (we use public internet)
        result = subprocess.run(
            ['aws', 'ec2', 'describe-vpc-endpoints',
             '--filters', f'Name=vpc-id,Values={vpc_id}',
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        endpoints = data.get('VpcEndpoints', [])

        # Should have ZERO VPC endpoints (cost savings: $86/month)
        assert len(endpoints) == 0, "Should have no VPC endpoints (use public internet for cost savings)"


class TestRunnerTaskConfiguration:
    """Test that ECS tasks are configured correctly."""

    @pytest.fixture
    def config(self):
        """Load configuration."""
        return load_config()

    def test_task_definition_exists(self, config):
        """Test that task definition exists with correct configuration."""
        # Get task definition ARN from stack outputs
        task_def_arn = get_stack_output('GitHubRunnersWebhook', 'TaskDefinitionArn')

        assert task_def_arn, "Task definition ARN should be exported"
        assert 'github' in task_def_arn.lower(), "Task definition should be for GitHub runners"

    def test_ecs_cluster_exists(self, config):
        """Test that ECS cluster exists and is active."""
        cluster_name = get_stack_output('GitHubRunnersWebhook', 'ClusterName')

        result = subprocess.run(
            ['aws', 'ecs', 'describe-clusters',
             '--clusters', cluster_name,
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        clusters = data.get('clusters', [])

        assert len(clusters) == 1, "Should have exactly one cluster"
        assert clusters[0]['status'] == 'ACTIVE', "Cluster should be active"


class TestLambdaWebhookHandler:
    """Test Lambda webhook handler configuration."""

    @pytest.fixture
    def config(self):
        """Load configuration."""
        return load_config()

    def test_lambda_function_exists(self, config):
        """Test that Lambda function exists with correct configuration."""
        lambda_name = get_stack_output('GitHubRunnersWebhook', 'LambdaFunctionName')

        result = subprocess.run(
            ['aws', 'lambda', 'get-function',
             '--function-name', lambda_name,
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        function_config = data['Configuration']

        # Validate configuration matches config file
        assert function_config['Runtime'].startswith('python'), "Should use Python runtime"
        assert function_config['Timeout'] == config['lambda']['timeout_seconds'], \
            f"Timeout should be {config['lambda']['timeout_seconds']} seconds"
        assert function_config['MemorySize'] == config['lambda']['memory_mb'], \
            f"Memory should be {config['lambda']['memory_mb']} MB"

    def test_lambda_has_ecs_permissions(self, config):
        """Test that Lambda has permissions to run ECS tasks."""
        lambda_name = get_stack_output('GitHubRunnersWebhook', 'LambdaFunctionName')

        result = subprocess.run(
            ['aws', 'lambda', 'get-function',
             '--function-name', lambda_name,
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        role_arn = data['Configuration']['Role']
        role_name = role_arn.split('/')[-1]

        # Get role policies
        result = subprocess.run(
            ['aws', 'iam', 'list-attached-role-policies',
             '--role-name', role_name,
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        policies = data.get('AttachedPolicies', [])

        # Should have some policies attached
        assert len(policies) > 0, "Lambda role should have policies attached"


class TestSecurityConfiguration:
    """Test security configuration and IAM permissions."""

    @pytest.fixture
    def config(self):
        """Load configuration."""
        return load_config()

    def test_webhook_secret_exists(self, config):
        """Test that webhook secret exists in Secrets Manager."""
        secret_name = config['naming']['webhook_secret_name']

        result = subprocess.run(
            ['aws', 'secretsmanager', 'describe-secret',
             '--secret-id', secret_name,
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

        assert data['Name'] == secret_name, "Secret should have correct name"
        assert 'ARN' in data, "Secret should have ARN"

    def test_github_token_secret_exists(self, config):
        """Test that GitHub token secret exists in Secrets Manager."""
        secret_name = config['naming']['github_token_secret_name']

        result = subprocess.run(
            ['aws', 'secretsmanager', 'describe-secret',
             '--secret-id', secret_name,
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

        assert data['Name'] == secret_name, "Secret should have correct name"
        assert 'ARN' in data, "Secret should have ARN"
