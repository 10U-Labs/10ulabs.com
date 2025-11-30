def test_dockerfile_installs_nodejs(dockerfile_run_commands_joined):
    assert dockerfile_run_commands_joined.find('node-v') != -1


def test_dockerfile_declares_node_version_arg(dockerfile_content):
    assert dockerfile_content.find('ARG NODE_VERSION') != -1


def test_dockerfile_installs_jsonlint_via_npm(npm_install_packages):
    assert npm_install_packages.find('jsonlint') != -1


def test_dockerfile_installs_npm_packages_globally(npm_install_packages):
    assert npm_install_packages.find('-g') != -1
