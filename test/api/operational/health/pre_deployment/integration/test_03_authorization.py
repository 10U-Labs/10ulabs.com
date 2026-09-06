from test_fixtures.integration import (
    create_api_gateway_authorization_tests,
    create_lambda_and_iam_authorization_tests,
)


TestAPIGatewayAuthorization = create_api_gateway_authorization_tests()
TestLambdaAndIAMAuthorization = create_lambda_and_iam_authorization_tests()
