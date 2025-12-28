"""Comprehensive tests for infra_validation module."""
import os
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

import infra_validation
from infra_validation import (
    reset_api_key_cache,
    get_api_key,
    validate_security_groups,
    validate_subnets,
    validate_vpc,
    validate_all_dependencies,
    ensure_dependencies_valid,
    reset_dependency_validation,
    get_dependencies_status,
    set_dependencies_status,
)


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset all caches before and after each test."""
    reset_api_key_cache()
    reset_dependency_validation()
    yield
    reset_api_key_cache()
    reset_dependency_validation()


# === API Key Functions ===


class TestResetApiKeyCache:
    """Tests for reset_api_key_cache function."""

    def test_reset_clears_cache(self):
        """reset_api_key_cache clears the cached value."""
        infra_validation._api_key_cache["value"] = "test-key"
        reset_api_key_cache()
        assert infra_validation._api_key_cache["value"] == ""


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_get_api_key_returns_cached(self):
        """get_api_key returns cached value if present."""
        infra_validation._api_key_cache["value"] = "cached-key"
        result = get_api_key()
        assert result == "cached-key"

    def test_get_api_key_no_parameter_name(self):
        """get_api_key returns empty string if parameter name not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_api_key()
            assert result == ""

    @patch("infra_validation.get_ssm_client")
    def test_get_api_key_from_ssm_returns_key(self, mock_get_ssm):
        """get_api_key returns the key retrieved from SSM."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "ssm-key"}}
        mock_get_ssm.return_value = mock_ssm

        with patch.dict(os.environ, {"API_KEY_PARAMETER_NAME": "/my/param"}):
            result = get_api_key()
            assert result == "ssm-key"

    @patch("infra_validation.get_ssm_client")
    def test_get_api_key_from_ssm_caches_key(self, mock_get_ssm):
        """get_api_key caches the key retrieved from SSM."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "ssm-key"}}
        mock_get_ssm.return_value = mock_ssm

        with patch.dict(os.environ, {"API_KEY_PARAMETER_NAME": "/my/param"}):
            get_api_key()
            assert infra_validation._api_key_cache["value"] == "ssm-key"

    @patch("infra_validation.get_ssm_client")
    def test_get_api_key_from_ssm_calls_with_decryption(self, mock_get_ssm):
        """get_api_key calls SSM with WithDecryption=True."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "ssm-key"}}
        mock_get_ssm.return_value = mock_ssm

        with patch.dict(os.environ, {"API_KEY_PARAMETER_NAME": "/my/param"}):
            get_api_key()
            mock_ssm.get_parameter.assert_called_once_with(
                Name="/my/param", WithDecryption=True
            )


# === Validate Security Groups ===


class TestValidateSecurityGroups:
    """Tests for validate_security_groups function."""

    def test_validate_empty_list(self):
        """validate_security_groups returns valid for empty list."""
        result = validate_security_groups([])
        assert result == {"valid": True, "missing": []}

    @patch("infra_validation.get_ec2_client")
    def test_validate_all_exist(self, mock_get_ec2):
        """validate_security_groups returns valid when all exist."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [{"GroupId": "sg-123"}, {"GroupId": "sg-456"}]
        }
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123", "sg-456"])
        assert result == {"valid": True, "missing": []}

    @patch("infra_validation.get_ec2_client")
    def test_validate_some_missing_returns_invalid(self, mock_get_ec2):
        """validate_security_groups returns invalid when some groups missing."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [{"GroupId": "sg-123"}]
        }
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123", "sg-456"])
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_some_missing_lists_missing_group(self, mock_get_ec2):
        """validate_security_groups lists the missing group in result."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [{"GroupId": "sg-123"}]
        }
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123", "sg-456"])
        assert "sg-456" in result["missing"]

    @patch("infra_validation.get_ec2_client")
    def test_validate_not_found_error_returns_invalid(self, mock_get_ec2):
        """validate_security_groups returns invalid on InvalidGroup.NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {"Error": {"Code": "InvalidGroup.NotFound", "Message": "Not found"}},
            "DescribeSecurityGroups",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123"])
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_not_found_error_lists_all_as_missing(self, mock_get_ec2):
        """validate_security_groups lists all groups as missing on NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {"Error": {"Code": "InvalidGroup.NotFound", "Message": "Not found"}},
            "DescribeSecurityGroups",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123"])
        assert result["missing"] == ["sg-123"]

    @patch("infra_validation.get_ec2_client")
    def test_validate_not_found_error_includes_error(self, mock_get_ec2):
        """validate_security_groups includes error on InvalidGroup.NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {"Error": {"Code": "InvalidGroup.NotFound", "Message": "Not found"}},
            "DescribeSecurityGroups",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123"])
        assert "error" in result

    @patch("infra_validation.get_ec2_client")
    def test_validate_other_error_returns_invalid(self, mock_get_ec2):
        """validate_security_groups returns invalid on other ClientErrors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeSecurityGroups",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123"])
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_other_error_missing_is_empty(self, mock_get_ec2):
        """validate_security_groups has empty missing list on other errors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeSecurityGroups",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123"])
        assert result["missing"] == []

    @patch("infra_validation.get_ec2_client")
    def test_validate_other_error_includes_error(self, mock_get_ec2):
        """validate_security_groups includes error on other ClientErrors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeSecurityGroups",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_security_groups(["sg-123"])
        assert "error" in result


# === Validate Subnets ===


class TestValidateSubnets:
    """Tests for validate_subnets function."""

    def test_validate_empty_list(self):
        """validate_subnets returns valid for empty list."""
        result = validate_subnets([])
        assert result == {"valid": True, "missing": []}

    @patch("infra_validation.get_ec2_client")
    def test_validate_all_exist(self, mock_get_ec2):
        """validate_subnets returns valid when all exist."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-1"}, {"SubnetId": "subnet-2"}]
        }
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1", "subnet-2"])
        assert result == {"valid": True, "missing": []}

    @patch("infra_validation.get_ec2_client")
    def test_validate_some_missing_returns_invalid(self, mock_get_ec2):
        """validate_subnets returns invalid when some subnets missing."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {"Subnets": [{"SubnetId": "subnet-1"}]}
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1", "subnet-2"])
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_some_missing_lists_missing_subnet(self, mock_get_ec2):
        """validate_subnets lists the missing subnet in result."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {"Subnets": [{"SubnetId": "subnet-1"}]}
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1", "subnet-2"])
        assert "subnet-2" in result["missing"]

    @patch("infra_validation.get_ec2_client")
    def test_validate_not_found_error_returns_invalid(self, mock_get_ec2):
        """validate_subnets returns invalid on InvalidSubnetID.NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {"Error": {"Code": "InvalidSubnetID.NotFound", "Message": "Not found"}},
            "DescribeSubnets",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1"])
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_not_found_error_lists_all_as_missing(self, mock_get_ec2):
        """validate_subnets lists all subnets as missing on NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {"Error": {"Code": "InvalidSubnetID.NotFound", "Message": "Not found"}},
            "DescribeSubnets",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1"])
        assert result["missing"] == ["subnet-1"]

    @patch("infra_validation.get_ec2_client")
    def test_validate_not_found_error_includes_error(self, mock_get_ec2):
        """validate_subnets includes error on InvalidSubnetID.NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {"Error": {"Code": "InvalidSubnetID.NotFound", "Message": "Not found"}},
            "DescribeSubnets",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1"])
        assert "error" in result

    @patch("infra_validation.get_ec2_client")
    def test_validate_other_error_returns_invalid(self, mock_get_ec2):
        """validate_subnets returns invalid on other ClientErrors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeSubnets",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1"])
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_other_error_missing_is_empty(self, mock_get_ec2):
        """validate_subnets has empty missing list on other errors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeSubnets",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1"])
        assert result["missing"] == []

    @patch("infra_validation.get_ec2_client")
    def test_validate_other_error_includes_error(self, mock_get_ec2):
        """validate_subnets includes error on other ClientErrors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeSubnets",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_subnets(["subnet-1"])
        assert "error" in result


# === Validate VPC ===


class TestValidateVpc:
    """Tests for validate_vpc function."""

    def test_validate_no_vpc_id_returns_invalid(self):
        """validate_vpc returns invalid when VPC ID is None."""
        result = validate_vpc(None)
        assert result["valid"] is False

    def test_validate_no_vpc_id_error_message(self):
        """validate_vpc returns not configured error when VPC ID is None."""
        result = validate_vpc(None)
        assert "not configured" in result["error"]

    def test_validate_empty_vpc_id_returns_invalid(self):
        """validate_vpc returns invalid when VPC ID is empty."""
        result = validate_vpc("")
        assert result["valid"] is False

    def test_validate_empty_vpc_id_error_message(self):
        """validate_vpc returns not configured error when VPC ID is empty."""
        result = validate_vpc("")
        assert "not configured" in result["error"]

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_exists_returns_valid(self, mock_get_ec2):
        """validate_vpc returns valid when VPC exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {"Vpcs": [{"VpcId": "vpc-123"}]}
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert result["valid"] is True

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_exists_error_is_none(self, mock_get_ec2):
        """validate_vpc returns error as None when VPC exists."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {"Vpcs": [{"VpcId": "vpc-123"}]}
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert result["error"] is None

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_not_found_returns_invalid(self, mock_get_ec2):
        """validate_vpc returns invalid when VPC not found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {"Vpcs": []}
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_not_found_error_message(self, mock_get_ec2):
        """validate_vpc returns not found error when VPC not found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {"Vpcs": []}
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert "not found" in result["error"]

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_not_found_error_returns_invalid(self, mock_get_ec2):
        """validate_vpc returns invalid on InvalidVpcID.NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {"Error": {"Code": "InvalidVpcID.NotFound", "Message": "Not found"}},
            "DescribeVpcs",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_not_found_error_error_message(self, mock_get_ec2):
        """validate_vpc returns not found error on InvalidVpcID.NotFound."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {"Error": {"Code": "InvalidVpcID.NotFound", "Message": "Not found"}},
            "DescribeVpcs",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert "not found" in result["error"]

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_other_error_returns_invalid(self, mock_get_ec2):
        """validate_vpc returns invalid on other ClientErrors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeVpcs",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert result["valid"] is False

    @patch("infra_validation.get_ec2_client")
    def test_validate_vpc_other_error_includes_message(self, mock_get_ec2):
        """validate_vpc includes error message on other ClientErrors."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeVpcs",
        )
        mock_get_ec2.return_value = mock_ec2

        result = validate_vpc("vpc-123")
        assert "Access denied" in result["error"]


# === Validate All Dependencies ===


class TestValidateAllDependencies:
    """Tests for validate_all_dependencies function."""

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_all_valid_returns_valid(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies returns valid when all pass."""
        mock_sg.return_value = {"valid": True, "missing": []}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": True, "error": None}

        with patch.dict(
            os.environ,
            {
                "SECURITY_GROUPS": "sg-1,sg-2",
                "SUBNETS": "subnet-1,subnet-2",
                "VPC_ID": "vpc-123",
            },
        ):
            result = validate_all_dependencies()

        assert result["valid"] is True

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_all_valid_errors_empty(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies returns empty errors when all pass."""
        mock_sg.return_value = {"valid": True, "missing": []}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": True, "error": None}

        with patch.dict(
            os.environ,
            {
                "SECURITY_GROUPS": "sg-1,sg-2",
                "SUBNETS": "subnet-1,subnet-2",
                "VPC_ID": "vpc-123",
            },
        ):
            result = validate_all_dependencies()

        assert result["errors"] == []

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_security_group_invalid_returns_invalid(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies returns invalid when security group fails."""
        mock_sg.return_value = {"valid": False, "missing": ["sg-1"]}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": True, "error": None}

        with patch.dict(
            os.environ,
            {"SECURITY_GROUPS": "sg-1", "SUBNETS": "", "VPC_ID": "vpc-123"},
        ):
            result = validate_all_dependencies()

        assert result["valid"] is False

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_security_group_invalid_has_one_error(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies reports one error for security group failure."""
        mock_sg.return_value = {"valid": False, "missing": ["sg-1"]}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": True, "error": None}

        with patch.dict(
            os.environ,
            {"SECURITY_GROUPS": "sg-1", "SUBNETS": "", "VPC_ID": "vpc-123"},
        ):
            result = validate_all_dependencies()

        assert len(result["errors"]) == 1

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_security_group_invalid_error_type(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies reports security_group error type."""
        mock_sg.return_value = {"valid": False, "missing": ["sg-1"]}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": True, "error": None}

        with patch.dict(
            os.environ,
            {"SECURITY_GROUPS": "sg-1", "SUBNETS": "", "VPC_ID": "vpc-123"},
        ):
            result = validate_all_dependencies()

        assert result["errors"][0]["type"] == "security_group"

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_empty_env_vars_returns_invalid(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies returns invalid with empty env vars."""
        mock_sg.return_value = {"valid": True, "missing": []}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": False, "error": "not configured"}

        with patch.dict(os.environ, {}, clear=True):
            result = validate_all_dependencies()

        assert result["valid"] is False

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_empty_env_vars_calls_sg_with_empty_list(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies calls validate_security_groups with empty list."""
        mock_sg.return_value = {"valid": True, "missing": []}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": False, "error": "not configured"}

        with patch.dict(os.environ, {}, clear=True):
            validate_all_dependencies()

        mock_sg.assert_called_with([])

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_empty_env_vars_calls_subnet_with_empty_list(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies calls validate_subnets with empty list."""
        mock_sg.return_value = {"valid": True, "missing": []}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": False, "error": "not configured"}

        with patch.dict(os.environ, {}, clear=True):
            validate_all_dependencies()

        mock_subnet.assert_called_with([])

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_whitespace_handling_strips_security_groups(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies strips whitespace from security groups."""
        mock_sg.return_value = {"valid": True, "missing": []}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": True, "error": None}

        with patch.dict(
            os.environ,
            {
                "SECURITY_GROUPS": " sg-1 , sg-2 ",
                "SUBNETS": " subnet-1 , , subnet-2 ",
                "VPC_ID": "vpc-123",
            },
        ):
            validate_all_dependencies()

        mock_sg.assert_called_with(["sg-1", "sg-2"])

    @patch("infra_validation.validate_vpc")
    @patch("infra_validation.validate_subnets")
    @patch("infra_validation.validate_security_groups")
    def test_whitespace_handling_strips_subnets(self, mock_sg, mock_subnet, mock_vpc):
        """validate_all_dependencies strips whitespace and empties from subnets."""
        mock_sg.return_value = {"valid": True, "missing": []}
        mock_subnet.return_value = {"valid": True, "missing": []}
        mock_vpc.return_value = {"valid": True, "error": None}

        with patch.dict(
            os.environ,
            {
                "SECURITY_GROUPS": " sg-1 , sg-2 ",
                "SUBNETS": " subnet-1 , , subnet-2 ",
                "VPC_ID": "vpc-123",
            },
        ):
            validate_all_dependencies()

        mock_subnet.assert_called_with(["subnet-1", "subnet-2"])


# === Ensure Dependencies Valid ===


class TestEnsureDependenciesValid:
    """Tests for ensure_dependencies_valid function."""

    def test_uses_cached_valid_result(self):
        """ensure_dependencies_valid uses cached valid result."""
        set_dependencies_status(checked=True, valid=True, errors=[])
        # Should not raise
        ensure_dependencies_valid()

    def test_uses_cached_invalid_result(self):
        """ensure_dependencies_valid raises on cached invalid result."""
        set_dependencies_status(checked=True, valid=False, errors=["error1"])
        with pytest.raises(RuntimeError, match="invalid"):
            ensure_dependencies_valid()

    @patch("infra_validation.validate_all_dependencies")
    def test_validates_and_caches_checked(self, mock_validate):
        """ensure_dependencies_valid sets checked to True after validation."""
        mock_validate.return_value = {
            "valid": True,
            "errors": [],
            "checked_resources": {},
        }
        ensure_dependencies_valid()
        status = get_dependencies_status()
        assert status["checked"] is True

    @patch("infra_validation.validate_all_dependencies")
    def test_validates_and_caches_valid(self, mock_validate):
        """ensure_dependencies_valid sets valid to True when dependencies valid."""
        mock_validate.return_value = {
            "valid": True,
            "errors": [],
            "checked_resources": {},
        }
        ensure_dependencies_valid()
        status = get_dependencies_status()
        assert status["valid"] is True

    @patch("infra_validation.validate_all_dependencies")
    def test_raises_on_invalid(self, mock_validate):
        """ensure_dependencies_valid raises RuntimeError when invalid."""
        mock_validate.return_value = {
            "valid": False,
            "errors": [{"type": "vpc", "details": {}}],
            "checked_resources": {},
        }
        with pytest.raises(RuntimeError, match="invalid"):
            ensure_dependencies_valid()


# === Dependency Status Functions ===


class TestResetDependencyValidation:
    """Tests for reset_dependency_validation function."""

    def test_reset_clears_checked(self):
        """reset_dependency_validation clears checked to False."""
        set_dependencies_status(checked=True, valid=True, errors=["error"])
        reset_dependency_validation()
        status = get_dependencies_status()
        assert status["checked"] is False

    def test_reset_clears_valid(self):
        """reset_dependency_validation clears valid to False."""
        set_dependencies_status(checked=True, valid=True, errors=["error"])
        reset_dependency_validation()
        status = get_dependencies_status()
        assert status["valid"] is False

    def test_reset_clears_errors(self):
        """reset_dependency_validation clears errors to empty list."""
        set_dependencies_status(checked=True, valid=True, errors=["error"])
        reset_dependency_validation()
        status = get_dependencies_status()
        assert status["errors"] == []


class TestGetDependenciesStatus:
    """Tests for get_dependencies_status function."""

    def test_returns_current_status(self):
        """get_dependencies_status returns current status."""
        set_dependencies_status(checked=True, valid=False, errors=["e1", "e2"])
        status = get_dependencies_status()
        assert status == {"checked": True, "valid": False, "errors": ["e1", "e2"]}

    def test_returns_copy_of_errors(self):
        """get_dependencies_status returns a copy of errors list."""
        original_errors = ["e1"]
        set_dependencies_status(checked=True, valid=False, errors=original_errors)
        status = get_dependencies_status()
        status["errors"].append("e2")
        # Original should be unchanged
        assert get_dependencies_status()["errors"] == ["e1"]


class TestSetDependenciesStatus:
    """Tests for set_dependencies_status function."""

    def test_sets_checked_field(self):
        """set_dependencies_status sets checked field."""
        set_dependencies_status(checked=True, valid=True, errors=["error"])
        assert infra_validation._dependencies_validated["checked"] is True

    def test_sets_valid_field(self):
        """set_dependencies_status sets valid field."""
        set_dependencies_status(checked=True, valid=True, errors=["error"])
        assert infra_validation._dependencies_validated["valid"] is True

    def test_sets_errors_field(self):
        """set_dependencies_status sets errors field."""
        set_dependencies_status(checked=True, valid=True, errors=["error"])
        assert infra_validation._dependencies_validated["errors"] == ["error"]
