import requests

from test_fixtures.http_endpoint import (
    error_response_hides,
    error_response_is_json,
    error_response_names_the_error,
)


class TestInputValidationJourney:
    def test_missing_device_id_returns_400(self, api_url: str) -> None:
        config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config},
            timeout=10
        )
        assert response.status_code == 400

    def test_missing_configuration_returns_400(self, api_url: str, test_device_id: str) -> None:
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"device_id": test_device_id},
            timeout=10
        )
        assert response.status_code == 400

    def test_invalid_configuration_returns_400(self, api_url: str, test_device_id: str) -> None:
        config = {"rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config, "device_id": test_device_id},
            timeout=10
        )
        assert response.status_code == 400

    def test_get_invalid_format_returns_400(self, api_url: str) -> None:
        response = requests.get(
            f"{api_url}/v1/rack-configurations/invalid",
            timeout=10
        )
        assert response.status_code == 400


class TestNotFoundHandlingJourney:
    def test_get_not_found_returns_404(self, api_url: str) -> None:
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        assert response.status_code == 404

    def test_404_response_is_json(self, api_url: str) -> None:
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        try:
            response.json()
        except ValueError:
            assert False, "404 response should be valid JSON"

    def test_404_response_does_not_contain_traceback(self, api_url: str) -> None:
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        text = response.text.lower()
        assert "traceback" not in text, "Error response should not contain traceback"

    def test_404_response_does_not_contain_line_numbers(self, api_url: str) -> None:
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        text = response.text.lower()
        assert "at line" not in text, "Error response should not contain line numbers"


class TestErrorResponseSecurityJourney:
    def test_error_response_is_json(self, api_url: str) -> None:
        assert error_response_is_json(
            f"{api_url}/v1/rack-configurations")

    def test_error_response_has_error_field(self, api_url: str) -> None:
        assert error_response_names_the_error(
            f"{api_url}/v1/rack-configurations")

    def test_error_response_does_not_reveal_var_paths(self, api_url: str) -> None:
        assert error_response_hides(
            f"{api_url}/v1/rack-configurations", "/var/")

    def test_error_response_does_not_reveal_tmp_paths(self, api_url: str) -> None:
        assert error_response_hides(
            f"{api_url}/v1/rack-configurations", "/tmp/")
