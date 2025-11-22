#!/usr/bin/env python3
import argparse
import json
import sys
import boto3

def find_suitable_subnet(instance_types, subnet_ids):
    ec2 = boto3.client('ec2')

    supported_azs_set = set()
    for instance_type in instance_types:
        response = ec2.describe_instance_type_offerings(
            LocationType='availability-zone',
            Filters=[{'Name': 'instance-type', 'Values': [instance_type]}]
        )
        azs = [offering['Location'] for offering in response['InstanceTypeOfferings']]
        supported_azs_set.update(azs)

    if not supported_azs_set:
        return None

    for subnet_id in subnet_ids:
        response = ec2.describe_subnets(SubnetIds=[subnet_id.strip()])
        subnet_az = response['Subnets'][0]['AvailabilityZone']
        if subnet_az in supported_azs_set:
            return subnet_id.strip()

    return None

def main():
    parser = argparse.ArgumentParser(description='Find suitable subnet for instance types')
    parser.add_argument('--instance-types', required=True, help='JSON array of instance types')
    parser.add_argument('--subnet-ids', required=True, help='Comma-separated list of subnet IDs')

    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('check', help='Check if suitable subnet exists')
    subparsers.add_parser('get', help='Get suitable subnet ID')

    args = parser.parse_args()

    instance_types = json.loads(args.instance_types)
    subnet_ids = args.subnet_ids.split(',')

    result = find_suitable_subnet(instance_types, subnet_ids)

    if args.command == 'check':
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.command == 'get':
        if result:
            print(result)
            sys.exit(0)
        else:
            print("ERROR: No suitable subnet found", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
