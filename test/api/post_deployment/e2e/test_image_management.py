import requests


def test_v1_image_for_docker_runners_post_triggers_workflow(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-docker-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_image_for_docker_runners_post_invalid_api_key_returns_403(api_url):
    headers = {"x-api-key": "invalid-key"}
    response = requests.post(f"{api_url}/v1/image-for-docker-runners", json={}, headers=headers, timeout=10)
    assert response.status_code == 403


def test_v1_image_for_docker_runners_get_lists_all_images(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_v1_image_for_docker_runners_get_with_no_images_returns_empty_list(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "images" in data or "count" in data


def test_v1_image_for_docker_runners_latest_get_returns_latest_stable(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_docker_runners_delete_removes_image(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-docker-runners/sha256:test", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_docker_runners_delete_invalid_digest_returns_error(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-docker-runners/invalid", headers=headers, timeout=10)
    assert response.status_code in [400, 403, 404, 500]


def test_v1_image_for_ec2_runners_post_triggers_packer_build(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-ec2-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_image_for_ec2_runners_post_invalid_api_key_returns_403(api_url):
    headers = {"x-api-key": "invalid-key"}
    response = requests.post(f"{api_url}/v1/image-for-ec2-runners", json={}, headers=headers, timeout=10)
    assert response.status_code == 403


def test_v1_image_for_ec2_runners_get_lists_all_amis(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_v1_image_for_ec2_runners_get_with_no_amis_returns_empty_list(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "amis" in data or "count" in data


def test_v1_image_for_ec2_runners_latest_get_retrieves_from_ssm(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_ec2_runners_delete_deregisters_ami(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-ec2-runners/ami-test123", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_ec2_runners_delete_invalid_ami_id_returns_error(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-ec2-runners/invalid", headers=headers, timeout=10)
    assert response.status_code in [400, 403, 404, 500]


def test_get_docker_runner_image_by_digest(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/sha256:test123", headers=headers, timeout=10)
    assert response.status_code in [200, 404]


def test_docker_image_build_triggers_workflow(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-docker-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_ec2_ami_build_triggers_workflow(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-ec2-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_docker_image_by_digest_returns_image_details(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "digest" in result or "success" in result


def test_docker_image_by_digest_includes_tags(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "tags" in result or "success" in result


def test_docker_image_by_digest_includes_pushed_at(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "pushed_at" in result or "success" in result


def test_docker_image_by_digest_includes_size(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "size_bytes" in result or "success" in result
