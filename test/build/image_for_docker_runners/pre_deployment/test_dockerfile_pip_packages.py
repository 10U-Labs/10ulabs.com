def test_dockerfile_installs_boto3_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('boto3') != -1


def test_dockerfile_installs_boto3_stubs_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('boto3-stubs') != -1


def test_dockerfile_installs_botocore_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('botocore') != -1


def test_dockerfile_installs_dnspython_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('dnspython') != -1


def test_dockerfile_installs_mypy_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('mypy') != -1


def test_dockerfile_installs_pylint_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('pylint') != -1


def test_dockerfile_installs_pytest_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('pytest') != -1


def test_dockerfile_installs_pyyaml_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('PyYAML') != -1


def test_dockerfile_installs_requests_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('requests') != -1


def test_dockerfile_installs_types_pyyaml_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('types-PyYAML') != -1


def test_dockerfile_installs_types_requests_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('types-requests') != -1


def test_dockerfile_installs_yamllint_via_pip3(pip3_install_packages):
    assert pip3_install_packages.find('yamllint') != -1
