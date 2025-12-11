"""Integration tests for runner label system."""
import pytest
from runner_labels import (
    parse_labels,
    validate_labels,
    get_instance_type,
    is_spot,
    LabelParseError,
    LabelValidationError,
    PLATFORMS,
    PRICING_MODELS,
    ECS_COMPUTE,
    EC2_COMPUTE,
    ECS_ARCHITECTURES,
    EC2_ARCHITECTURES,
    EC2_COMPUTE_REQUIRES_ARCH,
    EC2_COMPUTE_FORBIDS_ARCH,
)


# Valid label combinations for testing (single source of truth)
def get_ecs_labels(arch='x86', pricing='spot', runner_id='runner-12345'):
    """Generate valid ECS Fargate labels."""
    return ['ecs', 'fargate', arch, pricing, runner_id]


def get_ec2_labels(compute='memory-optimized', arch='intel', pricing='spot', runner_id='runner-12345'):
    """Generate valid EC2 labels with architecture."""
    return ['ec2', compute, arch, pricing, runner_id]


def get_ec2_gpu_labels(pricing='spot', runner_id='runner-12345'):
    """Generate valid EC2 GPU labels (no architecture)."""
    return ['ec2', 'gpu', pricing, runner_id]


def get_ec2_fpga_labels(pricing='on-demand', runner_id='runner-12345'):
    """Generate valid EC2 FPGA labels (no architecture)."""
    return ['ec2', 'fpga', pricing, runner_id]


class TestLabelParsingIntegration:
    """Integration tests for label parsing with real label combinations."""

    def test_parse_ecs_fargate_spot_labels_platform(self):
        """Test ECS Fargate spot labels parse platform correctly."""
        labels = get_ecs_labels()
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'

    def test_parse_ecs_fargate_spot_labels_compute(self):
        """Test ECS Fargate spot labels parse compute correctly."""
        labels = get_ecs_labels()
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'fargate'

    def test_parse_ecs_fargate_spot_labels_architecture(self):
        """Test ECS Fargate spot labels parse architecture correctly."""
        labels = get_ecs_labels(arch='x86')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.architecture == 'x86'

    def test_parse_ecs_fargate_spot_labels_pricing(self):
        """Test ECS Fargate spot labels parse pricing correctly."""
        labels = get_ecs_labels()
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.pricing == 'spot'

    def test_parse_ecs_fargate_spot_labels_is_spot(self):
        """Test ECS Fargate spot labels return is_spot true."""
        labels = get_ecs_labels()
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert is_spot(parsed) is True

    def test_parse_ecs_fargate_arm_on_demand_labels_platform(self):
        """Test ECS Fargate arm on-demand labels parse platform correctly."""
        labels = get_ecs_labels(arch='arm', pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'

    def test_parse_ecs_fargate_arm_on_demand_labels_compute(self):
        """Test ECS Fargate arm on-demand labels parse compute correctly."""
        labels = get_ecs_labels(arch='arm', pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'fargate'

    def test_parse_ecs_fargate_arm_on_demand_labels_architecture(self):
        """Test ECS Fargate arm on-demand labels parse architecture correctly."""
        labels = get_ecs_labels(arch='arm', pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.architecture == 'arm'

    def test_parse_ecs_fargate_arm_on_demand_labels_pricing(self):
        """Test ECS Fargate arm on-demand labels parse pricing correctly."""
        labels = get_ecs_labels(arch='arm', pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.pricing == 'on-demand'

    def test_parse_ecs_fargate_arm_on_demand_labels_is_spot(self):
        """Test ECS Fargate arm on-demand labels return is_spot false."""
        labels = get_ecs_labels(arch='arm', pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert is_spot(parsed) is False

    def test_parse_ec2_memory_optimized_intel_on_demand_labels_platform(self):
        """Test EC2 memory-optimized intel on-demand labels parse platform correctly."""
        labels = get_ec2_labels(pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_parse_ec2_memory_optimized_intel_on_demand_labels_compute(self):
        """Test EC2 memory-optimized intel on-demand labels parse compute correctly."""
        labels = get_ec2_labels(pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'memory-optimized'

    def test_parse_ec2_memory_optimized_intel_on_demand_labels_instance_type(self):
        """Test EC2 memory-optimized intel on-demand labels return correct instance type."""
        labels = get_ec2_labels(pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert get_instance_type(parsed) == 'r8i.4xlarge'

    def test_parse_ec2_gpu_on_demand_labels_platform(self):
        """Test EC2 gpu on-demand labels parse platform correctly."""
        labels = get_ec2_gpu_labels(pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_parse_ec2_gpu_on_demand_labels_compute(self):
        """Test EC2 gpu on-demand labels parse compute correctly."""
        labels = get_ec2_gpu_labels(pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'gpu'

    def test_parse_ec2_gpu_on_demand_labels_instance_type(self):
        """Test EC2 gpu on-demand labels return correct instance type."""
        labels = get_ec2_gpu_labels(pricing='on-demand')
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert get_instance_type(parsed) == 'g6e.2xlarge'

    def test_parse_ec2_memory_optimized_intel_spot_labels_platform(self):
        """Test EC2 memory-optimized intel spot labels parse platform correctly."""
        labels = get_ec2_labels()
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_parse_ec2_memory_optimized_intel_spot_labels_compute(self):
        """Test EC2 memory-optimized intel spot labels parse compute correctly."""
        labels = get_ec2_labels()
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.compute == 'memory-optimized'

    def test_parse_ec2_memory_optimized_intel_spot_labels_is_spot(self):
        """Test EC2 memory-optimized intel spot labels return is_spot true."""
        labels = get_ec2_labels()
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert is_spot(parsed) is True


class TestLabelValidationIntegration:
    """Integration tests for label validation with invalid combinations."""

    def test_reject_ecs_with_ec2_compute(self):
        """Test rejection of ECS with EC2-only compute type."""
        # Use first EC2-only compute type from the module constants
        ec2_compute = next(iter(EC2_COMPUTE))
        labels = ['ecs', ec2_compute, 'x86', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        with pytest.raises(LabelValidationError):
            validate_labels(parsed)

    def test_reject_ec2_with_fargate_compute(self):
        """Test rejection of EC2 with fargate compute type."""
        labels = ['ec2', 'fargate', 'intel', 'on-demand', 'runner-12345']
        parsed = parse_labels(labels)
        with pytest.raises(LabelValidationError):
            validate_labels(parsed)

    def test_reject_ecs_without_architecture(self):
        """Test rejection of ECS labels missing architecture."""
        labels = ['ecs', 'fargate', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        with pytest.raises(LabelValidationError):
            validate_labels(parsed)

    def test_reject_ec2_requires_arch_without_architecture(self):
        """Test rejection of EC2 compute types that require architecture when missing."""
        # Use first compute type that requires architecture
        compute = next(iter(EC2_COMPUTE_REQUIRES_ARCH))
        labels = ['ec2', compute, 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        with pytest.raises(LabelValidationError):
            validate_labels(parsed)

    def test_reject_ec2_forbids_arch_with_architecture(self):
        """Test rejection of EC2 compute types that forbid architecture when present."""
        # Use first compute type that forbids architecture
        compute = next(iter(EC2_COMPUTE_FORBIDS_ARCH))
        labels = ['ec2', compute, 'intel', 'spot', 'runner-12345']
        parsed = parse_labels(labels)
        with pytest.raises(LabelValidationError):
            validate_labels(parsed)

    def test_reject_missing_platform_label(self):
        """Test rejection of labels missing platform."""
        labels = ['fargate', 'x86', 'spot', 'runner-12345']
        with pytest.raises(LabelParseError):
            parse_labels(labels)

    def test_reject_missing_runner_id(self):
        """Test rejection of labels missing runner ID."""
        labels = ['ecs', 'fargate', 'x86', 'spot']
        with pytest.raises(LabelParseError):
            parse_labels(labels)


class TestLabelSystemWithExtraLabels:
    """Integration tests for label system with additional labels."""

    def test_labels_with_e2e_marker_parses_platform(self):
        """Test labels with e2e marker parse platform correctly."""
        labels = get_ecs_labels() + ['e2e']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ecs'

    def test_labels_with_self_hosted_parses_platform(self):
        """Test labels with self-hosted marker parse platform correctly."""
        labels = get_ec2_labels(pricing='on-demand') + ['self-hosted', 'linux', 'x64']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.platform == 'ec2'

    def test_labels_with_self_hosted_instance_type(self):
        """Test labels with self-hosted marker return correct instance type."""
        labels = get_ec2_labels(pricing='on-demand') + ['self-hosted', 'linux', 'x64']
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert get_instance_type(parsed) == 'r8i.4xlarge'

    def test_labels_in_any_order_platform(self):
        """Test labels in different orders parse platform identically."""
        labels_ordered = get_ecs_labels()
        labels_shuffled = list(reversed(labels_ordered))
        parsed1 = parse_labels(labels_ordered)
        parsed2 = parse_labels(labels_shuffled)
        assert parsed1.platform == parsed2.platform

    def test_labels_in_any_order_compute(self):
        """Test labels in different orders parse compute identically."""
        labels_ordered = get_ecs_labels()
        labels_shuffled = list(reversed(labels_ordered))
        parsed1 = parse_labels(labels_ordered)
        parsed2 = parse_labels(labels_shuffled)
        assert parsed1.compute == parsed2.compute

    def test_labels_in_any_order_pricing(self):
        """Test labels in different orders parse pricing identically."""
        labels_ordered = get_ecs_labels()
        labels_shuffled = list(reversed(labels_ordered))
        parsed1 = parse_labels(labels_ordered)
        parsed2 = parse_labels(labels_shuffled)
        assert parsed1.pricing == parsed2.pricing


class TestAllValidArchitectures:
    """Parameterized tests for all valid architecture combinations."""

    @pytest.mark.parametrize("arch", list(ECS_ARCHITECTURES))
    def test_ecs_accepts_all_valid_architectures(self, arch):
        """Test ECS accepts all valid ECS architectures."""
        labels = get_ecs_labels(arch=arch)
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.architecture == arch

    @pytest.mark.parametrize("arch", list(EC2_ARCHITECTURES))
    def test_ec2_memory_optimized_accepts_all_valid_architectures(self, arch):
        """Test EC2 memory-optimized accepts all valid EC2 architectures."""
        labels = get_ec2_labels(arch=arch)
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.architecture == arch

    @pytest.mark.parametrize("pricing", list(PRICING_MODELS))
    def test_all_pricing_models_are_valid(self, pricing):
        """Test all pricing models are valid."""
        labels = get_ecs_labels(pricing=pricing)
        parsed = parse_labels(labels)
        validate_labels(parsed)
        assert parsed.pricing == pricing
