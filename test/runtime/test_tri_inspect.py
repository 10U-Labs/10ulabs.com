import subprocess

def test_tri_inspect():
    result = subprocess.run(
        ["python3", "src/runtime/cmd/tri-inspect/main.py", "test"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Inspecting component: test" in result.stdout
