"""Comprehensive tests for the invalidate_cloudfront script."""
from unittest.mock import MagicMock

import pytest

from invalidate_cloudfront import find_distribution_id, wait_for_invalidation


class TestFindDistributionId:
    """Tests for find_distribution_id function."""

    def test_returns_none_when_no_distribution_carries_the_domain(self):
        """find_distribution_id reports no match for an unknown domain."""
        cloudfront = MagicMock()
        cloudfront.list_distributions.return_value = {
            "DistributionList": {
                "Items": [
                    {"Id": "E1", "Aliases": {"Items": ["other.example.com"]}}
                ]
            }
        }
        assert find_distribution_id(cloudfront, "10ulabs.com") is None


class TestWaitForInvalidation:
    """Tests for wait_for_invalidation function."""

    def test_raises_runtime_error_when_status_never_completes(self):
        """wait_for_invalidation gives up once max_attempts is exhausted."""
        cloudfront = MagicMock()
        cloudfront.get_invalidation.return_value = {
            "Invalidation": {"Status": "InProgress"}
        }
        with pytest.raises(RuntimeError):
            wait_for_invalidation(cloudfront, "E1", "I1", max_attempts=1)
