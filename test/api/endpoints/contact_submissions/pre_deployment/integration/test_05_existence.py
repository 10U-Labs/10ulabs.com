from test_fixtures.integration import assert_api_gateway_exists


class TestPrerequisiteExistence:
    def test_api_gateway_rest_api_exists(self, api_gateway_info):
        assert_api_gateway_exists(api_gateway_info)
        assert True

    def test_ses_sending_is_enabled(self, ses_client):
        response = ses_client.get_account_sending_enabled()
        assert response.get("Enabled", False), (
            "SES sending is not enabled in this region. "
            "Enable SES sending or request production access from AWS."
        )
