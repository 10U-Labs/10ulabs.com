"""Helper functions for EC2 instance management in tests."""
import os
import time
from botocore.exceptions import ClientError
from ec2_fleet import (
    launch_instance_with_retry,
    wait_for_instance_running,
    wait_for_status_checks,
    terminate_instance,
    LaunchOptions,
)


def build_launch_template_config(config):
    """Build launch template config."""

    template_config = {
        "ami_id": config["ami_id"],
        "security_group_id": config["security_group_id"],
        "iam_instance_profile": config["instance_profile"],
        "metadata_options": {
            "HttpTokens": "required",
            "HttpEndpoint": "enabled",
        },
    }
    if "user_data" in config:
        template_config["user_data"] = config["user_data"]
    tags = config.get("tags", [
        {"Key": "Name", "Value": "test-instance"},
        {"Key": "Purpose", "Value": "AMI Integration Testing"},
        {"Key": "ManagedBy", "Value": "pytest"}
    ])
    template_config["tag_specifications"] = [{
        "ResourceType": "instance",
        "Tags": tags,
    }]
    return template_config


def launch_instance(ec2_client, config):
    """Launch instance."""

    template_config = build_launch_template_config(config)
    instance_types = config.get("instance_types", [config.get("instance_type", "m7gd.xlarge")])
    subnet_ids = config.get("subnet_ids", [config.get("subnet_id")])
    options = LaunchOptions(
        instance_types=instance_types,
        subnet_ids=subnet_ids,
        allocation_strategy="lowest-price",
        max_retries=2,
        wait_for_ready=False,
    )
    return launch_instance_with_retry(ec2_client, template_config, options)


def wait_for_instance_ready(ec2_client, instance_id):
    """Wait for instance ready."""

    wait_for_instance_running(ec2_client, instance_id)
    wait_for_status_checks(ec2_client, instance_id)
    return True


def poll_ssm_command(ssm_client, instance_id, command_id, max_wait=60):
    """Poll ssm command."""

    start_time = time.time()
    while time.time() - start_time < max_wait:
        time.sleep(3)
        try:
            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            if output["Status"] in ("Success", "Failed", "Cancelled", "TimedOut"):
                return output
        except ClientError:
            pass
    result = {"Status": "Timeout", "StandardOutputContent": "", "StandardErrorContent": ""}
    return result


def get_instance_logs(ssm_client, instance_id):
    """Get instance logs."""

    log_commands = """
echo '=== cloud-init status ==='
cloud-init status 2>&1 || echo 'cloud-init status failed'

echo ''
echo '=== /var/log/user-data.log ==='
cat /var/log/user-data.log 2>&1 || echo 'user-data.log not found'

echo ''
echo '=== /var/log/cloud-init-output.log (last 50 lines) ==='
tail -50 /var/log/cloud-init-output.log 2>&1 || echo 'cloud-init-output.log not found'

echo ''
echo '=== Runner diag logs ==='
ls -la /home/github-runner/actions-runner/_diag/ 2>&1 || echo 'No diag directory'
tail -30 /home/github-runner/actions-runner/_diag/*.log 2>&1 || echo 'No diag logs'

echo ''
echo '=== Processes ==='
ps aux | grep -E 'runner|Runner' || echo 'No runner processes'
"""
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [log_commands]}
        )
        command_id = response["Command"]["CommandId"]
        output = poll_ssm_command(ssm_client, instance_id, command_id, max_wait=30)
        stdout = output.get("StandardOutputContent", "")
        stderr = output.get("StandardErrorContent", "")
        result = stdout
        if stderr:
            result = result + f"\n=== STDERR ===\n{stderr}"
        return result
    except ClientError as err:
        return f"Failed to retrieve logs: {err}"


def terminate_instance_safely(ec2_client, instance_id):
    """Safely terminate an EC2 instance."""
    terminate_instance(ec2_client, instance_id)


def get_subnet_ids():
    """Get subnet IDs from environment variables."""
    subnet_ids_env = os.environ.get("TEST_SUBNET_IDS", "")
    subnet_id_env = os.environ.get("TEST_SUBNET_ID", "")
    result = []
    if subnet_ids_env:
        result = [s.strip() for s in subnet_ids_env.split(",") if s.strip()]
    elif subnet_id_env:
        result = [subnet_id_env]
    return result


def get_instance_types():
    """Get instance types from INSTANCE_TYPES environment variable."""
    env_value = os.environ.get("INSTANCE_TYPES", "")
    result = env_value.split(",") if env_value else []
    return result
