from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import MagicMock

from test_fixtures.aws import (
    find_lifecycle_rule,
    iam_role_exists,
    stale_delete_markers,
)


def test_returns_true_when_role_exists() -> None:
    mock_client = MagicMock()
    mock_client.get_role.return_value = {
        "Role": {"RoleName": "test-role", "Arn": "arn:aws:iam::123456:role/test-role"}
    }
    result = iam_role_exists(mock_client, "test-role")
    assert result is True


def test_returns_false_when_role_not_found() -> None:
    mock_client = MagicMock()
    mock_client.exceptions.NoSuchEntityException = type(
        "NoSuchEntityException", (Exception,), {}
    )
    mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException()
    result = iam_role_exists(mock_client, "nonexistent-role")
    assert result is False


def test_calls_get_role_with_role_name() -> None:
    mock_client = MagicMock()
    mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
    iam_role_exists(mock_client, "my-role")
    assert mock_client.get_role.call_args[1]["RoleName"] == "my-role"


def test_passes_role_name_argument() -> None:
    mock_client = MagicMock()
    mock_client.get_role.return_value = {"Role": {}}
    iam_role_exists(mock_client, "custom-role-name")
    call_args = mock_client.get_role.call_args
    assert call_args[1]["RoleName"] == "custom-role-name"


class TestFindLifecycleRule:
    @staticmethod
    def _client(*rules: Any) -> MagicMock:
        client = MagicMock()
        client.get_bucket_lifecycle_configuration.return_value = {"Rules": list(rules)}
        return client

    def test_returns_the_rule_whose_id_matches(self) -> None:
        wanted = {"ID": "expire-delete-markers", "Status": "Enabled"}
        found = find_lifecycle_rule(self._client(wanted), "a-bucket", "expire-delete-markers")
        assert found == wanted

    def test_returns_none_when_no_rule_carries_that_id(self) -> None:
        other = {"ID": "abort-multipart-uploads", "Status": "Enabled"}
        found = find_lifecycle_rule(self._client(other), "a-bucket", "expire-delete-markers")
        assert found is None

    def test_reaches_a_rule_that_is_not_the_first(self) -> None:
        wanted = {"ID": "expire-delete-markers", "Status": "Enabled"}
        first = {"ID": "abort-multipart-uploads", "Status": "Disabled"}
        found = find_lifecycle_rule(
            self._client(first, wanted), "a-bucket", "expire-delete-markers"
        )
        assert found == wanted


class TestStaleDeleteMarkers:
    @staticmethod
    def _client(*pages: Any) -> MagicMock:
        client = MagicMock()
        client.get_paginator.return_value.paginate.return_value = list(pages)
        return client

    @staticmethod
    def _marker(key: str, **age: Any) -> Dict[str, Any]:
        return {"Key": key, "LastModified": datetime.now(timezone.utc) - timedelta(**age)}

    def test_returns_the_key_of_a_marker_older_than_the_cutoff(self) -> None:
        pages = self._client({"DeleteMarkers": [self._marker("left-behind", days=30)]})
        assert stale_delete_markers(pages, "a-bucket") == ["left-behind"]

    def test_omits_a_marker_newer_than_the_cutoff(self) -> None:
        pages = self._client({"DeleteMarkers": [self._marker("just-deleted", minutes=5)]})
        assert not stale_delete_markers(pages, "a-bucket")

    def test_reads_every_page_the_paginator_yields(self) -> None:
        pages = self._client(
            {"DeleteMarkers": [self._marker("first-page", days=30)]},
            {"DeleteMarkers": [self._marker("second-page", days=30)]},
        )
        assert stale_delete_markers(pages, "a-bucket") == ["first-page", "second-page"]
