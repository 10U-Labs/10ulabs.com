"""Pytest fixtures for www_common post-deployment integration tests."""
import pytest

pytest_plugins = ['pytest_layers']


@pytest.fixture(name="distribution_config", scope="module")
def distribution_config_fixture(cloudfront_client, config):
    """Get CloudFront distribution config for website domain."""
    distributions = cloudfront_client.list_distributions()
    if distributions["DistributionList"]["Quantity"] > 0:
        for item in distributions["DistributionList"]["Items"]:
            aliases = item.get("Aliases", {}).get("Items", [])
            if config["website_fqdn"] in aliases:
                dist_id = item["Id"]
                return cloudfront_client.get_distribution_config(Id=dist_id)
    assert False, f"CloudFront distribution for {config['website_fqdn']} not found"


@pytest.fixture(name="logging_config", scope="module")
def logging_config_fixture(distribution_config):
    """Get CloudFront logging config from distribution."""
    return distribution_config["DistributionConfig"].get("Logging", {})


@pytest.fixture(name="default_cache_behavior", scope="module")
def default_cache_behavior_fixture(distribution_config):
    """Get CloudFront default cache behavior from distribution."""
    return distribution_config["DistributionConfig"]["DefaultCacheBehavior"]


@pytest.fixture(name="public_access_block", scope="module")
def public_access_block_fixture(s3_client, config):
    """Get S3 bucket public access block configuration."""
    response = s3_client.get_public_access_block(Bucket=config["website_bucket_name"])
    return response["PublicAccessBlockConfiguration"]
