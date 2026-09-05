from typing import Any, Dict

import boto3
import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N"
    )


@pytest.fixture(name="distribution_config", scope="module")
def distribution_config_fixture(cloudfront_client: Any, config: Dict[str, Any]) -> Any:
    distributions = cloudfront_client.list_distributions()
    if distributions["DistributionList"]["Quantity"] > 0:
        for item in distributions["DistributionList"]["Items"]:
            aliases = item.get("Aliases", {}).get("Items", [])
            if config["website_fqdn"] in aliases:
                dist_id = item["Id"]
                return cloudfront_client.get_distribution_config(Id=dist_id)
    assert False, f"CloudFront distribution for {config['website_fqdn']} not found"


@pytest.fixture(scope="module")
def logging_config(distribution_config: Any) -> Any:
    return distribution_config["DistributionConfig"].get("Logging", {})


@pytest.fixture(name="default_cache_behavior", scope="module")
def default_cache_behavior_fixture(distribution_config: Any) -> Any:
    return distribution_config["DistributionConfig"]["DefaultCacheBehavior"]


@pytest.fixture(scope="module")
def viewer_certificate(distribution_config: Any) -> Any:
    return distribution_config["DistributionConfig"]["ViewerCertificate"]


@pytest.fixture(scope="module")
def custom_error_responses(distribution_config: Any) -> Any:
    return distribution_config["DistributionConfig"]["CustomErrorResponses"]


@pytest.fixture(scope="module")
def cache_policy_config(cloudfront_client: Any, default_cache_behavior: Any) -> Any:
    policy = cloudfront_client.get_cache_policy(
        Id=default_cache_behavior["CachePolicyId"]
    )
    return policy["CachePolicy"]["CachePolicyConfig"]


@pytest.fixture(scope="module")
def origin_request_policy_config(
    cloudfront_client: Any,
    default_cache_behavior: Any
) -> Any:
    policy = cloudfront_client.get_origin_request_policy(
        Id=default_cache_behavior["OriginRequestPolicyId"]
    )
    return policy["OriginRequestPolicy"]["OriginRequestPolicyConfig"]


@pytest.fixture(scope="module")
def public_access_block(s3_client: Any, config: Dict[str, Any]) -> Any:
    response = s3_client.get_public_access_block(Bucket=config["website_bucket_name"])
    return response["PublicAccessBlockConfiguration"]


@pytest.fixture(name="lambda_client_us_east_1", scope="module")
def lambda_client_us_east_1_fixture() -> Any:
    return boto3.client("lambda", region_name="us-east-1")


@pytest.fixture(name="spa_routing_lambda", scope="module")
def spa_routing_lambda_fixture(lambda_client_us_east_1: Any, config: Dict[str, Any]) -> Any:
    function_name = f"{config['resource_prefix']}SpaRouting"
    return lambda_client_us_east_1.get_function(FunctionName=function_name)


@pytest.fixture(scope="module")
def spa_routing_lambda_config(spa_routing_lambda: Any) -> Any:
    return spa_routing_lambda["Configuration"]
