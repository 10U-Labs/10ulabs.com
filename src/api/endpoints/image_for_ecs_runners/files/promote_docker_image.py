#!/usr/bin/env python3
import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def remove_tag_from_image(ecr_client, repository_name, tag_to_remove):
    try:
        response = ecr_client.describe_images(
            repositoryName=repository_name,
            imageIds=[{"imageTag": tag_to_remove}]
        )
        if response.get("imageDetails"):
            ecr_client.batch_delete_image(
                repositoryName=repository_name,
                imageIds=[{"imageTag": tag_to_remove}]
            )
            print(f"Removed tag '{tag_to_remove}' from previous image")
            return 0
        print(f"No image found with tag '{tag_to_remove}'")
        return 0
    except ClientError as e:
        if e.response['Error']['Code'] == 'ImageNotFoundException':
            print(f"No image found with tag '{tag_to_remove}'")
            return 0
        print(f"Error removing tag '{tag_to_remove}': {e}")
        return 1


def get_image_manifest(ecr_client, repository_name, source_tag):
    try:
        response = ecr_client.describe_images(
            repositoryName=repository_name,
            imageIds=[{"imageTag": source_tag}]
        )
        image_details = response.get("imageDetails", [])
        if not image_details:
            print(f"Error: No image found with tag '{source_tag}'")
            return None

        image_digest = image_details[0]["imageDigest"]
        manifest_response = ecr_client.batch_get_image(
            repositoryName=repository_name,
            imageIds=[{"imageDigest": image_digest}]
        )
        images = manifest_response.get("images", [])
        if not images:
            print(f"Error: Could not retrieve manifest for tag '{source_tag}'")
            return None

        return images[0]["imageManifest"]
    except ClientError as e:
        print(f"Error getting manifest for tag '{source_tag}': {e}")
        return None


def add_tag_to_image(ecr_client, repository_name, manifest, new_tag):
    try:
        ecr_client.put_image(
            repositoryName=repository_name,
            imageTag=new_tag,
            imageManifest=manifest
        )
        print(f"Added tag '{new_tag}' to image")
        return 0
    except ClientError as e:
        print(f"Error adding tag '{new_tag}': {e}")
        return 1


def promote_image(repository_name: str, image_tag: str, region: str) -> int:
    ecr_client = boto3.client("ecr", region_name=region)

    exit_code = 0

    print("=" * 80)
    print("DOCKER IMAGE PROMOTION")
    print("=" * 80)
    print(f"Repository: {repository_name}")
    print(f"Image Tag: {image_tag}")
    print(f"Region: {region}")
    print()

    print("Step 1: Remove 'latest' tag from previous image (if exists)")
    result = remove_tag_from_image(ecr_client, repository_name, "latest")
    if result != 0:
        exit_code = result
        return exit_code
    print()

    print(f"Step 2: Get manifest of image '{image_tag}'")
    manifest = get_image_manifest(ecr_client, repository_name, image_tag)
    if not manifest:
        exit_code = 1
        return exit_code
    print("Manifest retrieved successfully")
    print()

    print("Step 3: Add 'latest' tag to image")
    result = add_tag_to_image(ecr_client, repository_name, manifest, "latest")
    if result != 0:
        exit_code = result
        return exit_code
    print()

    print("Step 4: Add 'stable' tag to image")
    result = add_tag_to_image(ecr_client, repository_name, manifest, "stable")
    if result != 0:
        exit_code = result
        return exit_code
    print()

    print("Step 5: Remove 'available' tag from image")
    result = remove_tag_from_image(ecr_client, repository_name, "available")
    if result != 0:
        exit_code = result
        return exit_code
    print()

    print("=" * 80)
    print("PROMOTION COMPLETE")
    print("=" * 80)
    print(f"Image promoted: {image_tag} (available) → latest + stable")
    print()

    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Promote Docker image to latest and stable"
    )
    parser.add_argument("--repository", required=True, help="ECR repository name")
    parser.add_argument("--image-tag", required=True, help="Image tag to promote (e.g., build number)")
    parser.add_argument("--region", required=True, help="AWS region")
    args = parser.parse_args()

    result = promote_image(args.repository, args.image_tag, args.region)
    sys.exit(result)


if __name__ == "__main__":
    main()
