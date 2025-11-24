def test_dockerfile_installs_nodejs(dockerfile_run_commands_joined):
    assert 'node-v' in dockerfile_run_commands_joined


def test_dockerfile_sets_node_version_to_20_18_1(dockerfile_node_version):
    assert dockerfile_node_version == '20.18.1'


def test_dockerfile_installs_jsonlint_via_npm(npm_install_packages):
    assert 'jsonlint' in npm_install_packages


def test_dockerfile_installs_npm_packages_globally(npm_install_packages):
    assert '-g' in npm_install_packages
