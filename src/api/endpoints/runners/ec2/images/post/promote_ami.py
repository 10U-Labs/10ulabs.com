#!/usr/bin/env python3
"""Script to promote an AMI by tagging it as stable."""
import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def promote_ami(ami_id: str, region: str, tag_key: str) -> int:
    """Promote an AMI by tagging it as stable."""
    ec2_client = boto3.client('ec2', region_name=region)

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

    return exit_code


def main():
    """Parse command line arguments and run AMI promotion."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--ami-id', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--tag-key', required=True)
    args = parser.parse_args()

    result = promote_ami(args.ami_id, args.region, args.tag_key)
    sys.exit(result)


if __name__ == '__main__':
    main()
