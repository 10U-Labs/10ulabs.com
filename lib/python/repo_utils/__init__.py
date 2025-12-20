"""Repository path utilities."""

from pathlib import Path


def find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


REPO_ROOT = find_repo_root()


def extract_brace_block(content: str, start_pos: int) -> str:
    """Extract content of a brace-delimited block starting at the given position.

    Useful for parsing Terraform blocks, JSON objects, or other brace-delimited content.

    Args:
        content: The full text content to extract from.
        start_pos: Position of the opening brace in content.

    Returns:
        The block content including braces, or remaining content if no closing brace found.
    """
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[start_pos:start_pos + i + 1]
    return content[start_pos:]
