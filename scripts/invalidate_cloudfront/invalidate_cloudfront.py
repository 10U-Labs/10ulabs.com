import argparse
import sys
import time
import uuid
import boto3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fqdn", required=True)
    parser.add_argument("--region", required=True)
    args = parser.parse_args()

    domain_subdomain = args.fqdn
    aws_region = args.region

    cloudfront = boto3.client("cloudfront", region_name=aws_region)

    response = cloudfront.list_distributions()
    distribution_id = None

    for distribution in response.get("DistributionList", {}).get("Items", []):
        if domain_subdomain in distribution.get("Aliases", {}).get("Items", []):
            distribution_id = distribution["Id"]
            break

    if not distribution_id:
        print(f"Error: No CloudFront distribution found for {domain_subdomain}")
        sys.exit(1)

    paths = ["/", "/index.html", "/openapi.yml", "/404.html"]
    caller_reference = str(uuid.uuid4())

    print(f"Creating invalidation for distribution {distribution_id}")
    print(f"Paths: {', '.join(paths)}")

    invalidation_response = cloudfront.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            "Paths": {"Quantity": len(paths), "Items": paths},
            "CallerReference": caller_reference,
        },
    )

    invalidation_id = invalidation_response["Invalidation"]["Id"]
    print(f"Invalidation created: {invalidation_id}")
    print("Waiting for invalidation to complete...")

    while True:
        status_response = cloudfront.get_invalidation(
            DistributionId=distribution_id, Id=invalidation_id
        )
        status = status_response["Invalidation"]["Status"]
        print(f"Status: {status}")

        if status == "Completed":
            print("Invalidation completed successfully")
            return 0

        time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())
