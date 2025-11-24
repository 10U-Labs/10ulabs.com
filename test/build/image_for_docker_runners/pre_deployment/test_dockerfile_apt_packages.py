def test_dockerfile_installs_ca_certificates_via_apt_get(apt_get_install_packages):
    assert 'ca-certificates' in apt_get_install_packages


def test_dockerfile_installs_curl_via_apt_get(apt_get_install_packages):
    assert 'curl' in apt_get_install_packages


def test_dockerfile_installs_git_via_apt_get(apt_get_install_packages):
    assert 'git' in apt_get_install_packages


def test_dockerfile_installs_gnupg_via_apt_get(apt_get_install_packages):
    assert 'gnupg' in apt_get_install_packages


def test_dockerfile_installs_jq_via_apt_get(apt_get_install_packages):
    assert 'jq' in apt_get_install_packages


def test_dockerfile_installs_libicu76_via_apt_get(apt_get_install_packages):
    assert 'libicu76' in apt_get_install_packages


def test_dockerfile_installs_libssl3t64_via_apt_get(apt_get_install_packages):
    assert 'libssl3t64' in apt_get_install_packages


def test_dockerfile_installs_liblttng_ust1_via_apt_get(apt_get_install_packages):
    assert 'liblttng-ust1' in apt_get_install_packages


def test_dockerfile_installs_procps_via_apt_get(apt_get_install_packages):
    assert 'procps' in apt_get_install_packages


def test_dockerfile_installs_python3_via_apt_get(apt_get_install_packages):
    assert 'python3' in apt_get_install_packages


def test_dockerfile_installs_python3_pip_via_apt_get(apt_get_install_packages):
    assert 'python3-pip' in apt_get_install_packages


def test_dockerfile_installs_python3_venv_via_apt_get(apt_get_install_packages):
    assert 'python3-venv' in apt_get_install_packages


def test_dockerfile_installs_sudo_via_apt_get(apt_get_install_packages):
    assert 'sudo' in apt_get_install_packages


def test_dockerfile_installs_tar_via_apt_get(apt_get_install_packages):
    assert 'tar' in apt_get_install_packages


def test_dockerfile_installs_unzip_via_apt_get(apt_get_install_packages):
    assert 'unzip' in apt_get_install_packages


def test_dockerfile_installs_wget_via_apt_get(apt_get_install_packages):
    assert 'wget' in apt_get_install_packages


def test_dockerfile_installs_xz_utils_via_apt_get(apt_get_install_packages):
    assert 'xz-utils' in apt_get_install_packages


def test_dockerfile_installs_zlib1g_via_apt_get(apt_get_install_packages):
    assert 'zlib1g' in apt_get_install_packages
