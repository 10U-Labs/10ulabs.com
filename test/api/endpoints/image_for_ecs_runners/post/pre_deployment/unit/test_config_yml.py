"""Tests for config.yml file."""
from test.api.endpoints.image_for_ecs_runners.conftest import CONFIG_PATH

import yaml


def _read_config():
    """Read and parse the config.yml file."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_config_has_node_version():
    """Test that config has node_version field."""
    config = _read_config()
    assert config["node_version"] is not None


def test_config_node_version_is_string():
    """Test that config node_version is a string."""
    config = _read_config()
    assert isinstance(config["node_version"], str)


def test_config_has_runner_version():
    """Test that config has runner_version field."""
    config = _read_config()
    assert config["runner_version"] is not None


def test_config_runner_version_is_string():
    """Test that config runner_version is a string."""
    config = _read_config()
    assert isinstance(config["runner_version"], str)


def test_config_has_terraform_version():
    """Test that config has terraform_version field."""
    config = _read_config()
    assert config["terraform_version"] is not None


def test_config_terraform_version_is_string():
    """Test that config terraform_version is a string."""
    config = _read_config()
    assert isinstance(config["terraform_version"], str)


def test_config_has_yq_version():
    """Test that config has yq_version field."""
    config = _read_config()
    assert config["yq_version"] is not None


def test_config_yq_version_is_string():
    """Test that config yq_version is a string."""
    config = _read_config()
    assert isinstance(config["yq_version"], str)
