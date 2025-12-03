from botocore.exceptions import ClientError


class TestSubnetsExist:
    def test_all_subnets_exist_in_aws(self, ec2_client, subnet_ids):
        all_exist = False
        if subnet_ids:
            try:
                response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
                found_count = len(response.get("Subnets", []))
                all_exist = found_count == len(subnet_ids)
            except ClientError:
                all_exist = False
        assert all_exist

    def test_subnets_are_available(self, ec2_client, subnet_ids):
        all_available = False
        if subnet_ids:
            try:
                response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
                subnets = response.get("Subnets", [])
                if subnets:
                    all_available = all(s.get("State") == "available" for s in subnets)
            except ClientError:
                all_available = False
        assert all_available

    def test_subnets_have_available_ips(self, ec2_client, subnet_ids):
        have_ips = False
        if subnet_ids:
            try:
                response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
                subnets = response.get("Subnets", [])
                if subnets:
                    have_ips = all(s.get("AvailableIpAddressCount", 0) > 0 for s in subnets)
            except ClientError:
                have_ips = False
        assert have_ips

    def test_subnets_are_public(self, ec2_client, subnet_ids):
        are_public = False
        if subnet_ids:
            try:
                response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
                subnets = response.get("Subnets", [])
                if subnets:
                    are_public = all(s.get("MapPublicIpOnLaunch", False) for s in subnets)
            except ClientError:
                are_public = False
        assert are_public
