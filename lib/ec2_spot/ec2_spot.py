import time
import uuid
from typing import Any
from botocore.exceptions import ClientError


class SpotTerminationError(Exception):
    pass


class SpotCapacityError(Exception):
    pass


def get_subnet_az(ec2_client: Any, subnet_id: str) -> str:
    response = ec2_client.describe_subnets(SubnetIds=[subnet_id])
    return response["Subnets"][0]["AvailabilityZone"]


def get_subnet_azs(ec2_client: Any, subnet_ids: list[str]) -> dict[str, str]:
    result = {}
    if subnet_ids:
        response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        for subnet in response["Subnets"]:
            result[subnet["SubnetId"]] = subnet["AvailabilityZone"]
    return result


def filter_subnets_by_az(
    ec2_client: Any, subnet_ids: list[str], excluded_azs: list[str]
) -> list[str]:
    result = subnet_ids
    if excluded_azs:
        subnet_azs = get_subnet_azs(ec2_client, subnet_ids)
        result = [s for s in subnet_ids if subnet_azs.get(s) not in excluded_azs]
    return result


def create_launch_template(
    ec2_client: Any, template_name: str, config: dict[str, Any]
) -> str:
    template_data: dict[str, Any] = {"ImageId": config["ami_id"]}
    if "security_group_id" in config:
        template_data["SecurityGroupIds"] = [config["security_group_id"]]
    if "key_name" in config:
        template_data["KeyName"] = config["key_name"]
    if "iam_instance_profile" in config:
        template_data["IamInstanceProfile"] = {"Name": config["iam_instance_profile"]}
    if "user_data" in config:
        template_data["UserData"] = config["user_data"]
    if "block_device_mappings" in config:
        template_data["BlockDeviceMappings"] = config["block_device_mappings"]
    if "metadata_options" in config:
        template_data["MetadataOptions"] = config["metadata_options"]
    else:
        template_data["MetadataOptions"] = {
            "HttpTokens": "required",
            "HttpEndpoint": "enabled",
        }
    if "tag_specifications" in config:
        template_data["TagSpecifications"] = config["tag_specifications"]
    tag_specs = []
    if "template_tags" in config:
        tag_specs = [
            {
                "ResourceType": "launch-template",
                "Tags": [{"Key": k, "Value": str(v)} for k, v in config["template_tags"].items()],
            }
        ]
    response = ec2_client.create_launch_template(
        LaunchTemplateName=template_name,
        LaunchTemplateData=template_data,
        TagSpecifications=tag_specs if tag_specs else [],
    )
    return response["LaunchTemplate"]["LaunchTemplateId"]


def delete_launch_template(ec2_client: Any, template_id: str) -> None:
    try:
        ec2_client.delete_launch_template(LaunchTemplateId=template_id)
    except ClientError:
        pass


def create_fleet_instance(
    ec2_client: Any,
    template_id: str,
    instance_types: list[str],
    subnet_ids: list[str],
    allocation_strategy: str = "capacity-optimized",
    max_price: str | None = None,
) -> str:
    overrides = []
    for instance_type in instance_types:
        for subnet_id in subnet_ids:
            override: dict[str, Any] = {
                "InstanceType": instance_type,
                "SubnetId": subnet_id,
            }
            if max_price:
                override["MaxPrice"] = max_price
            overrides.append(override)
    response = ec2_client.create_fleet(
        Type="instant",
        TargetCapacitySpecification={
            "TotalTargetCapacity": 1,
            "DefaultTargetCapacityType": "spot",
        },
        SpotOptions={"AllocationStrategy": allocation_strategy},
        LaunchTemplateConfigs=[
            {
                "LaunchTemplateSpecification": {
                    "LaunchTemplateId": template_id,
                    "Version": "$Latest",
                },
                "Overrides": overrides,
            }
        ],
    )
    instances = response.get("Instances", [])
    result = ""
    if instances and instances[0].get("InstanceIds"):
        result = instances[0]["InstanceIds"][0]
    else:
        errors = response.get("Errors", [])
        error_msg = "; ".join([e.get("ErrorMessage", str(e)) for e in errors]) if errors else "No instances launched"
        raise SpotCapacityError(error_msg)
    return result


def get_instance_state(ec2_client: Any, instance_id: str) -> str:
    result = "unknown"
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if response["Reservations"] and response["Reservations"][0]["Instances"]:
            result = response["Reservations"][0]["Instances"][0]["State"]["Name"]
    except ClientError:
        pass
    return result


def get_instance_az(ec2_client: Any, instance_id: str) -> str:
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["Placement"]["AvailabilityZone"]


def is_spot_terminated(ec2_client: Any, instance_id: str) -> bool:
    result = False
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if response["Reservations"] and response["Reservations"][0]["Instances"]:
            instance = response["Reservations"][0]["Instances"][0]
            state = instance["State"]["Name"]
            state_reason = instance.get("StateReason", {}).get("Code", "")
            if state in ("terminated", "shutting-down") and "Spot" in state_reason:
                result = True
    except ClientError:
        pass
    return result


def wait_for_instance_running(
    ec2_client: Any, instance_id: str, max_attempts: int = 60, poll_interval: int = 5
) -> None:
    running = False
    attempt = 0
    while not running and attempt < max_attempts:
        state = get_instance_state(ec2_client, instance_id)
        if state == "running":
            running = True
        elif state in ("terminated", "shutting-down"):
            if is_spot_terminated(ec2_client, instance_id):
                raise SpotTerminationError(f"Instance {instance_id} was terminated due to spot interruption")
            raise RuntimeError(f"Instance {instance_id} entered {state} state")
        else:
            time.sleep(poll_interval)
        attempt = attempt + 1
    if not running:
        raise RuntimeError(f"Instance {instance_id} did not reach running state after {max_attempts} attempts")


def wait_for_status_checks(
    ec2_client: Any, instance_id: str, max_attempts: int = 40, poll_interval: int = 15
) -> None:
    passed = False
    attempt = 0
    while not passed and attempt < max_attempts:
        state = get_instance_state(ec2_client, instance_id)
        if state in ("terminated", "shutting-down"):
            if is_spot_terminated(ec2_client, instance_id):
                raise SpotTerminationError(f"Instance {instance_id} was terminated due to spot interruption")
            raise RuntimeError(f"Instance {instance_id} entered {state} state")
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        if response.get("InstanceStatuses"):
            status = response["InstanceStatuses"][0]
            system_status = status.get("SystemStatus", {}).get("Status", "")
            instance_status = status.get("InstanceStatus", {}).get("Status", "")
            if system_status == "ok" and instance_status == "ok":
                passed = True
        if not passed:
            time.sleep(poll_interval)
        attempt = attempt + 1
    if not passed:
        raise RuntimeError(f"Instance {instance_id} did not pass status checks after {max_attempts} attempts")


def terminate_instance(ec2_client: Any, instance_id: str) -> None:
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except ClientError:
        pass


def launch_spot_instance(
    ec2_client: Any,
    launch_template_config: dict[str, Any],
    instance_types: list[str],
    subnet_ids: list[str],
    allocation_strategy: str = "capacity-optimized",
    max_price: str | None = None,
) -> str:
    template_name = f"spot-launch-{uuid.uuid4().hex[:8]}"
    template_id = create_launch_template(ec2_client, template_name, launch_template_config)
    instance_id = ""
    try:
        instance_id = create_fleet_instance(
            ec2_client, template_id, instance_types, subnet_ids, allocation_strategy, max_price
        )
    finally:
        delete_launch_template(ec2_client, template_id)
    return instance_id


def launch_spot_instance_with_retry(
    ec2_client: Any,
    launch_template_config: dict[str, Any],
    instance_types: list[str],
    subnet_ids: list[str],
    allocation_strategy: str = "capacity-optimized",
    max_price: str | None = None,
    max_retries: int = 2,
    wait_for_ready: bool = True,
) -> str:
    excluded_azs: list[str] = []
    attempt = 0
    instance_id = ""
    last_error: Exception | None = None
    while not instance_id and attempt <= max_retries:
        available_subnets = filter_subnets_by_az(ec2_client, subnet_ids, excluded_azs)
        if not available_subnets:
            break
        current_instance_id = ""
        try:
            current_instance_id = launch_spot_instance(
                ec2_client,
                launch_template_config,
                instance_types,
                available_subnets,
                allocation_strategy,
                max_price,
            )
            if wait_for_ready:
                wait_for_instance_running(ec2_client, current_instance_id)
                wait_for_status_checks(ec2_client, current_instance_id)
            instance_id = current_instance_id
        except SpotTerminationError:
            if current_instance_id:
                try:
                    az = get_instance_az(ec2_client, current_instance_id)
                    excluded_azs.append(az)
                except ClientError:
                    pass
                terminate_instance(ec2_client, current_instance_id)
            last_error = SpotTerminationError(f"Spot instance terminated in attempt {attempt + 1}")
        except SpotCapacityError as e:
            last_error = e
        attempt = attempt + 1
    if not instance_id:
        error_msg = str(last_error) if last_error else "No subnets available"
        raise SpotCapacityError(f"Failed to launch spot instance after {attempt} attempts: {error_msg}")
    return instance_id
