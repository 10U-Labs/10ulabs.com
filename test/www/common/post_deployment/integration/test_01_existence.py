from typing import Any, Dict
def test_cloudfront_distribution_exists(cloudfront_client: Any) -> None:
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions["DistributionList"]
    assert distribution_list["Quantity"] >= 0


def test_acm_certificate_exists(acm_client: Any) -> None:
    certificates = acm_client.list_certificates()
    assert certificates["CertificateSummaryList"]


def test_s3_bucket_exists(s3_client: Any, config: Dict[str, Any]) -> None:
    response = s3_client.head_bucket(Bucket=config["website_bucket_name"])
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_spa_routing_function_exists(spa_routing_function: Any) -> None:
    assert spa_routing_function["Name"].endswith("SpaRouting")
