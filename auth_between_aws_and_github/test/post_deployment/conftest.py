#!/usr/bin/env python3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_FILE = REPO_ROOT / 'auth_between_aws_and_github' / 'config.json'


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)
