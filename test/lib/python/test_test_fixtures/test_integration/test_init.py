from test_fixtures.integration import (
    Layer2EndpointAuthenticationTests,
    create_layer2_s3_authorization_tests,
    create_simple_layer1_authentication_tests,
    create_www_common_fixtures,
    create_www_common_s3_existence_tests,
    s3_head_bucket_problem,
    get_aws_account_id_via_cli,
)


def test_layer2_endpoint_authentication_tests_import() -> None:
    assert Layer2EndpointAuthenticationTests is not None


def test_create_layer2_s3_authorization_tests_import() -> None:
    assert callable(create_layer2_s3_authorization_tests)


def test_create_simple_layer1_authentication_tests_import() -> None:
    assert callable(create_simple_layer1_authentication_tests)


def test_create_www_common_fixtures_import() -> None:
    assert callable(create_www_common_fixtures)


def test_create_www_common_s3_existence_tests_import() -> None:
    assert callable(create_www_common_s3_existence_tests)


def test_s3_head_bucket_problem_import() -> None:
    assert callable(s3_head_bucket_problem)


def test_get_aws_account_id_via_cli_import() -> None:
    assert callable(get_aws_account_id_via_cli)
