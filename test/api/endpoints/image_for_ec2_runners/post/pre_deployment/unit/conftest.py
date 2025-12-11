"""Pytest fixtures for pre-deployment unit tests."""
import importlib.util
from pathlib import Path
import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
POST_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners" / "post"


@pytest.fixture
def config_path():
    """Config path."""
    return POST_DIR / "config.yml"


@pytest.fixture
def loaded_config():
    """Loaded config."""
    return yaml.safe_load((POST_DIR / "config.yml").read_text())


@pytest.fixture
def post_dir():
    """Post dir."""
    return POST_DIR


@pytest.fixture
def setup_script_content():
    """Setup script content."""
    return (POST_DIR / "setup.py").read_text()


@pytest.fixture
def setup_script_path():
    """Setup script path."""
    return POST_DIR / "setup.py"


@pytest.fixture
def setup_module():
    """Load the setup module dynamically."""
    spec = importlib.util.spec_from_file_location("setup", POST_DIR / "setup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
