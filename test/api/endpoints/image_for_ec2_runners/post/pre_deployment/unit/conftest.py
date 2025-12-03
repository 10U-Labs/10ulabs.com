from pathlib import Path
import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
POST_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners" / "post"


@pytest.fixture
def config_path():
    return POST_DIR / "config.yml"


@pytest.fixture
def loaded_config():
    return yaml.safe_load((POST_DIR / "config.yml").read_text())


@pytest.fixture
def post_dir():
    return POST_DIR


@pytest.fixture
def setup_script_content():
    return (POST_DIR / "setup.sh").read_text()


@pytest.fixture
def setup_script_path():
    return POST_DIR / "setup.sh"
