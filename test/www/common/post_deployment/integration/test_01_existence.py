def test_cloudfront_distribution_exists(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    distribution_list = distributions["DistributionList"]
    assert distribution_list["Quantity"] >= 0


def test_acm_certificate_exists(acm_client):
    certificates = acm_client.list_certificates()
    assert certificates["CertificateSummaryList"]


def test_s3_bucket_exists(s3_client, config):
    response = s3_client.head_bucket(Bucket=config["website_bucket_name"])
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_lambda_edge_function_exists(spa_routing_lambda):
    assert spa_routing_lambda is not None


def test_lambda_edge_iam_role_exists(spa_routing_lambda_config):
    role_arn = spa_routing_lambda_config.get("Role", "")
    assert role_arn.startswith("arn:aws:iam::")
