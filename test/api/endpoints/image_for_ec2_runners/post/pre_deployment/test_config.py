import yaml
import pytest


@pytest.fixture
def config(config_path):
    return yaml.safe_load(config_path.read_text())


class TestConfigRunnerVersion:
    def test_config_has_runner_version_field(self, config):
        has_field = "runner_version" in config
        assert has_field

    def test_config_runner_version_is_string(self, config):
        is_string = isinstance(config["runner_version"], str)
        assert is_string


class TestConfigYqVersion:
    def test_config_has_yq_version_field(self, config):
        has_field = "yq_version" in config
        assert has_field

    def test_config_yq_version_is_string(self, config):
        is_string = isinstance(config["yq_version"], str)
        assert is_string


class TestConfigRunnerUser:
    def test_config_has_runner_user_field(self, config):
        has_field = "runner_user" in config
        assert has_field

    def test_config_runner_user_is_string(self, config):
        is_string = isinstance(config["runner_user"], str)
        assert is_string


class TestConfigSourceAmi:
    def test_config_has_source_ami_field(self, config):
        has_field = "source_ami" in config
        assert has_field

    def test_config_source_ami_is_debian(self, config):
        source_ami = config["source_ami"]
        is_debian = source_ami.startswith("debian-")
        assert is_debian


class TestConfigTags:
    def test_config_has_tags_field(self, config):
        has_field = "tags" in config
        assert has_field

    def test_config_has_purpose_tag(self, config):
        has_tag = "Purpose" in config["tags"]
        assert has_tag


class TestConfigSetupScript:
    def test_setup_script_exists(self, post_dir):
        script_path = post_dir / "setup.sh"
        assert script_path.exists()
