"""Unit tests for the Lambda layer build script."""

import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.api.endpoints.agents.shared.lambda_layer.build import build_layer


@pytest.fixture
def layer_source_dir(tmp_path):
    """Create a temporary layer source directory with test files."""
    layer_dir = tmp_path / "lambda_layer"
    layer_dir.mkdir()
    (layer_dir / "requirements.txt").write_text("PyJWT>=2.8.0\n")
    (layer_dir / "github_auth.py").write_text("# auth module\n")
    (layer_dir / "build.py").write_text("# build script\n")
    return layer_dir


@pytest.fixture
def output_path(tmp_path):
    """Create output path for the zip file."""
    return tmp_path / "output" / "layer.zip"


class TestBuildLayerPipInvocation:
    """Tests for pip install invocation."""

    def test_calls_pip_with_requirements_flag(self, layer_source_dir, output_path):
        """Test that pip is called with the -r flag."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert "-r" in args

    def test_calls_pip_with_requirements_path(self, layer_source_dir, output_path):
        """Test that pip is called with the requirements file path."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert str(requirements_path) in args

    def test_calls_pip_with_platform_flag(self, layer_source_dir, output_path):
        """Test that pip is called with --platform flag."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert "--platform" in args

    def test_calls_pip_with_arm64_platform(self, layer_source_dir, output_path):
        """Test that pip targets ARM64 Linux platform."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert "manylinux2014_aarch64" in args

    def test_calls_pip_with_python_version_flag(self, layer_source_dir, output_path):
        """Test that pip is called with --python-version flag."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert "--python-version" in args

    def test_calls_pip_with_python313(self, layer_source_dir, output_path):
        """Test that pip targets Python 3.13."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert "3.13" in args

    def test_calls_pip_with_only_binary(self, layer_source_dir, output_path):
        """Test that pip only installs binary wheels."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert "--only-binary=:all:" in args

    def test_calls_pip_with_check_true(self, layer_source_dir, output_path):
        """Test that pip is called with check=True to raise on failure."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            assert mock_run.call_args[1]["check"] is True

    def test_uses_python3_for_pip(self, layer_source_dir, output_path):
        """Test that pip is invoked via python3 for PATH resolution."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert args[0] == "python3"

    def test_uses_module_flag_for_pip(self, layer_source_dir, output_path):
        """Test that pip is invoked with -m flag."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert args[1] == "-m"

    def test_invokes_pip_module(self, layer_source_dir, output_path):
        """Test that pip module is specified."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run") as mock_run:
            build_layer("test_layer", requirements_path, output_path)
            args = mock_run.call_args[0][0]
            assert args[2] == "pip"


class TestBuildLayerModuleCopying:
    """Tests for Python module copying behavior."""

    def test_copies_python_modules_to_zip(self, layer_source_dir, output_path):
        """Test that Python modules are included in the zip."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run"):
            build_layer("test_layer", requirements_path, output_path)
            with zipfile.ZipFile(output_path, "r") as zf:
                names = zf.namelist()
                assert "python/github_auth.py" in names

    def test_excludes_build_script_from_zip(self, layer_source_dir, output_path):
        """Test that build.py is not included in the zip."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run"):
            build_layer("test_layer", requirements_path, output_path)
            with zipfile.ZipFile(output_path, "r") as zf:
                names = zf.namelist()
                assert "python/build.py" not in names


class TestBuildLayerOutputHandling:
    """Tests for output file and directory handling."""

    def test_creates_output_directory_if_missing(self, layer_source_dir, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        requirements_path = layer_source_dir / "requirements.txt"
        nested_output = tmp_path / "nested" / "dir" / "layer.zip"
        with patch("subprocess.run"):
            build_layer("test_layer", requirements_path, nested_output)
            assert nested_output.exists()

    def test_creates_valid_zip_file(self, layer_source_dir, output_path):
        """Test that output is a valid zip file."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run"):
            build_layer("test_layer", requirements_path, output_path)
            assert zipfile.is_zipfile(output_path)

    def test_zip_uses_deflate_compression(self, layer_source_dir, output_path):
        """Test that zip file uses DEFLATE compression."""
        requirements_path = layer_source_dir / "requirements.txt"
        with patch("subprocess.run"):
            build_layer("test_layer", requirements_path, output_path)
            with zipfile.ZipFile(output_path, "r") as zf:
                for info in zf.infolist():
                    assert info.compress_type == zipfile.ZIP_DEFLATED
