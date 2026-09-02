import runpy
import sys
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest

import invalidate_cloudfront
from invalidate_cloudfront import find_distribution_id, main, wait_for_invalidation


SCRIPT = invalidate_cloudfront.__file__
ARGV = [
    "invalidate_cloudfront.py",
    "--fqdn", "10ulabs.com",
    "--region", "us-east-2",
    "--paths", "/index.html",
]


def _listing(*distributions: Any) -> Dict[str, Any]:
    return {
        "DistributionList": {
            "Items": [
                {"Id": identifier, "Aliases": {"Items": list(aliases)}}
                for identifier, aliases in distributions
            ]
        }
    }


def _serving(status: str) -> MagicMock:
    cloudfront = MagicMock()
    cloudfront.list_distributions.return_value = _listing(("E1", ["10ulabs.com"]))
    cloudfront.create_invalidation.return_value = {"Invalidation": {"Id": "I1"}}
    cloudfront.get_invalidation.return_value = {"Invalidation": {"Status": status}}
    return cloudfront


def _run_main(cloudfront: Any, argv: Optional[List[str]] = None) -> Tuple[int, MagicMock]:
    with patch("boto3.client", return_value=cloudfront) as factory, \
            patch.object(sys, "argv", argv or ARGV), \
            patch("invalidate_cloudfront.time.sleep"):
        return main(), factory


def _exit_code_of_the_script() -> Any:
    try:
        runpy.run_path(SCRIPT, run_name="__main__")
    except SystemExit as exited:
        return exited.code
    return None


class TestFindDistributionId:
    def test_returns_none_when_no_distribution_carries_the_domain(self) -> None:
        cloudfront = MagicMock()
        cloudfront.list_distributions.return_value = {
            "DistributionList": {
                "Items": [
                    {"Id": "E1", "Aliases": {"Items": ["other.example.com"]}}
                ]
            }
        }
        assert find_distribution_id(cloudfront, "10ulabs.com") is None

    def test_returns_the_id_of_the_distribution_carrying_the_domain(self) -> None:
        cloudfront = MagicMock()
        cloudfront.list_distributions.return_value = _listing(
            ("E1", ["other.example.com"]), ("E2", ["10ulabs.com"])
        )
        assert find_distribution_id(cloudfront, "10ulabs.com") == "E2"

    def test_returns_the_first_id_when_two_distributions_carry_the_domain(self) -> None:
        cloudfront = MagicMock()
        cloudfront.list_distributions.return_value = _listing(
            ("E1", ["10ulabs.com"]), ("E2", ["10ulabs.com"])
        )
        assert find_distribution_id(cloudfront, "10ulabs.com") == "E1"

    def test_returns_none_when_the_response_lists_no_distributions(self) -> None:
        cloudfront = MagicMock()
        cloudfront.list_distributions.return_value = {}
        assert find_distribution_id(cloudfront, "10ulabs.com") is None


class TestWaitForInvalidation:
    def test_raises_runtime_error_when_status_never_completes(self) -> None:
        cloudfront = MagicMock()
        cloudfront.get_invalidation.return_value = {
            "Invalidation": {"Status": "InProgress"}
        }
        with pytest.raises(RuntimeError):
            wait_for_invalidation(cloudfront, "E1", "I1", max_attempts=1)

    def test_returns_none_when_the_first_status_read_says_completed(self) -> None:
        cloudfront = MagicMock()
        cloudfront.get_invalidation.return_value = {
            "Invalidation": {"Status": "Completed"}
        }
        wait_for_invalidation(cloudfront, "E1", "I1")

    def test_sleeps_the_poll_interval_between_two_status_reads(self) -> None:
        cloudfront = MagicMock()
        cloudfront.get_invalidation.side_effect = [
            {"Invalidation": {"Status": "InProgress"}},
            {"Invalidation": {"Status": "Completed"}},
        ]
        with patch("invalidate_cloudfront.time.sleep") as sleep:
            wait_for_invalidation(cloudfront, "E1", "I1", poll_interval=7)
        assert sleep.call_args.args == (7,)

    def test_stops_reading_once_the_status_reaches_completed(self) -> None:
        cloudfront = MagicMock()
        cloudfront.get_invalidation.side_effect = [
            {"Invalidation": {"Status": "InProgress"}},
            {"Invalidation": {"Status": "Completed"}},
        ]
        with patch("invalidate_cloudfront.time.sleep"):
            wait_for_invalidation(cloudfront, "E1", "I1", max_attempts=20)
        assert cloudfront.get_invalidation.call_count == 2


class TestMain:
    def test_returns_1_when_no_distribution_carries_the_domain(self) -> None:
        cloudfront = MagicMock()
        cloudfront.list_distributions.return_value = _listing(
            ("E1", ["other.example.com"])
        )
        assert _run_main(cloudfront)[0] == 1

    def test_returns_1_when_the_invalidation_never_completes(self) -> None:
        assert _run_main(_serving("InProgress"))[0] == 1

    def test_returns_0_when_the_invalidation_completes(self) -> None:
        assert _run_main(_serving("Completed"))[0] == 0

    def test_passes_each_comma_separated_path_as_its_own_stripped_item(self) -> None:
        cloudfront = _serving("Completed")
        argv = ARGV[:-1] + ["/index.html, /assets/*"]
        _run_main(cloudfront, argv)
        batch = cloudfront.create_invalidation.call_args.kwargs["InvalidationBatch"]
        assert batch["Paths"]["Items"] == ["/index.html", "/assets/*"]

    def test_builds_its_client_in_the_region_it_is_given(self) -> None:
        argv = ["invalidate_cloudfront.py", "--fqdn", "10ulabs.com",
                "--region", "eu-west-1", "--paths", "/index.html"]
        factory = _run_main(_serving("Completed"), argv)[1]
        assert factory.call_args.kwargs["region_name"] == "eu-west-1"


def test_entry_point() -> None:
    with patch("boto3.client", return_value=_serving("Completed")), \
            patch.object(sys, "argv", ARGV):
        assert _exit_code_of_the_script() == 0
