"""Tests to validate bootstrap infrastructure exists before www_shared deployment."""


def test_bootstrap_state_bucket_accessible(s3_client, bootstrap_outputs):
    """Verify the bootstrap S3 state bucket exists and is accessible."""
    bucket_name = bootstrap_outputs.get("state_bucket_name")
    assert bucket_name, "state_bucket_name output not found in bootstrap"
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_bootstrap_github_actions_role_exists(iam_client, bootstrap_outputs):
    """Verify the GitHub Actions IAM role exists."""
    role_arn = bootstrap_outputs.get("github_actions_role_arn")
    assert role_arn, "github_actions_role_arn output not found in bootstrap"
    role_name = role_arn.split("/")[-1]
    response = iam_client.get_role(RoleName=role_name)
    assert response["Role"]["RoleName"] == role_name


def test_bootstrap_route53_zone_exists(route53_client, bootstrap_outputs):
    """Verify the Route53 hosted zone exists."""
    zone_id = bootstrap_outputs.get("route53_zone_id")
    assert zone_id, "route53_zone_id output not found in bootstrap"
    response = route53_client.get_hosted_zone(Id=zone_id)
    assert response["HostedZone"]["Id"].endswith(zone_id)
