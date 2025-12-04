#!/usr/bin/env python3
import os
import stat
from pathlib import Path


def main():
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent
    hooks_dir = repo_root / '.git' / 'hooks'

    print("Installing git hooks...")

    pre_commit_source = script_dir / 'pre-commit'
    pre_commit_target = hooks_dir / 'pre-commit'

    if pre_commit_target.is_symlink():
        pre_commit_target.unlink()
    elif pre_commit_target.exists():
        pre_commit_target.unlink()

    pre_commit_target.symlink_to(pre_commit_source)

    pre_commit_source.chmod(pre_commit_source.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print("Git hooks installed successfully.")


if __name__ == '__main__':
    main()
