"""Fixtures for runners/ecs/images endpoint unit tests."""
import importlib.util
import sys
import urllib.error
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from repo_utils import REPO_ROOT

LAMBDA_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs" / "images" / "lambda"
HANDLER_PATH = LAMBDA_DIR / "handler.py"

# Load the handler module
handler_spec = importlib.util.spec_from_file_location("handler", HANDLER_PATH)
if handler_spec is None or handler_spec.loader is None:
    raise ImportError("Could not load handler module")
handler = importlib.util.module_from_spec(handler_spec)
sys.modules['handler'] = handler
handler_spec.loader.exec_module(handler)


@pytest.fixture(autouse=True)
def reset_handler_state():
    """Reset handler module state before each test."""
    handler.set_test_mode(False)
    handler.set_client('ecr', None)
    yield
    handler.set_test_mode(False)
    handler.set_client('ecr', None)


@pytest.fixture
def mock_ecr_client():
    """Create a mock ECR client."""
    return MagicMock()


@pytest.fixture
def mock_ssm_client():
    """Create a mock SSM client."""
    return MagicMock()


def _call_handler_with_image(ecr_client, image, handler_fn):
    """Set up ECR mock with image and call handler function."""
    ecr_client.describe_images.return_value = {'imageDetails': [image]}
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler_fn()


def _make_api_event(
    method: str = 'GET',
    path: str = '/v1/runners/ecs/images',
    path_params: dict | None = None,
    headers: dict | None = None,
    body: str | None = None
) -> dict:
    """Create an API Gateway event dict."""
    return {
        'httpMethod': method,
        'path': path,
        'headers': headers or {},
        'body': body,
        'pathParameters': path_params
    }


@pytest.fixture
def make_api_event():
    """Return factory function for creating API Gateway events."""
    return _make_api_event


@pytest.fixture
def sample_event():
    """Create a sample API Gateway event."""
    return _make_api_event()


@pytest.fixture
def sample_event_with_test_mode():
    """Create a sample API Gateway event with test mode header."""
    return _make_api_event(headers={'x-test-mode': 'true'})


def _make_mock_http_response(status: int = 204):
    """Create a mock HTTP response for urllib tests."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


@pytest.fixture
def mock_http_response_204():
    """Return a mock HTTP response with status 204."""
    return _make_mock_http_response(204)


@pytest.fixture
def make_mock_http_response():
    """Return factory function for creating mock HTTP responses."""
    return _make_mock_http_response


def _make_client_error(code: str = 'AccessDenied', message: str = 'Access denied'):
    """Create a botocore ClientError for testing."""
    return ClientError(
        {'Error': {'Code': code, 'Message': message}},
        'DescribeImages'
    )


@pytest.fixture
def access_denied_error():
    """Return an AccessDenied ClientError."""
    return _make_client_error('AccessDenied', 'Access denied')


@pytest.fixture
def make_client_error():
    """Return factory function for creating ClientErrors."""
    return _make_client_error


@pytest.fixture(name="github_workflow_trigger_context")
def _github_workflow_trigger_context_fixture():
    """Provide a context for testing GitHub workflow triggers.

    Returns a function that runs a callback with mocked GitHub API calls,
    yielding the captured urlopen Request object.
    """
    http_response = _make_mock_http_response(204)

    @contextmanager
    def _trigger_context(callback):
        with patch('handler.get_github_token', return_value='valid-token'):
            urlopen_patch = patch(
                'urllib.request.urlopen', return_value=http_response)
            with urlopen_patch as mock_urlopen:
                with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                    callback()
        yield mock_urlopen.call_args[0][0]

    return _trigger_context


def _trigger_workflow_with_response(status: int):
    """Trigger a GitHub workflow with a specific response status and return result."""
    mock_response = _make_mock_http_response(status)
    with patch('handler.get_github_token', return_value='valid-token'):
        with patch('urllib.request.urlopen', return_value=mock_response):
            with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                return handler.trigger_github_workflow('test.yml', {'ref': 'main'})


@pytest.fixture(name="trigger_workflow_with_response")
def _trigger_workflow_with_response_fixture():
    """Return factory for triggering workflows with custom response status."""
    return _trigger_workflow_with_response


def _call_latest_endpoint_with_stable_image(ecr_client, digest='sha256:abc'):
    """Set up stable image and call GET /latest endpoint, returning response."""
    stable_image = {
        'imageDigest': digest,
        'imageTags': ['stable'],
        'imagePushedAt': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    ecr_client.describe_images.return_value = {'imageDetails': [stable_image]}
    handler.set_client('ecr', ecr_client)
    event = _make_api_event(path='/v1/runners/ecs/images/latest')
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.lambda_handler(event, None)


@pytest.fixture(name="call_latest_endpoint")
def _call_latest_endpoint_fixture():
    """Return function to call GET /latest with stable image setup."""
    ecr_client = MagicMock()

    def _call(digest='sha256:abc'):
        return _call_latest_endpoint_with_stable_image(ecr_client, digest)
    return _call


def _trigger_workflow_with_url_error():
    """Trigger workflow and simulate URLError, returning result."""
    with patch('handler.get_github_token', return_value='valid-token'):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
            with patch.dict('os.environ', {'GITHUB_REPO': 'org/repo'}):
                return handler.trigger_github_workflow('test.yml', {'ref': 'main'})


@pytest.fixture(name="url_error_workflow_result")
def _url_error_workflow_result_fixture():
    """Return result of triggering workflow with URLError."""
    return _trigger_workflow_with_url_error()


def _list_ecr_images_with_single_image(ecr_client, digest='sha256:abc123', tags=None):
    """Set up ECR client with single image and call list_ecr_images."""
    if tags is None:
        tags = ['latest', 'v1.0']
    image = {
        'imageDigest': digest,
        'imageTags': tags,
        'imagePushedAt': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    return _call_handler_with_image(ecr_client, image, handler.list_ecr_images)


@pytest.fixture(name="single_image_list_result")
def _single_image_list_result_fixture():
    """Return result of list_ecr_images with a single image."""
    ecr_client = MagicMock()
    return _list_ecr_images_with_single_image(ecr_client)


def _list_ecr_images_sorted_by_date():
    """Set up two images with different dates and return sorted result."""
    ecr_client = MagicMock()
    older_image = {
        'imageDigest': 'sha256:older',
        'imageTags': ['v1.0'],
        'imagePushedAt': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    newer_image = {
        'imageDigest': 'sha256:newer',
        'imageTags': ['v2.0'],
        'imagePushedAt': datetime(2024, 6, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    ecr_client.describe_images.return_value = {'imageDetails': [older_image, newer_image]}
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.list_ecr_images()


@pytest.fixture(name="sorted_images_result")
def _sorted_images_result_fixture():
    """Return result of list_ecr_images with two images sorted by date."""
    return _list_ecr_images_sorted_by_date()


def _get_latest_ecr_image_with_stable():
    """Set up stable image and call get_latest_ecr_image."""
    ecr_client = MagicMock()
    stable_image = {
        'imageDigest': 'sha256:stable123',
        'imageTags': ['stable', 'v1.0'],
        'imagePushedAt': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    ecr_client.describe_images.return_value = {'imageDetails': [stable_image]}
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.get_latest_ecr_image()


@pytest.fixture(name="stable_image_result")
def _stable_image_result_fixture():
    """Return result of get_latest_ecr_image with stable image."""
    return _get_latest_ecr_image_with_stable()


def _get_latest_ecr_image_no_stable():
    """Set up non-stable image and call get_latest_ecr_image."""
    ecr_client = MagicMock()
    non_stable_image = {
        'imageDigest': 'sha256:latest123',
        'imageTags': ['latest'],
        'imagePushedAt': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    ecr_client.describe_images.return_value = {'imageDetails': [non_stable_image]}
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.get_latest_ecr_image()


@pytest.fixture(name="no_stable_image_result")
def _no_stable_image_result_fixture():
    """Return result of get_latest_ecr_image with no stable image."""
    return _get_latest_ecr_image_no_stable()


def _get_ecr_image_by_digest_result():
    """Set up image and call get_ecr_image_by_digest."""
    ecr_client = MagicMock()
    image = {
        'imageDigest': 'sha256:abc123',
        'imageTags': ['v1.0'],
        'imagePushedAt': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    return _call_handler_with_image(
        ecr_client, image, lambda: handler.get_ecr_image_by_digest('sha256:abc123')
    )


@pytest.fixture(name="image_by_digest_result")
def _image_by_digest_result_fixture():
    """Return result of get_ecr_image_by_digest."""
    return _get_ecr_image_by_digest_result()


def _get_ecr_image_not_found_result():
    """Call get_ecr_image_by_digest with empty response."""
    ecr_client = MagicMock()
    ecr_client.describe_images.return_value = {'imageDetails': []}
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.get_ecr_image_by_digest('sha256:notfound')


@pytest.fixture(name="image_not_found_result")
def _image_not_found_result_fixture():
    """Return result of get_ecr_image_by_digest for not found image."""
    return _get_ecr_image_not_found_result()


def _get_ecr_image_not_found_exception_result(make_error_fn):
    """Call get_ecr_image_by_digest with ImageNotFoundException."""
    ecr_client = MagicMock()
    ecr_client.describe_images.side_effect = make_error_fn(
        'ImageNotFoundException', 'Image not found')
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.get_ecr_image_by_digest('sha256:notfound')


@pytest.fixture(name="image_not_found_exception_result")
def _image_not_found_exception_result_fixture():
    """Return result of get_ecr_image_by_digest with ImageNotFoundException."""
    return _get_ecr_image_not_found_exception_result(_make_client_error)


def _delete_ecr_image_result():
    """Call delete_ecr_image and return result."""
    ecr_client = MagicMock()
    ecr_client.batch_delete_image.return_value = {}
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.delete_ecr_image('sha256:abc123')


@pytest.fixture(name="delete_image_result")
def _delete_image_result_fixture():
    """Return result of successful delete_ecr_image."""
    return _delete_ecr_image_result()


def _get_ecr_image_without_tags_result():
    """Set up image without tags and call get_ecr_image_by_digest."""
    ecr_client = MagicMock()
    image_no_tags = {
        'imageDigest': 'sha256:abc123',
        'imagePushedAt': datetime(2024, 1, 1, tzinfo=timezone.utc),
        'imageSizeInBytes': 1024
    }
    ecr_client.describe_images.return_value = {'imageDetails': [image_no_tags]}
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.get_ecr_image_by_digest('sha256:abc123')


@pytest.fixture(name="image_without_tags_result")
def _image_without_tags_result_fixture():
    """Return result of get_ecr_image_by_digest for image without tags."""
    return _get_ecr_image_without_tags_result()


def _delete_ecr_image_error_result():
    """Call delete_ecr_image with ClientError and return result."""
    ecr_client = MagicMock()
    ecr_client.batch_delete_image.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
        'BatchDeleteImage'
    )
    handler.set_client('ecr', ecr_client)
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        return handler.delete_ecr_image('sha256:abc123')


@pytest.fixture(name="delete_image_error_result")
def _delete_image_error_result_fixture():
    """Return result of delete_ecr_image with ClientError."""
    return _delete_ecr_image_error_result()
