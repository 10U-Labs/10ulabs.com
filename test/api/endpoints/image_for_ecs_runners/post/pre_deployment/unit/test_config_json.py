"""Tests for config.json file."""
import json

from test.api.endpoints.image_for_ecs_runners.conftest import CONFIG_PATH


def _read_config():
    """Read and parse the config.json file."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


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


def test_config_has_gh_version():
    """Test that config has gh_version field."""
    config = _read_config()
    assert config["gh_version"] is not None


def test_config_gh_version_is_string():
    """Test that config gh_version is a string."""
    config = _read_config()
    assert isinstance(config["gh_version"], str)


def test_config_has_hadolint_version():
    """Test that config has hadolint_version field."""
    config = _read_config()
    assert config["hadolint_version"] is not None


def test_config_hadolint_version_is_string():
    """Test that config hadolint_version is a string."""
    config = _read_config()
    assert isinstance(config["hadolint_version"], str)


def test_config_has_tflint_version():
    """Test that config has tflint_version field."""
    config = _read_config()
    assert config["tflint_version"] is not None


def test_config_tflint_version_is_string():
    """Test that config tflint_version is a string."""
    config = _read_config()
    assert isinstance(config["tflint_version"], str)
