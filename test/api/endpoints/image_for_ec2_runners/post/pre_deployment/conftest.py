from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
POST_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners" / "post"


@pytest.fixture
def post_dir():
    return POST_DIR


@pytest.fixture
def setup_script_path(post_dir):
    return post_dir / "setup.sh"


@pytest.fixture
def setup_script_content(setup_script_path):
    return setup_script_path.read_text()


@pytest.fixture
def config_path(post_dir):
    return post_dir / "config.yml"
