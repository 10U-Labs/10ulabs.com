"""Pytest fixtures for api/common/docker_repository post-deployment integration tests.

These tests follow the 3-layer testing model from POST_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Existence - Resources were created
- Layer 2: Configuration - Resources configured correctly
- Layer 3: Wiring - Components connected properly

Layer marker system and shared fixtures provided by parent conftest.py.
"""
