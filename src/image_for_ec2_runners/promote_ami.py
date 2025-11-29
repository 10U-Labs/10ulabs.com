#!/usr/bin/env python3
import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def promote_ami(ami_id: str, region: str, run_id: str, ssm_parameter_name: str, tag_key: str) -> int:
    ec2_client = boto3.client('ec2', region_name=region)
    ssm_client = boto3.client('ssm', region_name=region)

    exit_code = 0

    try:
        print(f"Tagging AMI {ami_id} with {tag_key}=true")
        ec2_client.create_tags(
            Resources=[ami_id],
            Tags=[{'Key': tag_key, 'Value': 'true'}]
        )
        print(f"AMI {ami_id} tagged with {tag_key}=true")
    except ClientError as e:
        print(f"Error tagging AMI: {e}")
        exit_code = 1

    if exit_code == 0:
        try:
            print(f"Updating SSM Parameter {ssm_parameter_name} with {ami_id}")
            ssm_client.put_parameter(
                Name=ssm_parameter_name,
                Value=ami_id,
                Type='String',
                Overwrite=True,
                Description=f"Latest stable GitHub runner AMI (updated by workflow run {run_id})"
            )
            print("SSM Parameter updated successfully")
        except ClientError as e:
            print(f"Error updating SSM parameter: {e}")
            exit_code = 1

    return exit_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ami-id', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--ssm-parameter-name', required=True)
    parser.add_argument('--tag-key', required=True)
    args = parser.parse_args()

    result = promote_ami(args.ami_id, args.region, args.run_id, args.ssm_parameter_name, args.tag_key)
    sys.exit(result)


if __name__ == '__main__':
    main()
