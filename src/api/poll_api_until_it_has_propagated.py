import sys
import time
import argparse
import requests


def poll_until_propagated(api_endpoint: str, max_attempts: int = 10) -> bool:
    for attempt in range(max_attempts):
        try:
            response = requests.get(
                f"{api_endpoint}/invalid",
                timeout=10,
                allow_redirects=True
            )

            if response.status_code == 404:
                print(f"API propagation confirmed after {attempt + 1} attempts")
                return True

            print(f"Attempt {attempt + 1}/{max_attempts}: Got status {response.status_code}, expected 404")

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_attempts}: Request failed: {e}")

        if attempt < max_attempts - 1:
            wait_time = 2 ** attempt
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

    print(f"API propagation failed after {max_attempts} attempts")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('api_endpoint', help='API endpoint URL to validate')
    parser.add_argument('--max-attempts', type=int, default=10, help='Maximum polling attempts')
    args = parser.parse_args()

    api_endpoint = args.api_endpoint.rstrip('/')

    print(f"Polling API endpoint: {api_endpoint}")
    print("Validating /invalid returns 404 status code...")

    success = poll_until_propagated(api_endpoint, args.max_attempts)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
