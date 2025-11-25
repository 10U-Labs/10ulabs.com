import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'scripts' / 'cleanup_packer_artifacts'))

from cleanup_packer_artifacts import (
    get_snapshot_ids_for_ami,
    cleanup_amis,
    cleanup_snapshots,
)


@pytest.fixture
def mock_ec2_client():
    return MagicMock()
