#!/usr/bin/env python3
import sys
import json
import boto3

def main():
    if len(sys.argv) != 3:
        print("Usage: find_suitable_subnet.py <instance_types_json> <subnet_ids_csv>", file=sys.stderr)
        sys.exit(1)

    instance_types = json.loads(sys.argv[1])
    subnet_ids = sys.argv[2].split(',')

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
        print(f"ERROR: No AZs found supporting instance types {instance_types}", file=sys.stderr)
        sys.exit(1)

    print(f"AZs supporting {instance_types}: {sorted(supported_azs_set)}", file=sys.stderr)

    for subnet_id in subnet_ids:
        response = ec2.describe_subnets(SubnetIds=[subnet_id.strip()])
        subnet_az = response['Subnets'][0]['AvailabilityZone']
        print(f"Checking subnet {subnet_id} in AZ {subnet_az}", file=sys.stderr)
        if subnet_az in supported_azs_set:
            print(f"Found suitable subnet {subnet_id} in supported AZ {subnet_az}", file=sys.stderr)
            print(subnet_id)
            sys.exit(0)

    print("ERROR: No suitable subnet found in any supported AZ", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    main()
