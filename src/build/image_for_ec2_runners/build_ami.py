#!/usr/bin/env python3
import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from io import StringIO
from typing import Any, Optional
import boto3
import paramiko
import yaml


@dataclass
class LaunchTemplateParams:
    template_name: str
    base_ami: str
    sg_id: str
    key_name: str
    iam_profile: Optional[str]


@dataclass
class CommandParams:
    ip_addr: str
    key_material: str
    commands: str

REQUIRED_FIELDS = ["ami_name", "region", "source_ami", "subnet_ids", "instance_types"]


def validate_commands(config):
    errors = []
    commands = config.get("commands")
    if commands is not None and not isinstance(commands, str):
        errors.append("commands must be a string (use YAML block scalar |)")
    return errors


def validate_config(config):
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    if "instance_types" in config:
        if not isinstance(config["instance_types"], list):
            errors.append("instance_types must be a list")
        elif not config["instance_types"]:
            errors.append("instance_types cannot be empty")
    if "subnet_ids" in config:
        if not isinstance(config["subnet_ids"], list):
            errors.append("subnet_ids must be a list")
        elif not config["subnet_ids"]:
            errors.append("subnet_ids cannot be empty")
    errors.extend(validate_commands(config))
    if "tags" in config and not isinstance(config["tags"], dict):
        errors.append("tags must be a dict")
    return errors


def get_vpc_from_subnet(ec2, subnet_id):
    response = ec2.describe_subnets(SubnetIds=[subnet_id])
    return response["Subnets"][0]["VpcId"]


def lookup_source_ami(ec2, ami_name):
    response = ec2.describe_images(
        Owners=["136693071363"],
        Filters=[
            {"Name": "name", "Values": [ami_name]},
        ],
    )
    if not response["Images"]:
        raise RuntimeError(f"No AMI found with name: {ami_name}")
    return response["Images"][0]["ImageId"]


def create_key_pair(ec2, key_name):
    response = ec2.create_key_pair(KeyName=key_name, KeyType="ed25519")
    return response["KeyMaterial"]


def delete_key_pair(ec2, key_name):
    ec2.delete_key_pair(KeyName=key_name)


def create_security_group(ec2, vpc_id, group_name):
    response = ec2.create_security_group(
        GroupName=group_name,
        Description="Temporary SG for AMI builder",
        VpcId=vpc_id,
    )
    sg_id = response["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}],
    )
    return sg_id


def delete_security_group(ec2, sg_id):
    deleted = False
    attempts = 0
    while not deleted and attempts < 12:
        try:
            ec2.delete_security_group(GroupId=sg_id)
            deleted = True
        except ec2.exceptions.ClientError:
            time.sleep(5)
        attempts += 1


def create_launch_template(ec2, params: LaunchTemplateParams):
    data: dict[str, Any] = {"ImageId": params.base_ami, "KeyName": params.key_name, "SecurityGroupIds": [params.sg_id]}
    if params.iam_profile:
        data["IamInstanceProfile"] = {"Name": params.iam_profile}
    ec2.create_launch_template(LaunchTemplateName=params.template_name, LaunchTemplateData=data)


def delete_launch_template(ec2, template_name):
    ec2.delete_launch_template(LaunchTemplateName=template_name)


def create_fleet_instance(ec2, template_name, instance_types, subnet_ids):
    overrides = [{"InstanceType": it, "SubnetId": sn} for it in instance_types for sn in subnet_ids]
    response = ec2.create_fleet(
        Type="instant",
        TargetCapacitySpecification={"TotalTargetCapacity": 1, "DefaultTargetCapacityType": "spot"},
        SpotOptions={"AllocationStrategy": "price-capacity-optimized"},
        LaunchTemplateConfigs=[{
            "LaunchTemplateSpecification": {"LaunchTemplateName": template_name, "Version": "$Latest"},
            "Overrides": overrides,
        }],
    )
    if response.get("Errors"):
        raise RuntimeError(f"Fleet errors: {response['Errors']}")
    return response["Instances"][0]["InstanceIds"][0]


def wait_for_instance(ec2, instance_id):
    print(f"Waiting for instance {instance_id} to be running...")
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])
    print("Waiting for status checks...")
    waiter = ec2.get_waiter("instance_status_ok")
    waiter.wait(InstanceIds=[instance_id])
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["PublicIpAddress"]


def run_ssh_command(client, cmd):
    print(f"Running: {cmd[:80]}{'...' if len(cmd) > 80 else ''}")
    _, stdout, stderr = client.exec_command(cmd, timeout=600)
    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        print(f"STDOUT: {stdout.read().decode()}")
        print(f"STDERR: {stderr.read().decode()}")
        raise RuntimeError(f"Command failed with exit code {exit_code}")


def parse_commands(commands_str):
    lines = []
    for line in commands_str.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def run_commands(params: CommandParams):
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
    for cmd in parse_commands(params.commands):
        run_ssh_command(client, cmd)
    client.close()


def create_ami(ec2, instance_id, ami_name, ami_description, tags):
    response = ec2.create_image(InstanceId=instance_id, Name=ami_name, Description=ami_description or "")
    ami_id = response["ImageId"]
    print(f"Creating AMI {ami_id}...")
    waiter = ec2.get_waiter("image_available")
    waiter.wait(ImageIds=[ami_id])
    if tags:
        tag_list = [{"Key": k, "Value": str(v)} for k, v in tags.items()]
        ec2.create_tags(Resources=[ami_id], Tags=tag_list)
        snapshots = ec2.describe_images(ImageIds=[ami_id])["Images"][0].get("BlockDeviceMappings", [])
        for bdm in snapshots:
            if "Ebs" in bdm:
                ec2.create_tags(Resources=[bdm["Ebs"]["SnapshotId"]], Tags=tag_list)
    return ami_id


def terminate_instance(ec2, instance_id):
    ec2.terminate_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_terminated")
    waiter.wait(InstanceIds=[instance_id])


def cleanup(ec2, instance_id, template_name, key_name, sg_id):
    if instance_id:
        print("Terminating temporary instance...")
        terminate_instance(ec2, instance_id)
    try:
        delete_launch_template(ec2, template_name)
    except boto3.exceptions.Boto3Error:
        pass
    try:
        print("Deleting temporary key pair...")
        delete_key_pair(ec2, key_name)
    except boto3.exceptions.Boto3Error:
        pass
    if sg_id:
        print("Deleting temporary security group...")
        delete_security_group(ec2, sg_id)


def load_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_value(value_str):
    result = value_str
    try:
        result = json.loads(value_str)
    except json.JSONDecodeError:
        pass
    return result


def apply_vars(config, var_list):
    csv_keys = {"instance_types", "subnet_ids"}
    for item in var_list or []:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key in csv_keys:
            parsed_value = [v.strip() for v in value.split(",")]
        elif key.startswith("tags."):
            child_key = key[5:]
            if "tags" not in config:
                config["tags"] = {}
            config["tags"][child_key] = parse_value(value)
            continue
        else:
            parsed_value = parse_value(value)
        config[key] = parsed_value


def cmd_validate(args):
    config = load_config(args.config)
    apply_vars(config, args.var)
    errors = validate_config(config)
    exit_code = 0
    if errors:
        for err in errors:
            print(f"Error: {err}", file=sys.stderr)
        exit_code = 1
    else:
        print("Configuration is valid.")
    return exit_code


@dataclass
class BuildState:
    instance_id: Optional[str] = None
    sg_id: Optional[str] = None
    key_material: Optional[str] = None
    result: Optional[str] = None


@dataclass
class BuildContext:
    ec2: object
    config: dict
    unique_id: str


def run_build(ctx: BuildContext, state: BuildState):
    key_name = f"ami-builder-{ctx.unique_id}"
    template_name = f"ami-builder-{ctx.unique_id}"
    subnet_ids = ctx.config["subnet_ids"]
    print(f"Subnets: {subnet_ids}")
    vpc_id = get_vpc_from_subnet(ctx.ec2, subnet_ids[0])
    print(f"VPC: {vpc_id}")
    print("Creating temporary key pair...")
    state.key_material = create_key_pair(ctx.ec2, key_name)
    print("Creating temporary security group...")
    state.sg_id = create_security_group(ctx.ec2, vpc_id, f"ami-builder-{ctx.unique_id}")
    print("Creating launch template...")
    lt_params = LaunchTemplateParams(template_name, ctx.config["source_ami"], state.sg_id, key_name, ctx.config.get("iam_instance_profile"))
    create_launch_template(ctx.ec2, lt_params)
    print(f"Creating EC2 Fleet with {len(ctx.config['instance_types'])} instance types x {len(subnet_ids)} subnets...")
    state.instance_id = create_fleet_instance(ctx.ec2, template_name, ctx.config["instance_types"], subnet_ids)
    print(f"Instance launched: {state.instance_id}")
    public_ip = wait_for_instance(ctx.ec2, state.instance_id)
    print(f"Instance ready at {public_ip}")
    if ctx.config.get("commands"):
        print("Running commands...")
        cmd_params = CommandParams(public_ip, state.key_material, ctx.config["commands"])
        run_commands(cmd_params)
    print("Creating AMI...")
    state.result = create_ami(ctx.ec2, state.instance_id, ctx.config["ami_name"], ctx.config.get("ami_description"), ctx.config.get("tags", {}))
    print(f"ami_id={state.result}")


def cmd_build(args):
    config = load_config(args.config)
    apply_vars(config, args.var)
    errors = validate_config(config)
    exit_code = 1
    if errors:
        for err in errors:
            print(f"Error: {err}", file=sys.stderr)
    else:
        unique_id = uuid.uuid4().hex[:8]
        ec2 = boto3.client("ec2", region_name=config["region"])
        print(f"Looking up AMI ID for: {config['source_ami']}")
        ami_id = lookup_source_ami(ec2, config["source_ami"])
        print(f"Found AMI ID: {ami_id}")
        config["source_ami"] = ami_id
        ctx = BuildContext(ec2, config, unique_id)
        state = BuildState()
        try:
            run_build(ctx, state)
        finally:
            cleanup(ctx.ec2, state.instance_id, f"ami-builder-{unique_id}", f"ami-builder-{unique_id}", state.sg_id)
        if state.result:
            exit_code = 0
    return exit_code


def main():
    parser = argparse.ArgumentParser(description="Build AMI using EC2 Fleet spot instances")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="Build an AMI from config")
    build_parser.add_argument("config", help="Path to YAML config file")
    build_parser.add_argument("--var", action="append", metavar="KEY=VALUE", help="Override config value")
    validate_parser = subparsers.add_parser("validate", help="Validate config file")
    validate_parser.add_argument("config", help="Path to YAML config file")
    validate_parser.add_argument("--var", action="append", metavar="KEY=VALUE", help="Override config value")
    args = parser.parse_args()
    exit_code = 1
    if args.command == "build":
        exit_code = cmd_build(args)
    elif args.command == "validate":
        exit_code = cmd_validate(args)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
