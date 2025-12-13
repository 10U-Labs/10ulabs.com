#!/usr/bin/env python3
"""Build a Lambda layer with Python dependencies.

Usage: python build.py <layer_name> <requirements_path> <output_path>
"""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def build_layer(layer_name: str, requirements_path: Path, output_path: Path) -> None:
    """Build a Lambda layer zip file."""
    print(f"Building Lambda layer: {layer_name}")
    print(f"Requirements: {requirements_path}")
    print(f"Output: {output_path}")

    layer_src_dir = requirements_path.parent

    with tempfile.TemporaryDirectory() as build_dir:
        build_path = Path(build_dir)
        python_dir = build_path / "python"
        python_dir.mkdir()

        # Install dependencies for Lambda's ARM64 Linux runtime
        subprocess.run(
            [
                "python3",
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_path),
                "-t",
                str(python_dir),
                "--platform",
                "manylinux2014_aarch64",
                "--implementation",
                "cp",
                "--python-version",
                "3.13",
                "--only-binary=:all:",
                "--quiet",
            ],
            check=True,
        )

        # Copy any Python modules from the layer source directory
        for pyfile in layer_src_dir.glob("*.py"):
            if pyfile.name != "build.py":
                shutil.copy(pyfile, python_dir)
                print(f"Added module: {pyfile.name}")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the zip
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in python_dir.rglob("*"):
                if file.is_file():
                    arcname = f"python/{file.relative_to(python_dir)}"
                    zf.write(file, arcname)

        size_kb = output_path.stat().st_size / 1024
        print(f"Layer built: {output_path} ({size_kb:.0f}K)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <layer_name> <requirements_path> <output_path>")
        sys.exit(1)

    build_layer(
        layer_name=sys.argv[1],
        requirements_path=Path(sys.argv[2]),
        output_path=Path(sys.argv[3]).resolve(),
    )
