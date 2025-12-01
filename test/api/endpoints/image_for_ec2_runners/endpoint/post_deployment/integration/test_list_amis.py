from ..conftest import make_authenticated_get


def test_list_amis_returns_200(amis_endpoint, api_key):
    response = make_authenticated_get(amis_endpoint, api_key)
    assert response.status_code == 200


def test_list_amis_returns_json(amis_endpoint, api_key):
    response = make_authenticated_get(amis_endpoint, api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_list_amis_has_success_field(amis_endpoint, api_key):
    response = make_authenticated_get(amis_endpoint, api_key)
    assert "success" in response.json()


def test_list_amis_has_amis_field(amis_endpoint, api_key):
    response = make_authenticated_get(amis_endpoint, api_key)
    assert "amis" in response.json()


def test_list_amis_has_count_field(amis_endpoint, api_key):
    response = make_authenticated_get(amis_endpoint, api_key)
    assert "count" in response.json()


def test_list_amis_amis_is_list(amis_endpoint, api_key):
    response = make_authenticated_get(amis_endpoint, api_key)
    assert isinstance(response.json()["amis"], list)


def test_list_amis_count_matches_amis_length(amis_endpoint, api_key):
    response = make_authenticated_get(amis_endpoint, api_key)
    data = response.json()
    assert data["count"] == len(data["amis"])
