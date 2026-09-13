import pytest

from repo_utils import REPO_ROOT

ROUTING_DIR = REPO_ROOT / "src" / "api" / "common" / "routing"
HEALTH_BEHAVIOUR = 'path_pattern           = "/health"'
DIAGNOSTICS_BEHAVIOUR = 'path_pattern           = "/diagnostics/*"'
API_ORIGIN = 'origin_id           = "api-10ulabs-com"'
API_ORIGIN_DOMAIN = "data.terraform_remote_state.api_10ulabs_com.outputs.api_gateway_execute_domain"
API_ROUTING_STATE = 'key    = "api.10ulabs.com/src/api/common/routing/terraform.tfstate"'


@pytest.fixture(name="cloudfront_tf")
def cloudfront_tf_fixture() -> str:
    return (ROUTING_DIR / "cloudfront_s3.tf").read_text(encoding="utf-8")


def _block_holding(content: str, opener: str, line: str) -> str:
    start = content.rindex(f"\n  {opener} {{\n", 0, content.index(line))
    return content[start:content.index("\n  }\n", start)]


def test_health_behaviour_targets_the_api_10ulabs_com_origin(cloudfront_tf: str) -> None:
    behaviour = _block_holding(cloudfront_tf, "ordered_cache_behavior", HEALTH_BEHAVIOUR)
    assert 'target_origin_id       = "api-10ulabs-com"' in behaviour


def test_diagnostics_behaviour_targets_the_api_10ulabs_com_origin(cloudfront_tf: str) -> None:
    behaviour = _block_holding(cloudfront_tf, "ordered_cache_behavior", DIAGNOSTICS_BEHAVIOUR)
    assert 'target_origin_id       = "api-10ulabs-com"' in behaviour


def test_diagnostics_behaviour_lets_post_through(cloudfront_tf: str) -> None:
    behaviour = _block_holding(cloudfront_tf, "ordered_cache_behavior", DIAGNOSTICS_BEHAVIOUR)
    assert '"POST"' in behaviour


def test_api_10ulabs_com_origin_is_that_repository_gateway(cloudfront_tf: str) -> None:
    assert API_ORIGIN_DOMAIN in _block_holding(cloudfront_tf, "origin", API_ORIGIN)


def test_routing_reads_api_10ulabs_com_routing_state_by_its_key() -> None:
    assert API_ROUTING_STATE in (ROUTING_DIR / "data.tf").read_text(encoding="utf-8")
