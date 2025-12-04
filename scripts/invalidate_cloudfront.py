import argparse
import sys
import time
import uuid
import boto3


def find_distribution_id(cloudfront, fqdn):
    response = cloudfront.list_distributions()
    distribution_id = None
    for distribution in response.get("DistributionList", {}).get("Items", []):
        aliases = distribution.get("Aliases", {}).get("Items", [])
        if distribution_id is None and fqdn in aliases:
            distribution_id = distribution["Id"]
    return distribution_id


def wait_for_invalidation(cloudfront, distribution_id, invalidation_id, max_attempts=20, poll_interval=5):
    completed = False
    attempt = 0
    while not completed and attempt < max_attempts:
        attempt = attempt + 1
        print(f"Checking invalidation status (attempt {attempt}/{max_attempts})...", flush=True)
        status_response = cloudfront.get_invalidation(
            DistributionId=distribution_id, Id=invalidation_id
        )
        status = status_response["Invalidation"]["Status"]
        print(f"  Status: {status}", flush=True)
        if status == "Completed":
            completed = True
        elif attempt < max_attempts:
            print(f"  Waiting {poll_interval}s before next check...", flush=True)
            time.sleep(poll_interval)
    if not completed:
        raise RuntimeError(f"Invalidation did not complete after {max_attempts} attempts")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fqdn", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--paths", required=True)
    args = parser.parse_args()

    paths = [p.strip() for p in args.paths.split(",")]
    cloudfront = boto3.client("cloudfront", region_name=args.region)

    distribution_id = find_distribution_id(cloudfront, args.fqdn)

    exit_code = 0
    if not distribution_id:
        print(f"Error: No CloudFront distribution found for {args.fqdn}", flush=True)
        exit_code = 1
    else:
        try:
            invalidation_response = cloudfront.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": str(uuid.uuid4()),
                },
            )
            invalidation_id = invalidation_response["Invalidation"]["Id"]
            print(f"Invalidation created: {invalidation_id}", flush=True)
            wait_for_invalidation(cloudfront, distribution_id, invalidation_id)
        except RuntimeError as e:
            print(f"Error: {e}", flush=True)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
