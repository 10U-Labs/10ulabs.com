def test_dockerfile_installs_boto3_via_pip3(pip3_install_packages):
    assert 'boto3' in pip3_install_packages


def test_dockerfile_installs_boto3_stubs_via_pip3(pip3_install_packages):
    assert 'boto3-stubs' in pip3_install_packages


def test_dockerfile_installs_botocore_via_pip3(pip3_install_packages):
    assert 'botocore' in pip3_install_packages


def test_dockerfile_installs_dnspython_via_pip3(pip3_install_packages):
    assert 'dnspython' in pip3_install_packages


def test_dockerfile_installs_mypy_via_pip3(pip3_install_packages):
    assert 'mypy' in pip3_install_packages


def test_dockerfile_installs_pylint_via_pip3(pip3_install_packages):
    assert 'pylint' in pip3_install_packages


def test_dockerfile_installs_pytest_via_pip3(pip3_install_packages):
    assert 'pytest' in pip3_install_packages


def test_dockerfile_installs_pyyaml_via_pip3(pip3_install_packages):
    assert 'PyYAML' in pip3_install_packages


def test_dockerfile_installs_requests_via_pip3(pip3_install_packages):
    assert 'requests' in pip3_install_packages


def test_dockerfile_installs_types_pyyaml_via_pip3(pip3_install_packages):
    assert 'types-PyYAML' in pip3_install_packages


def test_dockerfile_installs_types_requests_via_pip3(pip3_install_packages):
    assert 'types-requests' in pip3_install_packages


def test_dockerfile_installs_yamllint_via_pip3(pip3_install_packages):
    assert 'yamllint' in pip3_install_packages
