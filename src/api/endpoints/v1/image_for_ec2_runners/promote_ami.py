#!/usr/bin/env python3
import argparse
import sys
import boto3


def promote_ami(ami_id: str, region: str, run_id: str) -> int:
    ec2_client = boto3.client('ec2', region_name=region)
    ssm_client = boto3.client('ssm', region_name=region)

    try:
        print(f"Tagging AMI {ami_id} as stable")
        ec2_client.create_tags(
            Resources=[ami_id],
            Tags=[{'Key': 'stable', 'Value': 'true'}]
        )
        print(f"AMI {ami_id} tagged as stable")
    except Exception as e:
        print(f"Error tagging AMI: {e}")
        return 1

    try:
        print(f"Updating SSM Parameter /github-runner/ami/latest with {ami_id}")
        ssm_client.put_parameter(
            Name='/github-runner/ami/latest',
            Value=ami_id,
            Type='String',
            Overwrite=True,
            Description=f"Latest stable GitHub runner AMI (updated by workflow run {run_id})"
        )
        print("SSM Parameter updated successfully")
    except Exception as e:
        print(f"Error updating SSM parameter: {e}")
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ami-id', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()

    result = promote_ami(args.ami_id, args.region, args.run_id)
    sys.exit(result)


if __name__ == '__main__':
    main()
