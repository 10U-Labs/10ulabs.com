"""Tests for Dockerfile pip package installations."""


def test_dockerfile_installs_boto3_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs boto3 via pip3."""
    assert pip3_install_packages.find('boto3') != -1


def test_dockerfile_installs_boto3_stubs_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs boto3-stubs via pip3."""
    assert pip3_install_packages.find('boto3-stubs') != -1


def test_dockerfile_installs_botocore_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs botocore via pip3."""
    assert pip3_install_packages.find('botocore') != -1


def test_dockerfile_installs_dockerfile_parse_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs dockerfile-parse via pip3."""
    assert pip3_install_packages.find('dockerfile-parse') != -1


def test_dockerfile_installs_dnspython_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs dnspython via pip3."""
    assert pip3_install_packages.find('dnspython') != -1


def test_dockerfile_installs_mypy_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs mypy via pip3."""
    assert pip3_install_packages.find('mypy') != -1


def test_dockerfile_installs_paramiko_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs paramiko via pip3."""
    assert pip3_install_packages.find('paramiko') != -1


def test_dockerfile_installs_pylint_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs pylint via pip3."""
    assert pip3_install_packages.find('pylint') != -1


def test_dockerfile_installs_pytest_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs pytest via pip3."""
    assert pip3_install_packages.find('pytest') != -1


def test_dockerfile_installs_python_hcl2_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs python-hcl2 via pip3."""
    assert pip3_install_packages.find('python-hcl2') != -1


def test_dockerfile_installs_pyyaml_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs PyYAML via pip3."""
    assert pip3_install_packages.find('PyYAML') != -1


def test_dockerfile_installs_requests_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs requests via pip3."""
    assert pip3_install_packages.find('requests') != -1


def test_dockerfile_installs_types_dockerfile_parse_via_pip3(
    pip3_install_packages
):
    """Test that Dockerfile installs types-dockerfile-parse via pip3."""
    assert pip3_install_packages.find('types-dockerfile-parse') != -1


def test_dockerfile_installs_types_paramiko_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs types-paramiko via pip3."""
    assert pip3_install_packages.find('types-paramiko') != -1


def test_dockerfile_installs_types_pyyaml_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs types-PyYAML via pip3."""
    assert pip3_install_packages.find('types-PyYAML') != -1


def test_dockerfile_installs_types_requests_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs types-requests via pip3."""
    assert pip3_install_packages.find('types-requests') != -1


def test_dockerfile_installs_yamllint_via_pip3(pip3_install_packages):
    """Test that Dockerfile installs yamllint via pip3."""
    assert pip3_install_packages.find('yamllint') != -1
