import pytest

from naming_conventions import validate_name


def create_iam_role_tests(roles: list):
    class TestIAMRoleNamingConventions:
        @staticmethod
        def get_role_count():
            return len(roles)

        @pytest.mark.parametrize(
            "resource_name,role_name",
            roles,
            ids=[f"iam_role_{r[0]}" for r in roles],
        )
        def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
            error = validate_name(role_name)
            assert error is None, (
                f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
            )

    return TestIAMRoleNamingConventions


def create_lambda_function_tests(functions: list):
    class TestLambdaFunctionNamingConventions:
        @staticmethod
        def get_function_count():
            return len(functions)

        @pytest.mark.parametrize(
            "resource_name,function_name",
            functions,
            ids=[f"lambda_{f[0]}" for f in functions],
        )
        def test_lambda_function_name_is_pascalcase(self, resource_name, function_name):
            error = validate_name(function_name)
            assert error is None, (
                f"Lambda function '{resource_name}' has invalid name "
                f"'{function_name}': {error}"
            )

    return TestLambdaFunctionNamingConventions


def create_sqs_queue_tests(queues: list):
    class TestSQSQueueNamingConventions:
        @staticmethod
        def get_queue_count():
            return len(queues)

        @pytest.mark.parametrize(
            "resource_name,queue_name",
            queues,
            ids=[f"sqs_{q[0]}" for q in queues],
        )
        def test_sqs_queue_name_is_pascalcase(self, resource_name, queue_name):
            name_to_check = queue_name
            if name_to_check.endswith('.fifo'):
                name_to_check = name_to_check[:-5]
            error = validate_name(name_to_check)
            assert error is None, (
                f"SQS queue '{resource_name}' has invalid name "
                f"'{queue_name}': {error}"
            )

    return TestSQSQueueNamingConventions
