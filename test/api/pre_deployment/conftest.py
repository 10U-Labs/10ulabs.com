from pathlib import Path


def test_src_api_directory_exists():
    api_path = Path(__file__).parent.parent.parent.parent / "src" / "api"
    assert api_path.exists()
