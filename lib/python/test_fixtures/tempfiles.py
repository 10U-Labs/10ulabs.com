"""A temporary file written from a string, which several suites want.

The suites differ only in the suffix the file needs, so the writing is here
and the suffix is what each fixture supplies.
"""
import tempfile
from pathlib import Path


def write_temporary_file(content: str, suffix: str) -> Path:
    """Write content to a temporary file with a suffix and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False
    ) as handle:
        handle.write(content)
        handle.flush()
        return Path(handle.name)
