#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
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

    subnet_az_map = {}
    for subnet_id in subnet_ids:
        response = ec2.describe_subnets(SubnetIds=[subnet_id.strip()])
        subnet_az = response['Subnets'][0]['AvailabilityZone']
        if subnet_az in supported_azs_set:
            subnet_az_map[subnet_id.strip()] = subnet_az

    if not subnet_az_map:
        return None

    candidate_azs = list(set(subnet_az_map.values()))
    response = ec2.describe_spot_price_history(
        InstanceTypes=instance_types,
        ProductDescriptions=['Linux/UNIX'],
        StartTime=datetime.now(timezone.utc),
        MaxResults=1000
    )

    az_type_count = defaultdict(int)
    for price in response['SpotPriceHistory']:
        az_type_count[price['AvailabilityZone']] += 1

    ranked_azs = sorted(candidate_azs, key=lambda az: az_type_count.get(az, 0), reverse=True)

    for az in ranked_azs:
        for subnet_id, subnet_az in subnet_az_map.items():
            if subnet_az == az:
                return subnet_id

    return list(subnet_az_map.keys())[0]

def main():
    parser = argparse.ArgumentParser(description='Find suitable subnet for instance types')
    subparsers = parser.add_subparsers(dest='command', required=True)

    check_parser = subparsers.add_parser('check', help='Check if suitable subnet exists')
    check_parser.add_argument('--instance-types', required=True, help='JSON array of instance types')
    check_parser.add_argument('--subnet-ids', required=True, help='Comma-separated list of subnet IDs')

    get_parser = subparsers.add_parser('get', help='Get suitable subnet ID')
    get_parser.add_argument('--instance-types', required=True, help='JSON array of instance types')
    get_parser.add_argument('--subnet-ids', required=True, help='Comma-separated list of subnet IDs')

    args = parser.parse_args()

    instance_types = json.loads(args.instance_types)
    subnet_ids = args.subnet_ids.split(',')

    result = find_suitable_subnet(instance_types, subnet_ids)

    if args.command == 'check':
        if result:
            sys.exit(0)
        sys.exit(1)
    if args.command == 'get':
        if result:
            print(result)
            sys.exit(0)
        print("ERROR: No suitable subnet found", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
