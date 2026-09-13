import pytest
from repo_utils import REPO_ROOT

CLOUDFRONT_TF = REPO_ROOT / "src" / "www" / "common" / "cloudfront_s3.tf"
HEADERS_POLICY = 'resource "aws_cloudfront_response_headers_policy" "website"'


@pytest.fixture(name='headers_policy')
def headers_policy_fixture() -> str:
    content = CLOUDFRONT_TF.read_text(encoding='utf-8')
    start = content.index(HEADERS_POLICY)
    return content[start:content.index('\n}\n', start)]


def test_response_headers_policy_forbids_sniffing_the_content_type(headers_policy: str) -> None:
    assert 'content_type_options {' in headers_policy


def test_response_headers_policy_sends_the_referrer_to_the_origin_alone_across_sites(
    headers_policy: str
) -> None:
    assert 'referrer_policy = "strict-origin-when-cross-origin"' in headers_policy


def test_response_headers_policy_denies_framing(headers_policy: str) -> None:
    assert 'frame_option = "DENY"' in headers_policy


@pytest.mark.parametrize('block', ['content_type_options', 'referrer_policy', 'frame_options'])
def test_response_headers_policy_overrides_what_the_origin_sends(
    headers_policy: str, block: str
) -> None:
    start = headers_policy.index(f'{block} {{')
    assert 'override = true' in headers_policy[start:headers_policy.index('}', start)]
