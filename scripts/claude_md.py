#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def check_claude_md_should_be_updated() -> bool:
    result = subprocess.run(
        ['markdownlint-cli2', 'CLAUDE.md'],
        capture_output=True,
        text=True
    )
    should_be_updated = result.returncode != 0
    if should_be_updated:
        logging.info("markdownlint-cli2 found formatting issues in CLAUDE.md")
        if result.stdout:
            logging.info("Output: %s", result.stdout.strip())
        if result.stderr:
            logging.info("Errors: %s", result.stderr.strip())
    else:
        logging.info("CLAUDE.md is properly formatted")
    return should_be_updated

def update_claude_md() -> bool:
    result = subprocess.run(
        ['markdownlint-cli2', '--fix', 'CLAUDE.md'],
        capture_output=True,
        text=True
    )
    if result.stdout:
        logging.info("markdownlint-cli2 output: %s", result.stdout.strip())
    if result.stderr:
        logging.warning("markdownlint-cli2 errors: %s", result.stderr.strip())
    logging.info("Applied markdownlint fixes to CLAUDE.md")
    return True

def main():
    parser = argparse.ArgumentParser(description='Check or update CLAUDE.md formatting')
    parser.add_argument('--check', action='store_true', help='Check if CLAUDE.md needs formatting')
    parser.add_argument('--update', action='store_true', help='Update CLAUDE.md formatting')
    parser.add_argument('--output-file', help='Output file for check result (for GitHub Actions)')
    args = parser.parse_args()
    if not args.check and not args.update:
        logging.error("Must specify either --check or --update")
        sys.exit(1)
    if args.check:
        should_be_updated = check_claude_md_should_be_updated()
        if args.output_file:
            with open(args.output_file, 'a', encoding='utf-8') as f:
                f.write(f"claude_md_should_be_updated={'true' if should_be_updated else 'false'}\n")
        sys.exit(0)
    elif args.update:
        update_claude_md()
        logging.info("CLAUDE.md updated")
        sys.exit(0)

if __name__ == '__main__':
    main()
