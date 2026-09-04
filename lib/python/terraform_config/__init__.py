import re
from pathlib import Path

TEST_AWS_REGION = "us-east-2"


def packaged_lambda_sources(tf_file: Path) -> list:
    pattern = r'(?:source_file\s*=|content\s*=\s*file\()\s*"\$\{path\.module\}/([^"]+)"'
    content = tf_file.read_text(encoding="utf-8")
    return [
        packaged
        for packaged in re.findall(pattern, content)
        if packaged.endswith(".py") and ".." not in Path(packaged).parts
    ]


def packaged_lambda_archives(tf_file: Path) -> list:
    pattern = r'output_path\s*=\s*"\$\{path\.module\}/([^"]+)"'
    content = tf_file.read_text(encoding="utf-8")
    return re.findall(pattern, content)
