class TestLambdaConfiguration:
    def test_contact_handler_uses_python_runtime(
        self, lambda_client, shared_config
    ):
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        runtime = response["Configuration"]["Runtime"]
        assert runtime == "python3.13", (
            f"Lambda runtime should be python3.13, got: {runtime}"
        )

    def test_contact_handler_uses_arm64_architecture(
        self, lambda_client, shared_config
    ):
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        architectures = response["Configuration"].get("Architectures", [])
        assert "arm64" in architectures, (
            f"Lambda should use arm64 architecture, got: {architectures}"
        )

    def test_contact_handler_has_handler_configured(
        self, lambda_client, shared_config
    ):
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        handler = response["Configuration"]["Handler"]
        assert handler == "handler.lambda_handler", (
            f"Lambda handler should be handler.lambda_handler, got: {handler}"
        )

    def test_contact_handler_has_10_second_timeout(
        self, lambda_client, shared_config
    ):
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        timeout = response["Configuration"]["Timeout"]
        assert timeout == 10, (
            f"Lambda timeout should be 10 seconds, got: {timeout}"
        )

    def test_contact_handler_has_contact_email_env_var(
        self, contact_handler_env_vars
    ):
        assert "CONTACT_EMAIL" in contact_handler_env_vars, (
            "Lambda missing CONTACT_EMAIL environment variable"
        )

    def test_contact_handler_has_recaptcha_param_env_var(
        self, contact_handler_env_vars
    ):
        assert "RECAPTCHA_SECRET_PARAMETER_NAME" in contact_handler_env_vars, (
            "Lambda missing RECAPTCHA_SECRET_PARAMETER_NAME environment variable"
        )


class TestCloudWatchLogsConfiguration:
    def test_contact_handler_log_group_has_retention_set(
        self, contact_handler_log_group
    ):
        assert contact_handler_log_group["retention"] is not None, (
            f"Log group '{contact_handler_log_group['name']}' "
            "should have retention set"
        )

    def test_contact_handler_log_group_retention_is_7_days(
        self, contact_handler_log_group
    ):
        retention = contact_handler_log_group["retention"]
        assert retention == 7, (
            f"Log group retention should be 7 days, got: {retention}"
        )

