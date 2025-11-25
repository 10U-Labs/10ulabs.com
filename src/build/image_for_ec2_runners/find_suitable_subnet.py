#!/usr/bin/env python3
import argparse
import json
import sys
import boto3

def get_supported_azs(ec2, instance_types):
    supported_azs = set()
    for instance_type in instance_types:
        response = ec2.describe_instance_type_offerings(
            LocationType='availability-zone',
            Filters=[{'Name': 'instance-type', 'Values': [instance_type]}]
        )
        supported_azs.update(o['Location'] for o in response['InstanceTypeOfferings'])
    return supported_azs

def get_subnet_az_map(ec2, subnet_ids, supported_azs):
    subnet_az_map = {}
    for subnet_id in subnet_ids:
        response = ec2.describe_subnets(SubnetIds=[subnet_id.strip()])
        subnet_az = response['Subnets'][0]['AvailabilityZone']
        if subnet_az in supported_azs:
            subnet_az_map[subnet_id.strip()] = subnet_az
    return subnet_az_map

def get_az_scores(ec2, instance_types, candidate_azs):
    region = candidate_azs[0][:-1]
    response = ec2.get_spot_placement_scores(
        InstanceTypes=instance_types,
        TargetCapacity=1,
        SingleAvailabilityZone=True,
        RegionNames=[region]
    )
    az_id_scores = {
        e.get('AvailabilityZoneId'): e.get('Score', 0)
        for e in response.get('SpotPlacementScores', [])
        if e.get('AvailabilityZoneId')
    }
    az_response = ec2.describe_availability_zones(
        Filters=[{'Name': 'zone-name', 'Values': candidate_azs}]
    )
    az_name_scores = {}
    for az_info in az_response['AvailabilityZones']:
        az_name_scores[az_info['ZoneName']] = az_id_scores.get(az_info['ZoneId'], 0)
    return az_name_scores

def find_suitable_subnet(instance_types, subnet_ids):
    ec2 = boto3.client('ec2')
    supported_azs = get_supported_azs(ec2, instance_types)
    if not supported_azs:
        return None
    subnet_az_map = get_subnet_az_map(ec2, subnet_ids, supported_azs)
    if not subnet_az_map:
        return None
    candidate_azs = list(set(subnet_az_map.values()))
    az_scores = get_az_scores(ec2, instance_types, candidate_azs)
    ranked_azs = sorted(candidate_azs, key=lambda az: az_scores.get(az, 0), reverse=True)
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
