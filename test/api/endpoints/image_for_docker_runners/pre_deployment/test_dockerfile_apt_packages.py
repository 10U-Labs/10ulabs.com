def test_dockerfile_installs_ca_certificates_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('ca-certificates') != -1


def test_dockerfile_installs_curl_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('curl') != -1


def test_dockerfile_installs_git_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('git') != -1


def test_dockerfile_installs_gnupg_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('gnupg') != -1


def test_dockerfile_installs_jq_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('jq') != -1


def test_dockerfile_installs_libicu76_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('libicu76') != -1


def test_dockerfile_installs_libssl3t64_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('libssl3t64') != -1


def test_dockerfile_installs_liblttng_ust1_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('liblttng-ust1') != -1


def test_dockerfile_installs_procps_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('procps') != -1


def test_dockerfile_installs_python3_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('python3') != -1


def test_dockerfile_installs_python3_pip_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('python3-pip') != -1


def test_dockerfile_installs_python3_venv_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('python3-venv') != -1


def test_dockerfile_installs_sudo_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('sudo') != -1


def test_dockerfile_installs_tar_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('tar') != -1


def test_dockerfile_installs_unzip_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('unzip') != -1


def test_dockerfile_installs_wget_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('wget') != -1


def test_dockerfile_installs_xz_utils_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('xz-utils') != -1


def test_dockerfile_installs_zlib1g_via_apt_get(apt_get_install_packages):
    assert apt_get_install_packages.find('zlib1g') != -1
