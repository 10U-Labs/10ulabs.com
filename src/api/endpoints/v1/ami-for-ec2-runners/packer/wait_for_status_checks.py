#!/usr/bin/env python3
import subprocess
import sys
import time
import urllib.error
import urllib.request


def get_imds_token():
    req = urllib.request.Request(
        'http://169.254.169.254/latest/api/token',
        method='PUT',
        headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.read().decode('utf-8')


def get_metadata(token, path):
    req = urllib.request.Request(
        f'http://169.254.169.254/latest/meta-data/{path}',
        headers={'X-aws-ec2-metadata-token': token}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.read().decode('utf-8')


def main():
    print("Waiting for EC2 instance status checks to pass...")

    try:
        token = get_imds_token()
        instance_id = get_metadata(token, 'instance-id')
        region = get_metadata(token, 'placement/region')
    except (urllib.error.URLError, OSError) as e:
        print(f"Error getting instance metadata: {e}")
        sys.exit(1)

    print(f"Instance ID: {instance_id}")
    print(f"Region: {region}")

    poll_interval = 15
    max_attempts = 20

    for attempt in range(1, max_attempts + 1):
        print(f"Checking status (attempt {attempt}/{max_attempts})...")

        result = subprocess.run([
            'aws', 'ec2', 'describe-instance-status',
            '--instance-ids', instance_id,
            '--region', region,
            '--query', 'InstanceStatuses[0].[InstanceStatus.Status,SystemStatus.Status]',
            '--output', 'text'
        ], capture_output=True, text=True, check=False)

        if result.returncode == 0 and result.stdout.strip():
            statuses = result.stdout.strip().split()
            if len(statuses) >= 2:
                instance_status = statuses[0]
                system_status = statuses[1]

                print(f"  Instance Status: {instance_status}")
                print(f"  System Status: {system_status}")

                if instance_status == 'ok' and system_status == 'ok':
                    print("All status checks passed")
                    return 0

        if attempt == max_attempts:
            print(f"Status checks did not pass after {max_attempts} attempts")
            sys.exit(1)

        print(f"  Status not ready - waiting {poll_interval}s before retry...")
        time.sleep(poll_interval)

    print("Instance is ready for provisioning")
    return 0


if __name__ == '__main__':
    sys.exit(main())
