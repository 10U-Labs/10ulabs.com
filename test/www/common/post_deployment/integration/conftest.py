"""Pytest fixtures for www_common post-deployment integration tests."""
import boto3
import pytest


def pytest_configure(config):
    """Register the layer marker."""
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N"
    )


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


@pytest.fixture(name="lambda_client_us_east_1", scope="module")
def lambda_client_us_east_1_fixture():
    """Create a Lambda client for us-east-1 (required for Lambda@Edge)."""
    return boto3.client("lambda", region_name="us-east-1")


@pytest.fixture(name="spa_routing_lambda", scope="module")
def spa_routing_lambda_fixture(lambda_client_us_east_1, config):
    """Get the SPA routing Lambda function configuration."""
    function_name = f"{config['resource_prefix']}SpaRouting"
    return lambda_client_us_east_1.get_function(FunctionName=function_name)


@pytest.fixture(name="spa_routing_lambda_config", scope="module")
def spa_routing_lambda_config_fixture(spa_routing_lambda):
    """Get the SPA routing Lambda function configuration details."""
    return spa_routing_lambda["Configuration"]
