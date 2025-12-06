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

    def test_parse_ecs_fargate_spot_labels(self):
        """Test parsing ECS Fargate spot labels."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'
        assert parsed.compute == 'fargate'
        assert parsed.pricing == 'spot'
        assert is_spot(parsed) is True

    def test_parse_ecs_fargate_on_demand_labels(self):
        """Test parsing ECS Fargate on-demand labels."""
        labels = ['ecs', 'fargate', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'
        assert parsed.compute == 'fargate'
        assert parsed.pricing == 'on-demand'
        assert is_spot(parsed) is False

    def test_parse_ec2_c8i_on_demand_labels(self):
        """Test parsing EC2 c8i on-demand labels."""
        labels = ['ec2', 'c8i', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'
        assert parsed.compute == 'c8i'
        assert get_instance_type(parsed) == 'c8i.4xlarge'
        assert is_spot(parsed) is False

    def test_parse_ec2_r8i_on_demand_labels(self):
        """Test parsing EC2 r8i on-demand labels."""
        labels = ['ec2', 'r8i', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'
        assert parsed.compute == 'r8i'
        assert get_instance_type(parsed) == 'r8i.4xlarge'

    def test_parse_ec2_g6e_on_demand_labels(self):
        """Test parsing EC2 g6e on-demand labels."""
        labels = ['ec2', 'g6e', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'
        assert parsed.compute == 'g6e'
        assert get_instance_type(parsed) == 'g6e.xlarge'

    def test_parse_ec2_c8i_spot_labels(self):
        """Test parsing EC2 c8i spot labels."""
        labels = ['ec2', 'c8i', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'
        assert parsed.compute == 'c8i'
        assert is_spot(parsed) is True


class TestLabelValidationIntegration:
    """Integration tests for label validation with invalid combinations."""

    def test_reject_ecs_with_c8i_compute(self):
        """Test rejection of ECS with c8i compute type."""
        labels = ['ecs', 'c8i', 'on-demand', 'runner-12345']
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

    def test_labels_with_e2e_marker(self):
        """Test parsing labels with e2e marker."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345', 'e2e']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'
        assert 'e2e' in labels

    def test_labels_with_self_hosted(self):
        """Test parsing labels with self-hosted marker."""
        labels = ['ec2', 'c8i', 'on-demand', 'runner-12345', 'self-hosted', 'linux', 'x64']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'
        assert get_instance_type(parsed) == 'c8i.4xlarge'

    def test_labels_in_any_order(self):
        """Test parsing labels in different orders."""
        labels_ordered = ['ecs', 'fargate', 'spot', 'runner-12345']
        labels_shuffled = ['runner-12345', 'spot', 'ecs', 'fargate']
        parsed1 = parse_labels(labels_ordered)
        parsed2 = parse_labels(labels_shuffled)
        assert parsed1.platform == parsed2.platform
        assert parsed1.compute == parsed2.compute
        assert parsed1.pricing == parsed2.pricing
