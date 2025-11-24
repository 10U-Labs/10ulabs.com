import subprocess


def run_command_in_container(tag, command):
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/bin/bash", tag, "-c", command],
        check=False,
        capture_output=True,
        text=True
    )
    return result
