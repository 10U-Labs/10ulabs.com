"""Route53 hosted zone test battery for www_shared pre-deployment validation.

Tests are ordered to fail fast with maximum diagnostic granularity:
1. Zone existence verification
2. Read capability (GetHostedZone, ListResourceRecordSets)
3. Write capability (ChangeResourceRecordSets for create, modify, delete)
"""
import uuid

import pytest
from botocore.exceptions import ClientError


class TestZoneExistenceAndReadCapability:
    """Layer 1/3a: Verify zone exists and we can read from it."""

    def test_01_can_call_route53_get_hosted_zone_api(
        self, route53_client, hosted_zone_id
    ):
        """Verify we have permission to call route53:GetHostedZone."""
        try:
            route53_client.get_hosted_zone(Id=hosted_zone_id)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to call route53:GetHostedZone "
                    f"on zone '{hosted_zone_id}'"
                )
            raise

    def test_02_hosted_zone_exists(self, route53_client, hosted_zone_id):
        """Verify the Route53 hosted zone exists."""
        try:
            response = route53_client.get_hosted_zone(Id=hosted_zone_id)
            zone_id_from_response = response["HostedZone"]["Id"]
            assert zone_id_from_response.endswith(hosted_zone_id), (
                f"Zone ID mismatch: expected {hosted_zone_id}, "
                f"got {zone_id_from_response}"
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchHostedZone":
                pytest.fail(f"Hosted zone '{hosted_zone_id}' does not exist")
            raise

    def test_03_can_list_resource_record_sets(self, route53_client, hosted_zone_id):
        """Verify we can call route53:ListResourceRecordSets."""
        try:
            response = route53_client.list_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                MaxItems="1"
            )
            assert "ResourceRecordSets" in response
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to call route53:ListResourceRecordSets "
                    f"on zone '{hosted_zone_id}'"
                )
            raise


class TestWriteCapability:
    """Layer 3b: Verify we can write to the hosted zone."""

    @pytest.fixture
    def zone_name(self, route53_client, hosted_zone_id):
        """Get the zone name for constructing test record names."""
        response = route53_client.get_hosted_zone(Id=hosted_zone_id)
        return response["HostedZone"]["Name"]

    @pytest.fixture
    def test_record_name(self, zone_name):
        """Generate a unique test record name."""
        unique_id = str(uuid.uuid4())[:8]
        return f"_pre-deployment-test-{unique_id}.{zone_name}"

    def test_01_can_create_record(
        self, route53_client, hosted_zone_id, test_record_name
    ):
        """Verify we can call route53:ChangeResourceRecordSets to create."""
        try:
            response = route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    "Comment": "Pre-deployment capability test - create",
                    "Changes": [{
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": test_record_name,
                            "Type": "TXT",
                            "TTL": 60,
                            "ResourceRecords": [
                                {"Value": '"pre-deployment-test-v1"'}
                            ]
                        }
                    }]
                }
            )
            assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to create records in zone '{hosted_zone_id}'"
                )
            raise
        finally:
            try:
                route53_client.change_resource_record_sets(
                    HostedZoneId=hosted_zone_id,
                    ChangeBatch={
                        "Changes": [{
                            "Action": "DELETE",
                            "ResourceRecordSet": {
                                "Name": test_record_name,
                                "Type": "TXT",
                                "TTL": 60,
                                "ResourceRecords": [
                                    {"Value": '"pre-deployment-test-v1"'}
                                ]
                            }
                        }]
                    }
                )
            except ClientError:
                pass

    def test_02_can_modify_record(
        self, route53_client, hosted_zone_id, test_record_name
    ):
        """Verify we can call route53:ChangeResourceRecordSets to upsert."""
        try:
            route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    "Comment": "Pre-deployment capability test - setup",
                    "Changes": [{
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": test_record_name,
                            "Type": "TXT",
                            "TTL": 60,
                            "ResourceRecords": [
                                {"Value": '"pre-deployment-test-v1"'}
                            ]
                        }
                    }]
                }
            )
            response = route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    "Comment": "Pre-deployment capability test - upsert",
                    "Changes": [{
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": test_record_name,
                            "Type": "TXT",
                            "TTL": 60,
                            "ResourceRecords": [
                                {"Value": '"pre-deployment-test-v2"'}
                            ]
                        }
                    }]
                }
            )
            assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to modify records in zone '{hosted_zone_id}'"
                )
            raise
        finally:
            try:
                route53_client.change_resource_record_sets(
                    HostedZoneId=hosted_zone_id,
                    ChangeBatch={
                        "Changes": [{
                            "Action": "DELETE",
                            "ResourceRecordSet": {
                                "Name": test_record_name,
                                "Type": "TXT",
                                "TTL": 60,
                                "ResourceRecords": [
                                    {"Value": '"pre-deployment-test-v2"'}
                                ]
                            }
                        }]
                    }
                )
            except ClientError:
                pass

    def test_03_can_delete_record(
        self, route53_client, hosted_zone_id, test_record_name
    ):
        """Verify we can call route53:ChangeResourceRecordSets to delete."""
        try:
            route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    "Comment": "Pre-deployment capability test - setup",
                    "Changes": [{
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": test_record_name,
                            "Type": "TXT",
                            "TTL": 60,
                            "ResourceRecords": [
                                {"Value": '"pre-deployment-test-delete"'}
                            ]
                        }
                    }]
                }
            )
            response = route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    "Comment": "Pre-deployment capability test - delete",
                    "Changes": [{
                        "Action": "DELETE",
                        "ResourceRecordSet": {
                            "Name": test_record_name,
                            "Type": "TXT",
                            "TTL": 60,
                            "ResourceRecords": [
                                {"Value": '"pre-deployment-test-delete"'}
                            ]
                        }
                    }]
                }
            )
            assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                pytest.fail(
                    f"No permission to delete records in zone '{hosted_zone_id}'"
                )
            raise
