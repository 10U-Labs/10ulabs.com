import json
from pathlib import Path
from typing import Dict, Any


def load_runner_config(config_path: Path) -> Dict[str, Any]:
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
