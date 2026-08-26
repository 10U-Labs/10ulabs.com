import pytest

from naming_conventions.test_helpers import (
    create_iam_role_tests,
    create_lambda_function_tests,
    create_sqs_queue_tests,
)


class TestCreateIamRoleTests:
    def test_returns_class(self):
        roles = [("my_role", "TenULabsMyRole")]
        TestClass = create_iam_role_tests(roles)
        assert isinstance(TestClass, type)

    def test_returned_class_has_get_role_count(self):
        roles = [("my_role", "TenULabsMyRole")]
        TestClass = create_iam_role_tests(roles)
        assert hasattr(TestClass, "get_role_count")

    def test_get_role_count_returns_correct_count(self):
        roles = [("role_one", "RoleOne"), ("role_two", "RoleTwo")]
        TestClass = create_iam_role_tests(roles)
        assert TestClass.get_role_count() == 2

    def test_get_role_count_returns_zero_for_empty_list(self):
        TestClass = create_iam_role_tests([])
        assert TestClass.get_role_count() == 0

    def test_returned_class_has_test_method(self):
        roles = [("my_role", "TenULabsMyRole")]
        TestClass = create_iam_role_tests(roles)
        assert hasattr(TestClass, "test_iam_role_name_is_pascalcase")

    def test_test_method_passes_for_valid_pascalcase(self):
        roles = [("my_role", "TenULabsMyRole")]
        TestClass = create_iam_role_tests(roles)
        instance = TestClass()
        result = instance.test_iam_role_name_is_pascalcase("my_role", "TenULabsMyRole")
        assert result is None

    def test_test_method_fails_for_invalid_name_with_dash(self):
        roles = [("bad_role", "TenU-Labs-BadRole")]
        TestClass = create_iam_role_tests(roles)
        instance = TestClass()
        with pytest.raises(AssertionError, match="invalid name"):
            instance.test_iam_role_name_is_pascalcase("bad_role", "TenU-Labs-BadRole")


class TestCreateLambdaFunctionTests:
    def test_returns_class(self):
        functions = [("my_func", "TenULabsMyFunction")]
        TestClass = create_lambda_function_tests(functions)
        assert isinstance(TestClass, type)

    def test_returned_class_has_get_function_count(self):
        functions = [("my_func", "TenULabsMyFunction")]
        TestClass = create_lambda_function_tests(functions)
        assert hasattr(TestClass, "get_function_count")

    def test_get_function_count_returns_correct_count(self):
        functions = [("func_one", "FuncOne"), ("func_two", "FuncTwo")]
        TestClass = create_lambda_function_tests(functions)
        assert TestClass.get_function_count() == 2

    def test_get_function_count_returns_zero_for_empty_list(self):
        TestClass = create_lambda_function_tests([])
        assert TestClass.get_function_count() == 0

    def test_returned_class_has_test_method(self):
        functions = [("my_func", "TenULabsMyFunction")]
        TestClass = create_lambda_function_tests(functions)
        assert hasattr(TestClass, "test_lambda_function_name_is_pascalcase")

    def test_test_method_passes_for_valid_pascalcase(self):
        functions = [("my_func", "TenULabsMyFunction")]
        TestClass = create_lambda_function_tests(functions)
        instance = TestClass()
        result = instance.test_lambda_function_name_is_pascalcase(
            "my_func", "TenULabsMyFunction"
        )
        assert result is None

    def test_test_method_fails_for_invalid_name(self):
        functions = [("bad_func", "TenU-Labs-BadFunc")]
        TestClass = create_lambda_function_tests(functions)
        instance = TestClass()
        with pytest.raises(AssertionError, match="invalid name"):
            instance.test_lambda_function_name_is_pascalcase(
                "bad_func", "TenU-Labs-BadFunc"
            )


class TestCreateSqsQueueTests:
    def test_returns_class(self):
        queues = [("my_queue", "TenULabsMyQueue")]
        TestClass = create_sqs_queue_tests(queues)
        assert isinstance(TestClass, type)

    def test_returned_class_has_get_queue_count(self):
        queues = [("my_queue", "TenULabsMyQueue")]
        TestClass = create_sqs_queue_tests(queues)
        assert hasattr(TestClass, "get_queue_count")

    def test_get_queue_count_returns_correct_count(self):
        queues = [("queue_one", "QueueOne"), ("queue_two", "QueueTwo")]
        TestClass = create_sqs_queue_tests(queues)
        assert TestClass.get_queue_count() == 2

    def test_get_queue_count_returns_zero_for_empty_list(self):
        TestClass = create_sqs_queue_tests([])
        assert TestClass.get_queue_count() == 0

    def test_returned_class_has_test_method(self):
        queues = [("my_queue", "TenULabsMyQueue")]
        TestClass = create_sqs_queue_tests(queues)
        assert hasattr(TestClass, "test_sqs_queue_name_is_pascalcase")

    def test_test_method_passes_for_valid_pascalcase(self):
        queues = [("my_queue", "TenULabsMyQueue")]
        TestClass = create_sqs_queue_tests(queues)
        instance = TestClass()
        result = instance.test_sqs_queue_name_is_pascalcase("my_queue", "TenULabsMyQueue")
        assert result is None

    def test_test_method_passes_for_fifo_queue(self):
        queues = [("my_queue", "TenULabsMyQueue.fifo")]
        TestClass = create_sqs_queue_tests(queues)
        instance = TestClass()
        result = instance.test_sqs_queue_name_is_pascalcase(
            "my_queue", "TenULabsMyQueue.fifo"
        )
        assert result is None

    def test_test_method_fails_for_invalid_name(self):
        queues = [("bad_queue", "TenU-Labs-BadQueue")]
        TestClass = create_sqs_queue_tests(queues)
        instance = TestClass()
        with pytest.raises(AssertionError, match="invalid name"):
            instance.test_sqs_queue_name_is_pascalcase("bad_queue", "TenU-Labs-BadQueue")

    def test_test_method_fails_for_invalid_fifo_queue(self):
        queues = [("bad_fifo", "Bad-Queue.fifo")]
        TestClass = create_sqs_queue_tests(queues)
        instance = TestClass()
        with pytest.raises(AssertionError, match="invalid name"):
            instance.test_sqs_queue_name_is_pascalcase("bad_fifo", "Bad-Queue.fifo")
