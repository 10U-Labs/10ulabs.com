"""Comprehensive tests for ec2_fleet module."""
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from ec2_fleet import (
    FleetError,
    CapacityError,
    LaunchOptions,
    get_subnet_az,
    get_subnet_azs,
    filter_subnets_by_az,
    create_launch_template,
    delete_launch_template,
    create_fleet_instance,
    _build_fleet_overrides,
    _extract_instance_id,
    get_instance_state,
    get_instance_az,
    wait_for_instance_running,
    wait_for_status_checks,
    terminate_instance,
    launch_instance,
    _handle_launch_failure,
    _attempt_launch,
    launch_instance_with_retry,
)


# === Exception Classes ===


class TestFleetError:
    """Tests for FleetError exception class."""

    def test_fleet_error_is_exception(self):
        """FleetError should be a subclass of Exception."""
        assert issubclass(FleetError, Exception)

    def test_fleet_error_can_be_raised(self):
        """FleetError can be raised with a message."""
        with pytest.raises(FleetError, match="test message"):
            raise FleetError("test message")


class TestCapacityError:
    """Tests for CapacityError exception class."""

    def test_capacity_error_is_exception(self):
        """CapacityError should be a subclass of Exception."""
        assert issubclass(CapacityError, Exception)

    def test_capacity_error_can_be_raised(self):
        """CapacityError can be raised with a message."""
        with pytest.raises(CapacityError, match="no capacity"):
            raise CapacityError("no capacity")


# === LaunchOptions Dataclass ===


class TestLaunchOptions:
    """Tests for LaunchOptions dataclass."""

    def test_launch_options_sets_instance_types(self):
        """LaunchOptions sets instance_types correctly."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-123"],
        )
        assert opts.instance_types == ["m5.large"]

    def test_launch_options_sets_subnet_ids(self):
        """LaunchOptions sets subnet_ids correctly."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-123"],
        )
        assert opts.subnet_ids == ["subnet-123"]

    def test_launch_options_default_allocation_strategy(self):
        """LaunchOptions defaults allocation_strategy to lowest-price."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-123"],
        )
        assert opts.allocation_strategy == "lowest-price"

    def test_launch_options_default_max_retries(self):
        """LaunchOptions defaults max_retries to 2."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-123"],
        )
        assert opts.max_retries == 2

    def test_launch_options_default_wait_for_ready(self):
        """LaunchOptions defaults wait_for_ready to True."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-123"],
        )
        assert opts.wait_for_ready is True

    def test_launch_options_default_excluded_azs(self):
        """LaunchOptions defaults excluded_azs to empty list."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-123"],
        )
        assert opts.excluded_azs == []

    def test_launch_options_default_use_spot(self):
        """LaunchOptions defaults use_spot to True."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-123"],
        )
        assert opts.use_spot is True

    def test_launch_options_custom_allocation_strategy(self):
        """LaunchOptions accepts custom allocation_strategy."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
            allocation_strategy="diversified",
            max_retries=5,
            wait_for_ready=False,
            excluded_azs=["us-east-2a"],
            use_spot=False,
        )
        assert opts.allocation_strategy == "diversified"

    def test_launch_options_custom_max_retries(self):
        """LaunchOptions accepts custom max_retries."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
            allocation_strategy="diversified",
            max_retries=5,
            wait_for_ready=False,
            excluded_azs=["us-east-2a"],
            use_spot=False,
        )
        assert opts.max_retries == 5

    def test_launch_options_custom_wait_for_ready(self):
        """LaunchOptions accepts custom wait_for_ready."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
            allocation_strategy="diversified",
            max_retries=5,
            wait_for_ready=False,
            excluded_azs=["us-east-2a"],
            use_spot=False,
        )
        assert opts.wait_for_ready is False

    def test_launch_options_custom_excluded_azs(self):
        """LaunchOptions accepts custom excluded_azs."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
            allocation_strategy="diversified",
            max_retries=5,
            wait_for_ready=False,
            excluded_azs=["us-east-2a"],
            use_spot=False,
        )
        assert opts.excluded_azs == ["us-east-2a"]

    def test_launch_options_custom_use_spot(self):
        """LaunchOptions accepts custom use_spot."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
            allocation_strategy="diversified",
            max_retries=5,
            wait_for_ready=False,
            excluded_azs=["us-east-2a"],
            use_spot=False,
        )
        assert opts.use_spot is False


# === Subnet Functions ===


class TestGetSubnetAz:
    """Tests for get_subnet_az function."""

    def test_get_subnet_az_returns_az(self):
        """get_subnet_az returns the availability zone of a subnet."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-123", "AvailabilityZone": "us-east-2a"}]
        }
        result = get_subnet_az(mock_client, "subnet-123")
        assert result == "us-east-2a"

    def test_get_subnet_az_calls_describe_subnets_correctly(self):
        """get_subnet_az calls describe_subnets with correct subnet ID."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-123", "AvailabilityZone": "us-east-2a"}]
        }
        get_subnet_az(mock_client, "subnet-123")
        mock_client.describe_subnets.assert_called_once_with(SubnetIds=["subnet-123"])


class TestGetSubnetAzs:
    """Tests for get_subnet_azs function."""

    def test_get_subnet_azs_returns_mapping(self):
        """get_subnet_azs returns a mapping of subnet IDs to AZs."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [
                {"SubnetId": "subnet-1", "AvailabilityZone": "us-east-2a"},
                {"SubnetId": "subnet-2", "AvailabilityZone": "us-east-2b"},
            ]
        }
        result = get_subnet_azs(mock_client, ["subnet-1", "subnet-2"])
        assert result == {"subnet-1": "us-east-2a", "subnet-2": "us-east-2b"}

    def test_get_subnet_azs_empty_list_returns_empty_dict(self):
        """get_subnet_azs returns empty dict for empty input."""
        mock_client = MagicMock()
        result = get_subnet_azs(mock_client, [])
        assert result == {}

    def test_get_subnet_azs_empty_list_does_not_call_api(self):
        """get_subnet_azs does not call describe_subnets for empty input."""
        mock_client = MagicMock()
        get_subnet_azs(mock_client, [])
        mock_client.describe_subnets.assert_not_called()


class TestFilterSubnetsByAz:
    """Tests for filter_subnets_by_az function."""

    def test_filter_subnets_no_exclusions(self):
        """filter_subnets_by_az returns all subnets when no exclusions."""
        mock_client = MagicMock()
        result = filter_subnets_by_az(mock_client, ["subnet-1", "subnet-2"], [])
        assert result == ["subnet-1", "subnet-2"]

    def test_filter_subnets_with_exclusions(self):
        """filter_subnets_by_az filters out excluded AZs."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [
                {"SubnetId": "subnet-1", "AvailabilityZone": "us-east-2a"},
                {"SubnetId": "subnet-2", "AvailabilityZone": "us-east-2b"},
            ]
        }
        result = filter_subnets_by_az(
            mock_client, ["subnet-1", "subnet-2"], ["us-east-2a"]
        )
        assert result == ["subnet-2"]


# === Launch Template Functions ===


class TestCreateLaunchTemplate:
    """Tests for create_launch_template function."""

    def test_create_launch_template_minimal(self):
        """create_launch_template with minimal config."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        result = create_launch_template(
            mock_client, "test-template", {"ami_id": "ami-123"}
        )
        assert result == "lt-123"

    def test_create_launch_template_full_config(self):
        """create_launch_template with all config options."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-456"}
        }
        config = {
            "ami_id": "ami-123",
            "security_group_id": "sg-123",
            "key_name": "my-key",
            "iam_instance_profile": "my-profile",
            "user_data": "IyEvYmluL2Jhc2g=",
            "block_device_mappings": [{"DeviceName": "/dev/xvda"}],
            "metadata_options": {"HttpTokens": "required"},
            "tag_specifications": [{"ResourceType": "instance", "Tags": []}],
            "template_tags": {"Name": "test", "Env": "dev"},
        }
        result = create_launch_template(mock_client, "test-template", config)
        assert result == "lt-456"


class TestDeleteLaunchTemplate:
    """Tests for delete_launch_template function."""

    def test_delete_launch_template_success(self):
        """delete_launch_template deletes template successfully."""
        mock_client = MagicMock()
        delete_launch_template(mock_client, "lt-123")
        mock_client.delete_launch_template.assert_called_once_with(
            LaunchTemplateId="lt-123"
        )

    def test_delete_launch_template_ignores_error(self):
        """delete_launch_template ignores ClientError."""
        mock_client = MagicMock()
        mock_client.delete_launch_template.side_effect = ClientError(
            {"Error": {"Code": "NotFound"}}, "DeleteLaunchTemplate"
        )
        # Should not raise
        delete_launch_template(mock_client, "lt-123")


# === Fleet Instance Functions ===


class TestBuildFleetOverrides:
    """Tests for _build_fleet_overrides function."""

    def test_build_fleet_overrides_single(self):
        """_build_fleet_overrides with single instance type and subnet."""
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
        )
        result = _build_fleet_overrides(opts)
        assert result == [{"InstanceType": "m5.large", "SubnetId": "subnet-1"}]

    def test_build_fleet_overrides_multiple_returns_correct_count(self):
        """_build_fleet_overrides returns correct number of overrides."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
        )
        result = _build_fleet_overrides(opts)
        assert len(result) == 4

    def test_build_fleet_overrides_multiple_contains_first_combination(self):
        """_build_fleet_overrides includes m5.large with subnet-1."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
        )
        result = _build_fleet_overrides(opts)
        assert {"InstanceType": "m5.large", "SubnetId": "subnet-1"} in result

    def test_build_fleet_overrides_multiple_contains_cross_combination(self):
        """_build_fleet_overrides includes m5.xlarge with subnet-2."""
        opts = LaunchOptions(
            instance_types=["m5.large", "m5.xlarge"],
            subnet_ids=["subnet-1", "subnet-2"],
        )
        result = _build_fleet_overrides(opts)
        assert {"InstanceType": "m5.xlarge", "SubnetId": "subnet-2"} in result


class TestExtractInstanceId:
    """Tests for _extract_instance_id function."""

    def test_extract_instance_id_success(self):
        """_extract_instance_id extracts ID from successful response."""
        response = {"Instances": [{"InstanceIds": ["i-123"]}]}
        result = _extract_instance_id(response)
        assert result == "i-123"

    def test_extract_instance_id_no_instances(self):
        """_extract_instance_id raises CapacityError when no instances."""
        response = {"Instances": []}
        with pytest.raises(CapacityError, match="No instances launched"):
            _extract_instance_id(response)

    def test_extract_instance_id_with_errors(self):
        """_extract_instance_id raises CapacityError with error messages."""
        response = {
            "Instances": [],
            "Errors": [{"ErrorMessage": "InsufficientCapacity"}],
        }
        with pytest.raises(CapacityError, match="InsufficientCapacity"):
            _extract_instance_id(response)

    def test_extract_instance_id_empty_instance_ids(self):
        """_extract_instance_id raises when InstanceIds is empty."""
        response = {"Instances": [{"InstanceIds": []}]}
        with pytest.raises(CapacityError, match="No instances launched"):
            _extract_instance_id(response)


class TestCreateFleetInstance:
    """Tests for create_fleet_instance function."""

    def test_create_fleet_instance_spot_returns_instance_id(self):
        """create_fleet_instance with spot returns instance ID."""
        mock_client = MagicMock()
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-123"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            use_spot=True,
        )
        result = create_fleet_instance(mock_client, "lt-123", opts)
        assert result == "i-123"

    def test_create_fleet_instance_spot_uses_spot_options(self):
        """create_fleet_instance with spot uses SpotOptions."""
        mock_client = MagicMock()
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-123"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            use_spot=True,
        )
        create_fleet_instance(mock_client, "lt-123", opts)
        call_args = mock_client.create_fleet.call_args
        assert "SpotOptions" in call_args.kwargs

    def test_create_fleet_instance_on_demand_returns_instance_id(self):
        """create_fleet_instance with on-demand returns instance ID."""
        mock_client = MagicMock()
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            use_spot=False,
        )
        result = create_fleet_instance(mock_client, "lt-123", opts)
        assert result == "i-456"

    def test_create_fleet_instance_on_demand_uses_on_demand_options(self):
        """create_fleet_instance with on-demand uses OnDemandOptions."""
        mock_client = MagicMock()
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            use_spot=False,
        )
        create_fleet_instance(mock_client, "lt-123", opts)
        call_args = mock_client.create_fleet.call_args
        assert "OnDemandOptions" in call_args.kwargs


# === Instance State Functions ===


class TestGetInstanceState:
    """Tests for get_instance_state function."""

    def test_get_instance_state_running(self):
        """get_instance_state returns running state."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        result = get_instance_state(mock_client, "i-123")
        assert result == "running"

    def test_get_instance_state_not_found(self):
        """get_instance_state returns unknown for not found instance."""
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound"}}, "DescribeInstances"
        )
        result = get_instance_state(mock_client, "i-123")
        assert result == "unknown"

    def test_get_instance_state_other_error(self):
        """get_instance_state raises for other errors."""
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "DescribeInstances"
        )
        with pytest.raises(ClientError):
            get_instance_state(mock_client, "i-123")

    def test_get_instance_state_no_reservations(self):
        """get_instance_state returns unknown for empty reservations."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {"Reservations": []}
        result = get_instance_state(mock_client, "i-123")
        assert result == "unknown"


class TestGetInstanceAz:
    """Tests for get_instance_az function."""

    def test_get_instance_az_returns_az(self):
        """get_instance_az returns the availability zone."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {"Instances": [{"Placement": {"AvailabilityZone": "us-east-2a"}}]}
            ]
        }
        result = get_instance_az(mock_client, "i-123")
        assert result == "us-east-2a"


# === Wait Functions ===


class TestWaitForInstanceRunning:
    """Tests for wait_for_instance_running function."""

    def test_wait_for_instance_running_immediate(self):
        """wait_for_instance_running returns immediately if running."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        # Should not raise
        wait_for_instance_running(mock_client, "i-123", max_attempts=1)

    def test_wait_for_instance_running_terminated(self):
        """wait_for_instance_running raises if instance terminated."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "terminated"}}]}]
        }
        with pytest.raises(RuntimeError, match="terminated"):
            wait_for_instance_running(mock_client, "i-123", max_attempts=1)

    def test_wait_for_instance_running_timeout(self):
        """wait_for_instance_running raises on timeout."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "pending"}}]}]
        }
        with patch("ec2_fleet.time.sleep"):
            with pytest.raises(RuntimeError, match="did not reach running state"):
                wait_for_instance_running(
                    mock_client, "i-123", max_attempts=2, poll_interval=0
                )

    def test_wait_for_instance_running_shutting_down(self):
        """wait_for_instance_running raises if instance shutting down."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "shutting-down"}}]}]
        }
        with pytest.raises(RuntimeError, match="shutting-down"):
            wait_for_instance_running(mock_client, "i-123", max_attempts=1)


class TestWaitForStatusChecks:
    """Tests for wait_for_status_checks function."""

    def test_wait_for_status_checks_immediate(self):
        """wait_for_status_checks returns immediately if passed."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        mock_client.describe_instance_status.return_value = {
            "InstanceStatuses": [
                {
                    "SystemStatus": {"Status": "ok"},
                    "InstanceStatus": {"Status": "ok"},
                }
            ]
        }
        wait_for_status_checks(mock_client, "i-123", max_attempts=1)

    def test_wait_for_status_checks_terminated(self):
        """wait_for_status_checks raises if instance terminated."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "terminated"}}]}]
        }
        with pytest.raises(RuntimeError, match="terminated"):
            wait_for_status_checks(mock_client, "i-123", max_attempts=1)

    def test_wait_for_status_checks_timeout(self):
        """wait_for_status_checks raises on timeout."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        mock_client.describe_instance_status.return_value = {
            "InstanceStatuses": [
                {
                    "SystemStatus": {"Status": "initializing"},
                    "InstanceStatus": {"Status": "initializing"},
                }
            ]
        }
        with patch("ec2_fleet.time.sleep"):
            with pytest.raises(RuntimeError, match="did not pass status checks"):
                wait_for_status_checks(
                    mock_client, "i-123", max_attempts=2, poll_interval=0
                )

    def test_wait_for_status_checks_empty_statuses(self):
        """wait_for_status_checks handles empty InstanceStatuses."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        mock_client.describe_instance_status.return_value = {"InstanceStatuses": []}
        with patch("ec2_fleet.time.sleep"):
            with pytest.raises(RuntimeError, match="did not pass status checks"):
                wait_for_status_checks(
                    mock_client, "i-123", max_attempts=2, poll_interval=0
                )


# === Terminate Instance ===


class TestTerminateInstance:
    """Tests for terminate_instance function."""

    def test_terminate_instance_success(self):
        """terminate_instance terminates successfully."""
        mock_client = MagicMock()
        terminate_instance(mock_client, "i-123")
        mock_client.terminate_instances.assert_called_once_with(InstanceIds=["i-123"])

    def test_terminate_instance_ignores_error(self):
        """terminate_instance ignores ClientError."""
        mock_client = MagicMock()
        mock_client.terminate_instances.side_effect = ClientError(
            {"Error": {"Code": "NotFound"}}, "TerminateInstances"
        )
        # Should not raise
        terminate_instance(mock_client, "i-123")


# === Launch Instance ===


class TestLaunchInstance:
    """Tests for launch_instance function."""

    def test_launch_instance_returns_instance_id(self):
        """launch_instance returns the launched instance ID."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
        )
        result = launch_instance(mock_client, {"ami_id": "ami-123"}, opts)
        assert result == "i-456"

    def test_launch_instance_deletes_launch_template(self):
        """launch_instance cleans up the launch template."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
        )
        launch_instance(mock_client, {"ami_id": "ami-123"}, opts)
        mock_client.delete_launch_template.assert_called_once()


# === Handle Launch Failure ===


class TestHandleLaunchFailure:
    """Tests for _handle_launch_failure function."""

    def test_handle_launch_failure_adds_excluded_az(self):
        """_handle_launch_failure adds instance AZ to excluded list."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {"Instances": [{"Placement": {"AvailabilityZone": "us-east-2a"}}]}
            ]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
        )
        _handle_launch_failure(mock_client, "i-123", opts)
        assert "us-east-2a" in opts.excluded_azs

    def test_handle_launch_failure_terminates_instance(self):
        """_handle_launch_failure terminates the failed instance."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {"Instances": [{"Placement": {"AvailabilityZone": "us-east-2a"}}]}
            ]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
        )
        _handle_launch_failure(mock_client, "i-123", opts)
        mock_client.terminate_instances.assert_called_once()

    def test_handle_launch_failure_ignores_az_error_excluded_azs_unchanged(self):
        """_handle_launch_failure leaves excluded_azs unchanged on AZ error."""
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "NotFound"}}, "DescribeInstances"
        )
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
        )
        _handle_launch_failure(mock_client, "i-123", opts)
        assert opts.excluded_azs == []

    def test_handle_launch_failure_ignores_az_error_still_terminates(self):
        """_handle_launch_failure still terminates instance on AZ error."""
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "NotFound"}}, "DescribeInstances"
        )
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
        )
        _handle_launch_failure(mock_client, "i-123", opts)
        mock_client.terminate_instances.assert_called_once()


# === Attempt Launch ===


class TestAttemptLaunch:
    """Tests for _attempt_launch function."""

    def test_attempt_launch_success_returns_instance_id(self):
        """_attempt_launch returns instance ID on success."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-1", "AvailabilityZone": "us-east-2a"}]
        }
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        mock_client.describe_instance_status.return_value = {
            "InstanceStatuses": [
                {"SystemStatus": {"Status": "ok"}, "InstanceStatus": {"Status": "ok"}}
            ]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            wait_for_ready=True,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert instance_id == "i-456"

    def test_attempt_launch_success_returns_no_error(self):
        """_attempt_launch returns no error on success."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-1", "AvailabilityZone": "us-east-2a"}]
        }
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        mock_client.describe_instance_status.return_value = {
            "InstanceStatuses": [
                {"SystemStatus": {"Status": "ok"}, "InstanceStatus": {"Status": "ok"}}
            ]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            wait_for_ready=True,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert error is None

    def test_attempt_launch_no_available_subnets_returns_empty_instance_id(self):
        """_attempt_launch returns empty string when all subnets excluded."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-1", "AvailabilityZone": "us-east-2a"}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=["us-east-2a"],
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert instance_id == ""

    def test_attempt_launch_no_available_subnets_returns_no_error(self):
        """_attempt_launch returns no error when all subnets excluded."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-1", "AvailabilityZone": "us-east-2a"}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=["us-east-2a"],
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert error is None

    def test_attempt_launch_capacity_error_returns_empty_instance_id(self):
        """_attempt_launch returns empty string on CapacityError."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {"Instances": [], "Errors": []}
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert instance_id == ""

    def test_attempt_launch_capacity_error_returns_capacity_error(self):
        """_attempt_launch returns CapacityError on capacity failure."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {"Instances": [], "Errors": []}
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert isinstance(error, CapacityError)

    def test_attempt_launch_runtime_error_returns_empty_instance_id(self):
        """_attempt_launch returns empty string on RuntimeError."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "State": {"Name": "terminated"},
                            "Placement": {"AvailabilityZone": "us-east-2a"},
                        }
                    ]
                }
            ]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
            wait_for_ready=True,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert instance_id == ""

    def test_attempt_launch_runtime_error_returns_runtime_error(self):
        """_attempt_launch returns RuntimeError on instance failure."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "State": {"Name": "terminated"},
                            "Placement": {"AvailabilityZone": "us-east-2a"},
                        }
                    ]
                }
            ]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
            wait_for_ready=True,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert isinstance(error, RuntimeError)

    def test_attempt_launch_runtime_error_no_instance_id_returns_error(self):
        """_attempt_launch returns RuntimeError when launch fails before getting instance ID."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.side_effect = RuntimeError("Fleet creation failed")
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
            wait_for_ready=True,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert isinstance(error, RuntimeError)

    def test_attempt_launch_runtime_error_no_instance_id_empty_instance_id(self):
        """_attempt_launch returns empty instance ID when RuntimeError before getting ID."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.side_effect = RuntimeError("Fleet creation failed")
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=[],
            wait_for_ready=True,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert instance_id == ""

    def test_attempt_launch_skip_wait_returns_instance_id(self):
        """_attempt_launch returns instance ID when wait_for_ready is False."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            wait_for_ready=False,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert instance_id == "i-456"

    def test_attempt_launch_skip_wait_returns_no_error(self):
        """_attempt_launch returns no error when wait_for_ready is False."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            wait_for_ready=False,
        )
        instance_id, error = _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        assert error is None

    def test_attempt_launch_skip_wait_does_not_call_describe_instances(self):
        """_attempt_launch skips describe_instances when wait_for_ready is False."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            wait_for_ready=False,
        )
        _attempt_launch(mock_client, {"ami_id": "ami-123"}, opts)
        mock_client.describe_instances.assert_not_called()


# === Launch Instance With Retry ===


class TestLaunchInstanceWithRetry:
    """Tests for launch_instance_with_retry function."""

    def test_launch_instance_with_retry_success(self):
        """launch_instance_with_retry succeeds on first attempt."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [{"InstanceIds": ["i-456"]}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            wait_for_ready=False,
        )
        result = launch_instance_with_retry(mock_client, {"ami_id": "ami-123"}, opts)
        assert result == "i-456"

    def test_launch_instance_with_retry_exhausted(self):
        """launch_instance_with_retry raises after exhausting retries."""
        mock_client = MagicMock()
        mock_client.create_launch_template.return_value = {
            "LaunchTemplate": {"LaunchTemplateId": "lt-123"}
        }
        mock_client.create_fleet.return_value = {
            "Instances": [],
            "Errors": [{"ErrorMessage": "InsufficientCapacity"}],
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            max_retries=0,
            wait_for_ready=False,
        )
        with pytest.raises(CapacityError, match="Failed to launch instance"):
            launch_instance_with_retry(mock_client, {"ami_id": "ami-123"}, opts)

    def test_launch_instance_with_retry_no_subnets(self):
        """launch_instance_with_retry raises when no subnets available."""
        mock_client = MagicMock()
        mock_client.describe_subnets.return_value = {
            "Subnets": [{"SubnetId": "subnet-1", "AvailabilityZone": "us-east-2a"}]
        }
        opts = LaunchOptions(
            instance_types=["m5.large"],
            subnet_ids=["subnet-1"],
            excluded_azs=["us-east-2a"],
            max_retries=0,
        )
        with pytest.raises(CapacityError, match="No subnets available"):
            launch_instance_with_retry(mock_client, {"ami_id": "ami-123"}, opts)
