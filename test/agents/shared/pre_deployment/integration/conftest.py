"""Pytest fixtures for agents/shared pre-deployment integration tests.

All shared fixtures (aws_region, ssm_client, s3_client, etc.) are inherited
from test/conftest.py which parses values from the shared Terraform module.
"""
