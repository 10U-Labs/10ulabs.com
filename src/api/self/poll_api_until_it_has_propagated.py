import sys
import time
import json
import argparse
import requests


def validate_root_endpoint(api_endpoint: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"{api_endpoint}/", timeout=10, allow_redirects=True)

        if response.status_code == 403:
            return False, f"Root endpoint returned 403 Forbidden - likely WAF blocking or CloudFront not ready"

        if response.status_code != 200:
            return False, f"Root endpoint returned {response.status_code}, expected 200"

        if 'text/html' not in response.headers.get('Content-Type', ''):
            return False, f"Root endpoint returned wrong content type: {response.headers.get('Content-Type')}"

        if 'swagger' not in response.text.lower():
            return False, "Root endpoint doesn't contain Swagger UI"

        return True, "Root endpoint (Swagger UI) working correctly"

    except requests.exceptions.RequestException as e:
        return False, f"Root endpoint request failed: {e}"


def validate_health_endpoint(api_endpoint: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"{api_endpoint}/health", timeout=10, allow_redirects=True)

        if response.status_code == 403:
            return False, f"Health endpoint returned 403 Forbidden - likely WAF blocking"

        if response.status_code != 200:
            return False, f"Health endpoint returned {response.status_code}, expected 200"

        if 'application/json' not in response.headers.get('Content-Type', ''):
            return False, f"Health endpoint returned wrong content type: {response.headers.get('Content-Type')}"

        try:
            body = response.json()
            if body.get('status') != 'healthy':
                return False, f"Health endpoint returned unexpected status: {body.get('status')}"
            if body.get('service') != '10U Labs API':
                return False, f"Health endpoint returned unexpected service: {body.get('service')}"
        except json.JSONDecodeError:
            return False, "Health endpoint returned invalid JSON"

        return True, "Health endpoint working correctly"

    except requests.exceptions.RequestException as e:
        return False, f"Health endpoint request failed: {e}"


def validate_echo_endpoint(api_endpoint: str) -> tuple[bool, str]:
    try:
        test_payload = {'test': 'validation', 'timestamp': time.time()}
        response = requests.post(
            f"{api_endpoint}/v1/echo",
            json=test_payload,
            timeout=10,
            allow_redirects=True
        )

        if response.status_code == 403:
            return False, f"Echo endpoint returned 403 Forbidden - likely WAF blocking"

        if response.status_code != 200:
            return False, f"Echo endpoint returned {response.status_code}, expected 200"

        if 'application/json' not in response.headers.get('Content-Type', ''):
            return False, f"Echo endpoint returned wrong content type: {response.headers.get('Content-Type')}"

        try:
            body = response.json()
            if 'echo' not in body:
                return False, "Echo endpoint didn't return 'echo' field"
            if body['echo'] != test_payload:
                return False, f"Echo endpoint didn't echo payload correctly: {body['echo']}"
            if 'received_at' not in body:
                return False, "Echo endpoint didn't return 'received_at' field"
        except json.JSONDecodeError:
            return False, "Echo endpoint returned invalid JSON"

        return True, "Echo endpoint working correctly"

    except requests.exceptions.RequestException as e:
        return False, f"Echo endpoint request failed: {e}"


def validate_invalid_endpoint(api_endpoint: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"{api_endpoint}/invalid", timeout=10, allow_redirects=True)

        if response.status_code == 403:
            return False, f"Invalid endpoint returned 403 instead of 404 - WAF may be misconfigured"

        if response.status_code != 404:
            return False, f"Invalid endpoint returned {response.status_code}, expected 404"

        return True, "Invalid endpoint correctly returns 404"

    except requests.exceptions.RequestException as e:
        return False, f"Invalid endpoint request failed: {e}"


def poll_until_propagated(api_endpoint: str, max_attempts: int = 20) -> bool:
    endpoints = [
        ("Root (Swagger UI)", validate_root_endpoint),
        ("Health", validate_health_endpoint),
        ("Echo", validate_echo_endpoint),
        ("Invalid (404)", validate_invalid_endpoint)
    ]

    for attempt in range(max_attempts):
        print(f"\n=== Attempt {attempt + 1}/{max_attempts} ===")

        all_passed = True
        results = []

        for name, validator in endpoints:
            success, message = validator(api_endpoint)
            status = "✓" if success else "✗"
            print(f"{status} {name}: {message}")
            results.append((name, success, message))

            if not success:
                all_passed = False

        if all_passed:
            print(f"\n✓ All endpoints validated successfully after {attempt + 1} attempts")
            return True

        if attempt < max_attempts - 1:
            wait_time = min(2 ** attempt, 60)
            print(f"\nWaiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

    print(f"\n✗ API validation failed after {max_attempts} attempts")
    print("\nFailed endpoints:")
    for name, success, message in results:
        if not success:
            print(f"  - {name}: {message}")

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('api_endpoint', help='API endpoint URL to validate')
    parser.add_argument('--max-attempts', type=int, default=20, help='Maximum polling attempts')
    args = parser.parse_args()

    api_endpoint = args.api_endpoint.rstrip('/')

    print(f"Validating API endpoint: {api_endpoint}")
    print("Testing all endpoints: /, /health, /v1/echo, /invalid")

    success = poll_until_propagated(api_endpoint, args.max_attempts)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
