from pathlib import Path
def test_shared_file_exists(src_dir: Path) -> None:
    assert (src_dir / "shared.tf").exists()


def test_shared_common_module_defined(src_dir: Path) -> None:
    content = (src_dir / "shared.tf").read_text()
    assert 'module "common"' in content


def test_shared_module_source_path(src_dir: Path) -> None:
    content = (src_dir / "shared.tf").read_text()
    assert 'source = "../../../lib/terraform/common"' in content
