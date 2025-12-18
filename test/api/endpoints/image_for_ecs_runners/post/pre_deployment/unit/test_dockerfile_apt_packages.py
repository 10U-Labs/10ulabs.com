"""Tests for Dockerfile apt package installations."""


def test_dockerfile_installs_ca_certificates_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs ca-certificates via apt-get."""
    assert apt_get_install_packages.find('ca-certificates') != -1


def test_dockerfile_installs_curl_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs curl via apt-get."""
    assert apt_get_install_packages.find('curl') != -1


def test_dockerfile_installs_fontconfig_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs fontconfig via apt-get."""
    assert apt_get_install_packages.find('fontconfig') != -1


def test_dockerfile_installs_git_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs git via apt-get."""
    assert apt_get_install_packages.find('git') != -1


def test_dockerfile_installs_jq_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs jq via apt-get."""
    assert apt_get_install_packages.find('jq') != -1


def test_dockerfile_installs_libasound2t64_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libasound2t64 via apt-get."""
    assert apt_get_install_packages.find('libasound2t64') != -1


def test_dockerfile_installs_libatk_bridge2_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libatk-bridge2.0-0t64 via apt-get."""
    assert apt_get_install_packages.find('libatk-bridge2.0-0t64') != -1


def test_dockerfile_installs_libatk1_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libatk1.0-0t64 via apt-get."""
    assert apt_get_install_packages.find('libatk1.0-0t64') != -1


def test_dockerfile_installs_libatspi2_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libatspi2.0-0t64 via apt-get."""
    assert apt_get_install_packages.find('libatspi2.0-0t64') != -1


def test_dockerfile_installs_libavahi_client3_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libavahi-client3 via apt-get."""
    assert apt_get_install_packages.find('libavahi-client3') != -1


def test_dockerfile_installs_libavahi_common3_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libavahi-common3 via apt-get."""
    assert apt_get_install_packages.find('libavahi-common3') != -1


def test_dockerfile_installs_libcairo2_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libcairo2 via apt-get."""
    assert apt_get_install_packages.find('libcairo2') != -1


def test_dockerfile_installs_libcups2t64_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libcups2t64 via apt-get."""
    assert apt_get_install_packages.find('libcups2t64') != -1


def test_dockerfile_installs_libdrm_amdgpu1_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libdrm-amdgpu1 via apt-get."""
    assert apt_get_install_packages.find('libdrm-amdgpu1') != -1


def test_dockerfile_installs_libdrm2_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libdrm2 via apt-get."""
    assert apt_get_install_packages.find('libdrm2') != -1


def test_dockerfile_installs_libfontconfig1_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libfontconfig1 via apt-get."""
    assert apt_get_install_packages.find('libfontconfig1') != -1


def test_dockerfile_installs_libfreetype6_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libfreetype6 via apt-get."""
    assert apt_get_install_packages.find('libfreetype6') != -1


def test_dockerfile_installs_libgbm1_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libgbm1 via apt-get."""
    assert apt_get_install_packages.find('libgbm1') != -1


def test_dockerfile_installs_libgl1_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libgl1 via apt-get."""
    assert apt_get_install_packages.find('libgl1') != -1


def test_dockerfile_installs_libgl1_mesa_dri_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libgl1-mesa-dri via apt-get."""
    assert apt_get_install_packages.find('libgl1-mesa-dri') != -1


def test_dockerfile_installs_libglib2_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libglib2.0-0t64 via apt-get."""
    assert apt_get_install_packages.find('libglib2.0-0t64') != -1


def test_dockerfile_installs_libglx_mesa0_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libglx-mesa0 via apt-get."""
    assert apt_get_install_packages.find('libglx-mesa0') != -1


def test_dockerfile_installs_libglx0_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libglx0 via apt-get."""
    assert apt_get_install_packages.find('libglx0') != -1


def test_dockerfile_installs_libharfbuzz0b_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libharfbuzz0b via apt-get."""
    assert apt_get_install_packages.find('libharfbuzz0b') != -1


def test_dockerfile_installs_libicu76_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libicu76 via apt-get."""
    assert apt_get_install_packages.find('libicu76') != -1


def test_dockerfile_installs_liblttng_ust1_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs liblttng-ust1 via apt-get."""
    assert apt_get_install_packages.find('liblttng-ust1') != -1


def test_dockerfile_installs_libnss3_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libnss3 via apt-get."""
    assert apt_get_install_packages.find('libnss3') != -1


def test_dockerfile_installs_libpango_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libpango-1.0-0 via apt-get."""
    assert apt_get_install_packages.find('libpango-1.0-0') != -1


def test_dockerfile_installs_libsm6_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libsm6 via apt-get."""
    assert apt_get_install_packages.find('libsm6') != -1


def test_dockerfile_installs_libssl3t64_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libssl3t64 via apt-get."""
    assert apt_get_install_packages.find('libssl3t64') != -1


def test_dockerfile_installs_libthai0_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libthai0 via apt-get."""
    assert apt_get_install_packages.find('libthai0') != -1


def test_dockerfile_installs_libxaw7_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxaw7 via apt-get."""
    assert apt_get_install_packages.find('libxaw7') != -1


def test_dockerfile_installs_libxcomposite1_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libxcomposite1 via apt-get."""
    assert apt_get_install_packages.find('libxcomposite1') != -1


def test_dockerfile_installs_libxdamage1_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxdamage1 via apt-get."""
    assert apt_get_install_packages.find('libxdamage1') != -1


def test_dockerfile_installs_libxext6_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxext6 via apt-get."""
    assert apt_get_install_packages.find('libxext6') != -1


def test_dockerfile_installs_libxfixes3_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxfixes3 via apt-get."""
    assert apt_get_install_packages.find('libxfixes3') != -1


def test_dockerfile_installs_libxfont2_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxfont2 via apt-get."""
    assert apt_get_install_packages.find('libxfont2') != -1


def test_dockerfile_installs_libxi6_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxi6 via apt-get."""
    assert apt_get_install_packages.find('libxi6') != -1


def test_dockerfile_installs_libxkbcommon0_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs libxkbcommon0 via apt-get."""
    assert apt_get_install_packages.find('libxkbcommon0') != -1


def test_dockerfile_installs_libxmu6_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxmu6 via apt-get."""
    assert apt_get_install_packages.find('libxmu6') != -1


def test_dockerfile_installs_libxrandr2_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxrandr2 via apt-get."""
    assert apt_get_install_packages.find('libxrandr2') != -1


def test_dockerfile_installs_libxt6t64_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxt6t64 via apt-get."""
    assert apt_get_install_packages.find('libxt6t64') != -1


def test_dockerfile_installs_libxxf86vm1_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs libxxf86vm1 via apt-get."""
    assert apt_get_install_packages.find('libxxf86vm1') != -1


def test_dockerfile_installs_mesa_libgallium_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs mesa-libgallium via apt-get."""
    assert apt_get_install_packages.find('mesa-libgallium') != -1


def test_dockerfile_installs_procps_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs procps via apt-get."""
    assert apt_get_install_packages.find('procps') != -1


def test_dockerfile_installs_python3_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs python3 via apt-get."""
    assert apt_get_install_packages.find('python3') != -1


def test_dockerfile_installs_python3_pip_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs python3-pip via apt-get."""
    assert apt_get_install_packages.find('python3-pip') != -1


def test_dockerfile_installs_sudo_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs sudo via apt-get."""
    assert apt_get_install_packages.find('sudo') != -1


def test_dockerfile_installs_tar_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs tar via apt-get."""
    assert apt_get_install_packages.find('tar') != -1


def test_dockerfile_installs_unzip_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs unzip via apt-get."""
    assert apt_get_install_packages.find('unzip') != -1


def test_dockerfile_installs_wget_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs wget via apt-get."""
    assert apt_get_install_packages.find('wget') != -1


def test_dockerfile_installs_x11_xkb_utils_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs x11-xkb-utils via apt-get."""
    assert apt_get_install_packages.find('x11-xkb-utils') != -1


def test_dockerfile_installs_xfonts_scalable_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs xfonts-scalable via apt-get."""
    assert apt_get_install_packages.find('xfonts-scalable') != -1


def test_dockerfile_installs_xfonts_utils_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs xfonts-utils via apt-get."""
    assert apt_get_install_packages.find('xfonts-utils') != -1


def test_dockerfile_installs_xserver_common_via_apt_get(
    apt_get_install_packages
):
    """Test that Dockerfile installs xserver-common via apt-get."""
    assert apt_get_install_packages.find('xserver-common') != -1


def test_dockerfile_installs_xvfb_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs xvfb via apt-get."""
    assert apt_get_install_packages.find('xvfb') != -1


def test_dockerfile_installs_zip_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs zip via apt-get."""
    assert apt_get_install_packages.find('zip') != -1


def test_dockerfile_installs_zlib1g_via_apt_get(apt_get_install_packages):
    """Test that Dockerfile installs zlib1g via apt-get."""
    assert apt_get_install_packages.find('zlib1g') != -1
