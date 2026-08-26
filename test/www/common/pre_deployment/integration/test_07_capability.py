import uuid

import pytest
from botocore.exceptions import ClientError


@pytest.fixture(name="test_object_key")
def object_key_fixture():
    return f".pre-deployment-test/{uuid.uuid4()}.txt"


@pytest.fixture(name="zone_name")
def zone_name_fixture(route53_client, hosted_zone_id):
    response = route53_client.get_hosted_zone(Id=hosted_zone_id)
    return response["HostedZone"]["Name"]


@pytest.fixture(name="test_record_name")
def record_name_fixture(zone_name):
    unique_id = str(uuid.uuid4())[:8]
    return f"_pre-deployment-test-{unique_id}.{zone_name}"


def test_can_list_objects_in_state_bucket(s3_client, state_bucket_name):
    try:
        response = s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        assert "Contents" in response or "KeyCount" in response
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:ListObjectsV2 on '{state_bucket_name}'")
        raise


def test_can_get_object_from_state_bucket(s3_client, state_bucket_name):
    try:
        response = s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        if not response.get("Contents"):
            pytest.skip("No objects in bucket to test GetObject")
        key = response["Contents"][0]["Key"]
        obj_response = s3_client.get_object(Bucket=state_bucket_name, Key=key)
        assert obj_response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:GetObject on '{state_bucket_name}'")
        raise


def test_can_put_object_to_state_bucket(s3_client, state_bucket_name, test_object_key):
    try:
        response = s3_client.put_object(
            Bucket=state_bucket_name,
            Key=test_object_key,
            Body=b"pre-deployment capability test"
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:PutObject on '{state_bucket_name}'")
        raise
    finally:
        s3_client.delete_object(Bucket=state_bucket_name, Key=test_object_key)


def test_can_delete_object_from_state_bucket(s3_client, state_bucket_name, test_object_key):
    try:
        s3_client.put_object(
            Bucket=state_bucket_name,
            Key=test_object_key,
            Body=b"pre-deployment capability test"
        )
        response = s3_client.delete_object(Bucket=state_bucket_name, Key=test_object_key)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 204
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to call s3:DeleteObject on '{state_bucket_name}'")
        raise
    finally:
        s3_client.delete_object(Bucket=state_bucket_name, Key=test_object_key)


def _change_record(route53_client, hosted_zone_id, record_name, action, value, comment):
    return route53_client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            "Comment": f"Pre-deployment capability test - {comment}",
            "Changes": [{
                "Action": action,
                "ResourceRecordSet": {
                    "Name": record_name,
                    "Type": "TXT",
                    "TTL": 60,
                    "ResourceRecords": [{"Value": f'"{value}"'}]
                }
            }]
        }
    )


def test_can_create_route53_record(route53_client, hosted_zone_id, test_record_name):
    try:
        response = _change_record(
            route53_client, hosted_zone_id, test_record_name,
            "CREATE", "pre-deployment-test-v1", "create",
        )
        assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to create records in zone '{hosted_zone_id}'")
        raise
    finally:
        _change_record(
            route53_client, hosted_zone_id, test_record_name,
            "DELETE", "pre-deployment-test-v1", "cleanup",
        )


def test_can_upsert_route53_record(route53_client, hosted_zone_id, test_record_name):
    try:
        _change_record(
            route53_client, hosted_zone_id, test_record_name,
            "CREATE", "pre-deployment-test-v1", "setup",
        )
        response = _change_record(
            route53_client, hosted_zone_id, test_record_name,
            "UPSERT", "pre-deployment-test-v2", "upsert",
        )
        assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to modify records in zone '{hosted_zone_id}'")
        raise
    finally:
        _change_record(
            route53_client, hosted_zone_id, test_record_name,
            "DELETE", "pre-deployment-test-v2", "cleanup",
        )


def test_can_delete_route53_record(route53_client, hosted_zone_id, test_record_name):
    try:
        _change_record(
            route53_client, hosted_zone_id, test_record_name,
            "CREATE", "pre-deployment-test-delete", "setup",
        )
        response = _change_record(
            route53_client, hosted_zone_id, test_record_name,
            "DELETE", "pre-deployment-test-delete", "delete",
        )
        assert response["ChangeInfo"]["Status"] in ("PENDING", "INSYNC")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            pytest.fail(f"No permission to delete records in zone '{hosted_zone_id}'")
        raise
