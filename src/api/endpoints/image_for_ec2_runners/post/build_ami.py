#!/usr/bin/env python3
"""Build AMI using EC2 Fleet spot instances for GitHub Actions runners."""
import argparse
import logging
import sys
import time
import uuid
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, Optional
import boto3
from botocore.exceptions import ClientError
import paramiko
from ec2_fleet import (
    create_fleet_instance as shared_create_fleet,
    wait_for_instance_running as shared_wait_running,
    wait_for_status_checks as shared_wait_status,
    LaunchOptions,
)

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)

SETUP_SCRIPT = "setup.sh"


@dataclass
class LaunchTemplateParams:
    """Parameters for creating an EC2 launch template."""

    template_name: str
    base_ami: str
    sg_id: str
    key_name: str
    iam_profile: Optional[str]


@dataclass
class ScriptParams:
    """Parameters for running the setup script on an instance."""

    ip_addr: str
    key_material: str
    script_path: str
    runner_version: str
    yq_version: str
    runner_user: str


@dataclass
class BuildState:
    """Mutable state tracking for the AMI build process."""

    instance_id: Optional[str] = None
    sg_id: Optional[str] = None
    key_material: Optional[str] = None
    result: Optional[str] = None


@dataclass
class BuildContext:
    """Immutable context for the AMI build process."""

    ec2: Any
    args: Any
    script_dir: Path
    unique_id: str


def get_vpc_from_subnet(ec2, subnet_id):
    """Get the VPC ID from a subnet ID."""
    response = ec2.describe_subnets(SubnetIds=[subnet_id])
    return response["Subnets"][0]["VpcId"]


def lookup_source_ami(ec2, ami_name):
    """Look up an AMI ID by name from Debian."""
    response = ec2.describe_images(
        Owners=["136693071363"],
        Filters=[
            {"Name": "name", "Values": [ami_name]},
        ],
    )
    if not response["Images"]:
        raise RuntimeError(f"No AMI found with name: {ami_name}")
    return response["Images"][0]["ImageId"]


def create_key_pair(ec2, key_name, tags):
    """Create an EC2 key pair and return the private key material."""
    tag_specs = []
    if tags:
        tag_list = [{"Key": k, "Value": str(v)} for k, v in tags.items()]
        tag_specs = [{"ResourceType": "key-pair", "Tags": tag_list}]
    response = ec2.create_key_pair(
        KeyName=key_name, KeyType="ed25519", TagSpecifications=tag_specs
    )
    return response["KeyMaterial"]


def delete_key_pair(ec2, key_name):
    """Delete an EC2 key pair."""
    ec2.delete_key_pair(KeyName=key_name)


def create_security_group(ec2, vpc_id, group_name, tags):
    """Create a security group with SSH access."""
    tag_specs = []
    if tags:
        tag_list = [{"Key": k, "Value": str(v)} for k, v in tags.items()]
        tag_specs = [{"ResourceType": "security-group", "Tags": tag_list}]
    response = ec2.create_security_group(
        GroupName=group_name,
        Description="Temporary SG for AMI builder",
        VpcId=vpc_id,
        TagSpecifications=tag_specs,
    )
    sg_id = response["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        }],
    )
    return sg_id


def delete_security_group(ec2, sg_id):
    """Delete a security group with retry logic."""
    deleted = False
    attempts = 0
    while not deleted and attempts < 12:
        try:
            ec2.delete_security_group(GroupId=sg_id)
            deleted = True
        except ec2.exceptions.ClientError:
            time.sleep(5)
        attempts += 1


def create_launch_template(ec2, params: LaunchTemplateParams, tags):
    """Create an EC2 launch template."""
    data: dict[str, Any] = {
        "ImageId": params.base_ami,
        "KeyName": params.key_name,
        "SecurityGroupIds": [params.sg_id],
    }
    if params.iam_profile:
        data["IamInstanceProfile"] = {"Name": params.iam_profile}
    tag_specs = []
    if tags:
        tag_list = [{"Key": k, "Value": str(v)} for k, v in tags.items()]
        tag_specs = [{"ResourceType": "launch-template", "Tags": tag_list}]
    ec2.create_launch_template(
        LaunchTemplateName=params.template_name,
        LaunchTemplateData=data,
        TagSpecifications=tag_specs,
    )


def delete_launch_template(ec2, template_name):
    """Delete an EC2 launch template."""
    try:
        ec2.delete_launch_template(LaunchTemplateName=template_name)
    except ClientError:
        pass


def create_fleet_instance(ec2, template_name, instance_types, subnet_ids):
    """Create a fleet instance using the specified template."""
    response = ec2.describe_launch_templates(LaunchTemplateNames=[template_name])
    template_id = response["LaunchTemplates"][0]["LaunchTemplateId"]
    options = LaunchOptions(
        instance_types=instance_types,
        subnet_ids=subnet_ids,
        allocation_strategy="lowest-price",
    )
    return shared_create_fleet(ec2, template_id, options)


def wait_for_instance_running(ec2, instance_id):
    """Wait for an EC2 instance to reach running state."""
    logging.info("Waiting for instance %s to be running...", instance_id)
    shared_wait_running(ec2, instance_id)
    logging.info("Instance is running")


def wait_for_status_checks(ec2, instance_id):
    """Wait for EC2 instance status checks to pass."""
    logging.info("Waiting for status checks to pass...")
    shared_wait_status(ec2, instance_id)
    logging.info("All status checks passed")


def get_instance_public_ip(ec2, instance_id):
    """Get the public IP address of an EC2 instance."""
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["PublicIpAddress"]


def wait_for_instance(ec2, instance_id):
    """Wait for instance to be running and status checks to pass."""
    wait_for_instance_running(ec2, instance_id)
    wait_for_status_checks(ec2, instance_id)
    return get_instance_public_ip(ec2, instance_id)


def run_ssh_command(client, cmd):
    """Run a command over SSH and stream output to stdout."""
    _, stdout, _ = client.exec_command(cmd, timeout=600, get_pty=True)
    channel = stdout.channel
    while not channel.exit_status_ready():
        if channel.recv_ready():
            sys.stdout.write(channel.recv(4096).decode())
            sys.stdout.flush()
        time.sleep(0.1)
    while channel.recv_ready():
        sys.stdout.write(channel.recv(4096).decode())
        sys.stdout.flush()
    exit_code = channel.recv_exit_status()
    if exit_code != 0:
        raise RuntimeError(f"Command failed with exit code {exit_code}")


def run_script(params: ScriptParams):
    """Upload and run the setup script on the instance via SSH."""
    key = paramiko.Ed25519Key.from_private_key(StringIO(params.key_material))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for attempt in range(30):
        try:
            client.connect(params.ip_addr, username="admin", pkey=key, timeout=10)
            break
        except (paramiko.ssh_exception.NoValidConnectionsError, TimeoutError, OSError):
            if attempt == 29:
                raise
            time.sleep(10)
    sftp = client.open_sftp()
    remote_script = "/tmp/setup.sh"
    sftp.put(params.script_path, remote_script)
    sftp.chmod(remote_script, 0o755)
    sftp.close()
    args_str = (
        f"--runner-version {params.runner_version} "
        f"--yq-version {params.yq_version} "
        f"--runner-user {params.runner_user}"
    )
    env_setup = (
        "export DEBIAN_FRONTEND=noninteractive && "
        "export TERM=dumb && export NO_COLOR=1 && "
        "echo quiet \\\"1\\\"\\; > /etc/apt/apt.conf.d/99quiet"
    )
    full_cmd = f"sudo bash -c '{env_setup} && {remote_script} {args_str}'"
    run_ssh_command(client, full_cmd)
    client.close()


def create_ami(ec2, instance_id, ami_name, ami_description, tags):
    """Create an AMI from an instance and apply tags."""
    description = ami_description or ""
    response = ec2.create_image(InstanceId=instance_id, Name=ami_name, Description=description)
    ami_id = response["ImageId"]
    logging.info("Creating AMI %s...", ami_id)
    waiter = ec2.get_waiter("image_available")
    waiter.wait(ImageIds=[ami_id])
    logging.info("AMI %s created.", ami_id)
    if tags:
        tag_list = [{"Key": k, "Value": str(v)} for k, v in tags.items()]
        ec2.create_tags(Resources=[ami_id], Tags=tag_list)
        image = ec2.describe_images(ImageIds=[ami_id])["Images"][0]
        snapshots = image.get("BlockDeviceMappings", [])
        for bdm in snapshots:
            if "Ebs" in bdm:
                ec2.create_tags(Resources=[bdm["Ebs"]["SnapshotId"]], Tags=tag_list)
    return ami_id


def terminate_instance(ec2, instance_id):
    """Terminate an EC2 instance and wait for termination."""
    ec2.terminate_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_terminated")
    waiter.wait(InstanceIds=[instance_id], WaiterConfig={"Delay": 15, "MaxAttempts": 40})


def cleanup(ec2, instance_id, template_name, key_name, sg_id):
    """Clean up temporary resources created during the build."""
    if instance_id:
        logging.info("Terminating temporary instance...")
        terminate_instance(ec2, instance_id)
        logging.info("Temporary instance terminated.")
    try:
        delete_launch_template(ec2, template_name)
    except boto3.exceptions.Boto3Error:
        pass
    try:
        logging.info("Deleting temporary key pair...")
        delete_key_pair(ec2, key_name)
        logging.info("Temporary key pair deleted.")
    except boto3.exceptions.Boto3Error:
        pass
    if sg_id:
        logging.info("Deleting temporary security group...")
        delete_security_group(ec2, sg_id)
        logging.info("Temporary security group deleted.")


def parse_tags(tag_list):
    """Parse KEY=VALUE tag arguments into a dictionary."""
    tags = {}
    for item in tag_list or []:
        if "=" in item:
            key, value = item.split("=", 1)
            tags[key] = value
    return tags


def run_build(ctx: BuildContext, state: BuildState):
    """Execute the AMI build process."""
    key_name = f"ami-builder-{ctx.unique_id}"
    template_name = f"ami-builder-{ctx.unique_id}"
    subnet_ids = ctx.args.subnet_ids
    tags = parse_tags(ctx.args.tag)
    logging.info("Subnets: %s", subnet_ids)
    vpc_id = get_vpc_from_subnet(ctx.ec2, subnet_ids[0])
    logging.info("VPC: %s", vpc_id)
    logging.info("Creating temporary key pair...")
    state.key_material = create_key_pair(ctx.ec2, key_name, tags)
    logging.info("Creating temporary security group...")
    sg_name = f"ami-builder-{ctx.unique_id}"
    state.sg_id = create_security_group(ctx.ec2, vpc_id, sg_name, tags)
    logging.info("Creating launch template...")
    lt_params = LaunchTemplateParams(
        template_name, ctx.args.source_ami, state.sg_id, key_name,
        ctx.args.iam_instance_profile,
    )
    create_launch_template(ctx.ec2, lt_params, tags)
    num_types = len(ctx.args.instance_types)
    num_subnets = len(subnet_ids)
    msg = "Creating EC2 Fleet with %d instance types x %d subnets..."
    logging.info(msg, num_types, num_subnets)
    state.instance_id = create_fleet_instance(
        ctx.ec2, template_name, ctx.args.instance_types, subnet_ids
    )
    logging.info("Instance launched: %s", state.instance_id)
    public_ip = wait_for_instance(ctx.ec2, state.instance_id)
    logging.info("Instance ready at %s", public_ip)
    script_path = ctx.script_dir / SETUP_SCRIPT
    if script_path.exists():
        logging.info("Running setup script...")
        script_params = ScriptParams(
            public_ip,
            state.key_material,
            str(script_path),
            ctx.args.runner_version,
            ctx.args.yq_version,
            ctx.args.runner_user,
        )
        run_script(script_params)
    state.result = create_ami(
        ctx.ec2, state.instance_id, ctx.args.ami_name, ctx.args.ami_description, tags
    )


def cmd_build(args: argparse.Namespace):
    """Handle the build command with parsed arguments."""
    script_dir = Path(__file__).parent
    script_path = script_dir / SETUP_SCRIPT
    exit_code = 1
    if not script_path.exists():
        logging.error("Error: setup script not found: %s", script_path)
    else:
        unique_id = uuid.uuid4().hex[:8]
        ec2 = boto3.client("ec2", region_name=args.region)
        args.subnet_ids = [s.strip() for s in args.subnet_ids.split(",")]
        args.instance_types = [t.strip() for t in args.instance_types.split(",")]
        logging.info("Looking up AMI ID for: %s", args.source_ami)
        ami_id = lookup_source_ami(ec2, args.source_ami)
        logging.info("Found AMI ID: %s", ami_id)
        args.source_ami = ami_id
        ctx = BuildContext(ec2, args, script_dir, unique_id)
        state = BuildState()
        try:
            run_build(ctx, state)
        finally:
            template_name = f"ami-builder-{unique_id}"
            key_name = f"ami-builder-{unique_id}"
            cleanup(ctx.ec2, state.instance_id, template_name, key_name, state.sg_id)
        if state.result:
            print(f"AMI_ID={state.result}")
            logging.info("Done.")
            exit_code = 0
    return exit_code


def main():
    """Parse command line arguments and run the AMI build."""
    desc = "Build AMI using EC2 Fleet spot instances"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--ami-name", required=True, help="Name for the created AMI")
    parser.add_argument("--ami-description", help="Description for the created AMI")
    parser.add_argument("--region", required=True, help="AWS region")
    parser.add_argument("--source-ami", required=True, help="Source AMI name to look up")
    parser.add_argument("--subnet-ids", required=True, help="Comma-separated subnet IDs")
    parser.add_argument("--instance-types", required=True, help="Comma-separated instance types")
    parser.add_argument("--runner-version", required=True, help="GitHub runner version")
    parser.add_argument("--yq-version", required=True, help="yq version")
    parser.add_argument("--runner-user", required=True, help="Username for GitHub runner")
    parser.add_argument("--iam-instance-profile", help="IAM instance profile name")
    parser.add_argument("--tag", action="append", metavar="KEY=VALUE", help="Tag to apply")
    args = parser.parse_args()
    return cmd_build(args)


if __name__ == "__main__":
    sys.exit(main())
