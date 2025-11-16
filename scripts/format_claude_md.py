#!/usr/bin/env python3
import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def main():
    result = subprocess.run(
        ['markdownlint-cli2', '--fix', 'CLAUDE.md'],
        capture_output=True,
        text=True
    )
    logging.info("Applied markdownlint fixes to CLAUDE.md")
    sys.exit(0)

if __name__ == '__main__':
    main()
