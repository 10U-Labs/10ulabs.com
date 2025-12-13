"""Pre-deployment tests for agents/shared Lambda layer Terraform configuration."""
import re


def test_lambda_layer_tf_defines_github_auth_layer(agents_shared_dir):
    """Test that lambda_layer.tf defines the GitHub auth layer."""
    lambda_layer_tf = agents_shared_dir / "lambda_layer.tf"
    content = lambda_layer_tf.read_text()
    pattern = r'resource\s+"aws_lambda_layer_version"\s+"github_auth"'
    assert re.search(pattern, content) is not None


def test_lambda_layer_supports_python313(agents_shared_dir):
    """Test that Lambda layer supports Python 3.13 runtime."""
    lambda_layer_tf = agents_shared_dir / "lambda_layer.tf"
    content = lambda_layer_tf.read_text()
    assert "python3.13" in content


def test_lambda_layer_supports_python312(agents_shared_dir):
    """Test that Lambda layer supports Python 3.12 runtime."""
    lambda_layer_tf = agents_shared_dir / "lambda_layer.tf"
    content = lambda_layer_tf.read_text()
    assert "python3.12" in content


def test_lambda_layer_build_script_exists(agents_shared_dir):
    """Test that Lambda layer build script exists."""
    layer_dir = agents_shared_dir / "lambda_layer"
    assert (layer_dir / "build.py").exists()


def test_lambda_layer_requirements_exists(agents_shared_dir):
    """Test that Lambda layer requirements.txt exists."""
    layer_dir = agents_shared_dir / "lambda_layer"
    assert (layer_dir / "requirements.txt").exists()


def test_lambda_layer_github_auth_module_exists(agents_shared_dir):
    """Test that Lambda layer github_auth.py module exists."""
    layer_dir = agents_shared_dir / "lambda_layer"
    assert (layer_dir / "github_auth.py").exists()


def test_lambda_layer_requirements_has_pyjwt(agents_shared_dir):
    """Test that requirements.txt includes PyJWT."""
    requirements = agents_shared_dir / "lambda_layer" / "requirements.txt"
    content = requirements.read_text()
    assert "PyJWT" in content


def test_lambda_layer_requirements_has_cryptography(agents_shared_dir):
    """Test that requirements.txt includes cryptography."""
    requirements = agents_shared_dir / "lambda_layer" / "requirements.txt"
    content = requirements.read_text()
    assert "cryptography" in content
