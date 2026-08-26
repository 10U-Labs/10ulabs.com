from test_fixtures.integration import create_layer6_capability_tests


TestDeploymentCapabilities = create_layer6_capability_tests(
    frozenset({'lambda', 'iam', 'ssm'})
)
