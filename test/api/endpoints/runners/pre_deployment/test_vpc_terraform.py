def test_vpc_terraform_file_exists(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    assert vpc_file.exists()


def test_vpc_resource_exists(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_vpc" "runner_vpc"' in content


def test_vpc_uses_cidr_variable(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'var.vpc_cidr' in content


def test_vpc_has_dns_support_enabled(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'enable_dns_support' in content


def test_vpc_has_dns_hostnames_enabled(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'enable_dns_hostnames' in content


def test_public_subnet_resource_exists(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_subnet" "public"' in content


def test_internet_gateway_resource_exists(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_internet_gateway" "main"' in content


def test_route_table_resource_exists(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route_table" "public"' in content


def test_route_table_association_exists(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route_table_association" "public"' in content


def test_security_group_exists(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_security_group" "runner_sg"' in content


def test_availability_zones_data_source_exists(runners_src_path):
    data_file = runners_src_path / "data.tf"
    with open(data_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "aws_availability_zones" "available"' in content


def test_security_group_allows_egress(runners_src_path):
    vpc_file = runners_src_path / "vpc.tf"
    with open(vpc_file, encoding="utf-8") as f:
        content = f.read()
    assert 'egress' in content
