import json
import os
from pathlib import Path


def test_cdk_out_directory_exists():
    cdk_out_path = Path(__file__).parent.parent.parent / "src" / "api" / "cdk.out"
    assert cdk_out_path.exists()
    assert cdk_out_path.is_dir()


def test_cloudformation_template_exists():
    template_path = Path(__file__).parent.parent.parent / "src" / "api" / "cdk.out" / "TenULabsApi.template.json"
    assert template_path.exists()
    assert template_path.is_file()


def test_cloudformation_template_has_resources():
    template_path = Path(__file__).parent.parent.parent / "src" / "api" / "cdk.out" / "TenULabsApi.template.json"
    with open(template_path) as f:
        template = json.load(f)
    assert "Resources" in template
    assert len(template["Resources"]) > 0
