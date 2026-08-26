from pathlib import Path


def _find_repo_root_from_path(start_path: Path) -> Path:
    for parent in [start_path] + list(start_path.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


def _find_repo_root() -> Path:
    return _find_repo_root_from_path(Path(__file__).resolve())


REPO_ROOT = _find_repo_root()


def extract_brace_block(content: str, start_pos: int) -> str:
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[start_pos:start_pos + i + 1]
    return content[start_pos:]
