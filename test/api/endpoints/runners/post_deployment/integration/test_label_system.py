"""Integration tests for runner label system."""
from runner_labels import (
    parse_labels,
    validate_labels,
    get_instance_type,
    is_spot,
    LabelParseError,
    LabelValidationError,
)


class TestLabelParsingIntegration:
    """Integration tests for label parsing with real label combinations."""

    def test_parse_ecs_fargate_spot_labels_platform(self):
        """Test ECS Fargate spot labels parse platform correctly."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'

    def test_parse_ecs_fargate_spot_labels_compute(self):
        """Test ECS Fargate spot labels parse compute correctly."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'fargate'

    def test_parse_ecs_fargate_spot_labels_pricing(self):
        """Test ECS Fargate spot labels parse pricing correctly."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.pricing == 'spot'

    def test_parse_ecs_fargate_spot_labels_is_spot(self):
        """Test ECS Fargate spot labels return is_spot true."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert is_spot(parsed) is True

    def test_parse_ecs_fargate_on_demand_labels_platform(self):
        """Test ECS Fargate on-demand labels parse platform correctly."""
        labels = ['ecs', 'fargate', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'

    def test_parse_ecs_fargate_on_demand_labels_compute(self):
        """Test ECS Fargate on-demand labels parse compute correctly."""
        labels = ['ecs', 'fargate', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'fargate'

    def test_parse_ecs_fargate_on_demand_labels_pricing(self):
        """Test ECS Fargate on-demand labels parse pricing correctly."""
        labels = ['ecs', 'fargate', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.pricing == 'on-demand'

    def test_parse_ecs_fargate_on_demand_labels_is_spot(self):
        """Test ECS Fargate on-demand labels return is_spot false."""
        labels = ['ecs', 'fargate', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert is_spot(parsed) is False

    def test_parse_ec2_r8i_on_demand_labels_platform(self):
        """Test EC2 r8i on-demand labels parse platform correctly."""
        labels = ['ec2', 'r8i', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_parse_ec2_r8i_on_demand_labels_compute(self):
        """Test EC2 r8i on-demand labels parse compute correctly."""
        labels = ['ec2', 'r8i', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'r8i'

    def test_parse_ec2_r8i_on_demand_labels_instance_type(self):
        """Test EC2 r8i on-demand labels return correct instance type."""
        labels = ['ec2', 'r8i', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert get_instance_type(parsed) == 'r8i.4xlarge'

    def test_parse_ec2_g6e_on_demand_labels_platform(self):
        """Test EC2 g6e on-demand labels parse platform correctly."""
        labels = ['ec2', 'g6e', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_parse_ec2_g6e_on_demand_labels_compute(self):
        """Test EC2 g6e on-demand labels parse compute correctly."""
        labels = ['ec2', 'g6e', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'g6e'

    def test_parse_ec2_g6e_on_demand_labels_instance_type(self):
        """Test EC2 g6e on-demand labels return correct instance type."""
        labels = ['ec2', 'g6e', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert get_instance_type(parsed) == 'g6e.2xlarge'

    def test_parse_ec2_r8i_spot_labels_platform(self):
        """Test EC2 r8i spot labels parse platform correctly."""
        labels = ['ec2', 'r8i', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_parse_ec2_r8i_spot_labels_compute(self):
        """Test EC2 r8i spot labels parse compute correctly."""
        labels = ['ec2', 'r8i', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'r8i'

    def test_parse_ec2_r8i_spot_labels_is_spot(self):
        """Test EC2 r8i spot labels return is_spot true."""
        labels = ['ec2', 'r8i', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert is_spot(parsed) is True


class TestLabelValidationIntegration:
    """Integration tests for label validation with invalid combinations."""

    def test_reject_ecs_with_r8i_compute(self):
        """Test rejection of ECS with r8i compute type."""
        labels = ['ecs', 'r8i', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        try:
            validate_labels(parsed)
            assert False, "Should have raised LabelValidationError"
        except LabelValidationError:
            pass

    def test_reject_ec2_with_fargate_compute(self):
        """Test rejection of EC2 with fargate compute type."""
        labels = ['ec2', 'fargate', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        try:
            validate_labels(parsed)
            assert False, "Should have raised LabelValidationError"
        except LabelValidationError:
            pass

    def test_reject_missing_platform_label(self):
        """Test rejection of labels missing platform."""
        labels = ['fargate', 'spot', 'runner-12345']
        try:
            parse_labels(labels)
            assert False, "Should have raised LabelParseError"
        except LabelParseError:
            pass

    def test_reject_missing_runner_id(self):
        """Test rejection of labels missing runner ID."""
        labels = ['ecs', 'fargate', 'spot']
        try:
            parse_labels(labels)
            assert False, "Should have raised LabelParseError"
        except LabelParseError:
            pass


class TestLabelSystemWithExtraLabels:
    """Integration tests for label system with additional labels."""

    def test_labels_with_e2e_marker_parses_platform(self):
        """Test labels with e2e marker parse platform correctly."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345', 'e2e']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'

    def test_labels_with_self_hosted_parses_platform(self):
        """Test labels with self-hosted marker parse platform correctly."""
        labels = ['ec2', 'r8i', 'on-demand', 'runner-12345', 'self-hosted', 'linux', 'x64']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_labels_with_self_hosted_instance_type(self):
        """Test labels with self-hosted marker return correct instance type."""
        labels = ['ec2', 'r8i', 'on-demand', 'runner-12345', 'self-hosted', 'linux', 'x64']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert get_instance_type(parsed) == 'r8i.4xlarge'

    def test_labels_in_any_order_platform(self):
        """Test labels in different orders parse platform identically."""
        labels_ordered = ['ecs', 'fargate', 'spot', 'runner-12345']
        labels_shuffled = ['runner-12345', 'spot', 'ecs', 'fargate']
        parsed1 = parse_labels(labels_ordered)
        parsed2 = parse_labels(labels_shuffled)
        assert parsed1.platform == parsed2.platform

    def test_labels_in_any_order_compute(self):
        """Test labels in different orders parse compute identically."""
        labels_ordered = ['ecs', 'fargate', 'spot', 'runner-12345']
        labels_shuffled = ['runner-12345', 'spot', 'ecs', 'fargate']
        parsed1 = parse_labels(labels_ordered)
        parsed2 = parse_labels(labels_shuffled)
        assert parsed1.compute == parsed2.compute

    def test_labels_in_any_order_pricing(self):
        """Test labels in different orders parse pricing identically."""
        labels_ordered = ['ecs', 'fargate', 'spot', 'runner-12345']
        labels_shuffled = ['runner-12345', 'spot', 'ecs', 'fargate']
        parsed1 = parse_labels(labels_ordered)
        parsed2 = parse_labels(labels_shuffled)
        assert parsed1.pricing == parsed2.pricing
