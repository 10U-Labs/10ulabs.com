"""Tests for the account the ECS runner image runs its jobs as."""
from test.api.endpoints.runners.ecs.images.conftest import DOCKERFILE_PATH


def _read_dockerfile():
    """Read the Dockerfile the runner image is built from."""
    with open(DOCKERFILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def _user_directives():
    """List the argument of every USER instruction in the Dockerfile."""
    return [
        line.split(maxsplit=1)[1].strip()
        for line in _read_dockerfile().splitlines()
        if line.startswith('USER ')
    ]


def test_dockerfile_runs_as_a_numeric_uid():
    """Test that every USER instruction names a uid rather than an account name."""
    directives = _user_directives()
    assert directives and all(
        part.isdigit() for user in directives for part in user.split(':')
    ), f"USER must name a numeric uid; the Dockerfile has {directives or 'none'}"


def test_dockerfile_creates_the_uid_it_runs_as():
    """Test that a useradd in the Dockerfile creates the uid USER names."""
    uid = _user_directives()[0].split(':')[0]
    assert f"useradd -m -u {uid} " in _read_dockerfile(), (
        f"USER names uid {uid}, which no useradd in the Dockerfile creates"
    )
