import yaml

from test.image_for_docker_runners.conftest import CONFIG_PATH


def _read_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_config_has_node_version():
    config = _read_config()
    assert config["node_version"] is not None


def test_config_node_version_is_string():
    config = _read_config()
    assert isinstance(config["node_version"], str)


def test_config_has_runner_version():
    config = _read_config()
    assert config["runner_version"] is not None


def test_config_runner_version_is_string():
    config = _read_config()
    assert isinstance(config["runner_version"], str)


def test_config_has_terraform_version():
    config = _read_config()
    assert config["terraform_version"] is not None


def test_config_terraform_version_is_string():
    config = _read_config()
    assert isinstance(config["terraform_version"], str)


def test_config_has_yq_version():
    config = _read_config()
    assert config["yq_version"] is not None


def test_config_yq_version_is_string():
    config = _read_config()
    assert isinstance(config["yq_version"], str)
