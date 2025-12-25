"""Post-deployment integration tests: AgentCore Memory.

Verifies the AgentCore Memory and OpenSearch Serverless collection are deployed.

Five-layer testing model:
- Layer 3: Existence - Does the OpenSearch collection exist?
- Layer 4: Configuration - Is it configured for vector search?
"""

import pytest
from botocore.exceptions import ClientError


def _find_policy_for_collection(policies, collection_name):
    """Check if any policy matches the given collection name."""
    for policy in policies:
        if collection_name.replace("-", "") in policy["name"].replace("-", ""):
            return True
    return False


class TestOpenSearchCollectionExistence:
    """Layer 3: Verify the OpenSearch Serverless collection exists."""

    def test_01_opensearch_collection_exists(
        self, opensearch_client, memory_collection_name
    ):
        """Verify the OpenSearch Serverless collection exists."""
        try:
            response = opensearch_client.list_collections(
                collectionFilters={"name": memory_collection_name}
            )
            collections = response.get("collectionSummaries", [])
            names = [c["name"] for c in collections]
            assert memory_collection_name in names, (
                f"OpenSearch collection '{memory_collection_name}' not found. "
                "Run terraform apply to create it."
            )
        except ClientError as err:
            pytest.fail(f"Failed to list OpenSearch collections: {err}")


class TestOpenSearchCollectionConfiguration:
    """Layer 4: Verify the OpenSearch collection is configured correctly."""

    def test_01_collection_is_vector_search_type(
        self, opensearch_client, memory_collection_name
    ):
        """Verify the collection is configured for vector search."""
        try:
            response = opensearch_client.list_collections(
                collectionFilters={"name": memory_collection_name}
            )
            collections = response.get("collectionSummaries", [])
            for c in collections:
                if c["name"] == memory_collection_name:
                    collection_type = c.get("type", "")
                    assert collection_type == "VECTORSEARCH", (
                        f"OpenSearch collection '{memory_collection_name}' should be "
                        f"type VECTORSEARCH, got: {collection_type}"
                    )
                    return
            pytest.skip(f"Collection '{memory_collection_name}' not found")
        except ClientError as err:
            pytest.fail(f"Failed to get collection: {err}")

    def test_02_collection_has_encryption_policy(
        self, opensearch_client, memory_collection_name
    ):
        """Verify the collection has encryption policy."""
        try:
            response = opensearch_client.list_security_policies(
                type="encryption"
            )
            policies = response.get("securityPolicySummaries", [])
            assert _find_policy_for_collection(policies, memory_collection_name), (
                f"No encryption policy found for collection '{memory_collection_name}'."
            )
        except ClientError as err:
            pytest.fail(f"Failed to list security policies: {err}")

    def test_03_collection_has_network_policy(
        self, opensearch_client, memory_collection_name
    ):
        """Verify the collection has network policy."""
        try:
            response = opensearch_client.list_security_policies(
                type="network"
            )
            policies = response.get("securityPolicySummaries", [])
            assert _find_policy_for_collection(policies, memory_collection_name), (
                f"No network policy found for collection '{memory_collection_name}'."
            )
        except ClientError as err:
            pytest.fail(f"Failed to list security policies: {err}")

    def test_04_collection_has_access_policy(
        self, opensearch_client, memory_collection_name
    ):
        """Verify the collection has access policy."""
        try:
            response = opensearch_client.list_access_policies(
                type="data"
            )
            policies = response.get("accessPolicySummaries", [])
            assert _find_policy_for_collection(policies, memory_collection_name), (
                f"No access policy found for collection '{memory_collection_name}'."
            )
        except ClientError as err:
            pytest.fail(f"Failed to list access policies: {err}")
