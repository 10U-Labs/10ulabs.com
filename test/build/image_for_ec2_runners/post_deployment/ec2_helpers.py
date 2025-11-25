import time
from botocore.exceptions import ClientError


def launch_spot_instance(ec2_client, config):
    run_params = {
        "ImageId": config["ami_id"],
        "InstanceType": config["instance_type"],
        "MinCount": 1,
        "MaxCount": 1,
        "SubnetId": config["subnet_id"],
        "SecurityGroupIds": [config["security_group_id"]],
        "IamInstanceProfile": {"Name": config["instance_profile"]},
        "InstanceMarketOptions": {
            "MarketType": "spot",
            "SpotOptions": {
                "MaxPrice": config["max_spot_price"],
                "SpotInstanceType": "one-time"
            }
        },
        "TagSpecifications": [{
            "ResourceType": "instance",
            "Tags": config.get("tags", [
                {"Key": "Name", "Value": "test-instance"},
                {"Key": "Purpose", "Value": "AMI Testing"},
                {"Key": "ManagedBy", "Value": "pytest"}
            ])
        }]
    }
    if "user_data" in config:
        run_params["UserData"] = config["user_data"]
    response = ec2_client.run_instances(**run_params)
    return response["Instances"][0]["InstanceId"]


def wait_for_instance_ready(ec2_client, instance_id):
    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id], WaiterConfig={"Delay": 5, "MaxAttempts": 120})
    max_wait_time = 600
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        if response["InstanceStatuses"]:
            status = response["InstanceStatuses"][0]
            instance_status = status.get("InstanceStatus", {}).get("Status", "")
            system_status = status.get("SystemStatus", {}).get("Status", "")
            if instance_status == "ok" and system_status == "ok":
                return True
        time.sleep(5)
    return False


def terminate_instance_safely(ec2_client, instance_id):
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except ClientError:
        pass
