"""Pytest configuration for AMI validation tests"""
import pytest


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--ami-id",
        action="store",
        required=True,
        help="AMI ID to validate"
    )
    parser.addoption(
        "--instance-type",
        action="store",
        default="t4g.micro",
        help="Instance type to use for testing (default: t4g.micro)"
    )
    parser.addoption(
        "--subnet-id",
        action="store",
        required=True,
        help="Subnet ID to launch test instance in"
    )
    parser.addoption(
        "--region",
        action="store",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    parser.addoption(
        "--instance-id",
        action="store",
        required=True,
        help="EC2 instance ID to test"
    )
    # Note: --connection is provided by testinfra, don't redefine it


@pytest.fixture
def ami_id(request):
    """AMI ID being tested"""
    return request.config.getoption("--ami-id")


@pytest.fixture
def instance_id(request):
    """EC2 instance ID for testing"""
    return request.config.getoption("--instance-id")


@pytest.fixture
def instance_type(request):
    """EC2 instance type"""
    return request.config.getoption("--instance-type")


@pytest.fixture
def subnet_id(request):
    """Subnet ID where instance is launched"""
    return request.config.getoption("--subnet-id")


@pytest.fixture
def region(request):
    """AWS region"""
    return request.config.getoption("--region")
