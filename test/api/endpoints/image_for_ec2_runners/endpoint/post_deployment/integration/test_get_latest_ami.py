import pytest

from ..conftest import make_authenticated_get


@pytest.fixture(name="latest_response", scope="module")
def latest_response_fixture(latest_ami_endpoint, api_key):
    return make_authenticated_get(latest_ami_endpoint, api_key)


@pytest.fixture(name="has_available_ami", scope="module")
def has_available_ami_fixture(latest_response):
    return latest_response.json().get("success", False)


def test_get_latest_ami_returns_200_or_500(latest_response):
    assert latest_response.status_code in [200, 500]


def test_get_latest_ami_returns_json(latest_response):
    assert latest_response.headers["Content-Type"] == "application/json"


def test_get_latest_ami_has_success_field(latest_response):
    assert "success" in latest_response.json()


def test_get_latest_ami_has_ami_id_when_available(latest_response, has_available_ami):
    if not has_available_ami:
        pytest.skip("No AMI available")
    assert "ami_id" in latest_response.json()


def test_get_latest_ami_has_name_when_available(latest_response, has_available_ami):
    if not has_available_ami:
        pytest.skip("No AMI available")
    assert "name" in latest_response.json()


def test_get_latest_ami_has_state_when_available(latest_response, has_available_ami):
    if not has_available_ami:
        pytest.skip("No AMI available")
    assert "state" in latest_response.json()


def test_get_latest_ami_has_creation_date_when_available(latest_response, has_available_ami):
    if not has_available_ami:
        pytest.skip("No AMI available")
    assert "creation_date" in latest_response.json()


def test_get_latest_ami_has_error_when_unavailable(latest_response, has_available_ami):
    if has_available_ami:
        pytest.skip("AMI is available")
    assert "error" in latest_response.json()
