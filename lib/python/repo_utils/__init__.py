import re
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


_STATE_KEY_PATTERN = re.compile(r'^\s*key\s*=\s*"([^"]+)"', re.MULTILINE)


def state_key_for(stack_dir: Path) -> str:
    backend_path = stack_dir / "backend.tf"
    if not backend_path.exists():
        raise RuntimeError(f"No backend.tf at {backend_path}")
    match = _STATE_KEY_PATTERN.search(backend_path.read_text(encoding='utf-8'))
    if match is None:
        raise RuntimeError(f"No state key declared in {backend_path}")
    return match.group(1)
