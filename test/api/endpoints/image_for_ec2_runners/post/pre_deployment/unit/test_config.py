"""Unit tests for runner configuration validation."""


class TestConfigRunnerVersion:
    def test_config_has_runner_version_field(self, loaded_config):
        has_field = "runner_version" in loaded_config
        assert has_field

    def test_config_runner_version_is_string(self, loaded_config):
        is_string = isinstance(loaded_config["runner_version"], str)
        assert is_string


class TestConfigYqVersion:
    def test_config_has_yq_version_field(self, loaded_config):
        has_field = "yq_version" in loaded_config
        assert has_field

    def test_config_yq_version_is_string(self, loaded_config):
        is_string = isinstance(loaded_config["yq_version"], str)
        assert is_string


class TestConfigRunnerUser:
    def test_config_has_runner_user_field(self, loaded_config):
        has_field = "runner_user" in loaded_config
        assert has_field

    def test_config_runner_user_is_string(self, loaded_config):
        is_string = isinstance(loaded_config["runner_user"], str)
        assert is_string


class TestConfigSourceAmi:
    def test_config_has_source_ami_field(self, loaded_config):
        has_field = "source_ami" in loaded_config
        assert has_field

    def test_config_source_ami_is_debian(self, loaded_config):
        source_ami = loaded_config["source_ami"]
        is_debian = source_ami.startswith("debian-")
        assert is_debian


class TestConfigTags:
    def test_config_has_purpose_tag(self, loaded_config):
        has_tag = "Purpose" in loaded_config["tags"]
        assert has_tag

    def test_config_has_tags_field(self, loaded_config):
        has_field = "tags" in loaded_config
        assert has_field

    def test_setup_script_exists(self, post_dir):
        script_path = post_dir / "setup.sh"
        assert script_path.exists()
