import { describe, it, expect, beforeAll, vi } from 'vitest';
import path from 'path';

const REPO_ROOT = path.resolve(import.meta.dirname, '../../../../../..');
vi.stubEnv('ETC_PATH', path.join(REPO_ROOT, 'etc'));

describe('runner_labels', () => {
  let runnerLabels;

  beforeAll(async () => {
    runnerLabels = await import('common/runner_labels.js');
  });

  describe('parseLabels', () => {
    it('should parse valid ECS Fargate labels', () => {
      const labels = ['self-hosted', 'ecs', 'fargate', 'arm', 'spot', 'runner-12345'];
      const parsed = runnerLabels.parseLabels(labels);

      expect(parsed.platform).toBe('ecs');
      expect(parsed.compute).toBe('fargate');
      expect(parsed.architecture).toBe('arm');
      expect(parsed.pricing).toBe('spot');
      expect(parsed.runnerId).toBe('runner-12345');
    });

    it('should parse valid EC2 general-purpose labels', () => {
      const labels = ['self-hosted', 'ec2', 'general-purpose', 'arm', 'on-demand', 'runner-99999'];
      const parsed = runnerLabels.parseLabels(labels);

      expect(parsed.platform).toBe('ec2');
      expect(parsed.compute).toBe('general-purpose');
      expect(parsed.architecture).toBe('arm');
      expect(parsed.pricing).toBe('on-demand');
      expect(parsed.runnerId).toBe('runner-99999');
    });

    it('should parse valid EC2 GPU labels without architecture', () => {
      const labels = ['self-hosted', 'ec2', 'gpu', 'spot', 'runner-777'];
      const parsed = runnerLabels.parseLabels(labels);

      expect(parsed.platform).toBe('ec2');
      expect(parsed.compute).toBe('gpu');
      expect(parsed.architecture).toBeNull();
      expect(parsed.pricing).toBe('spot');
      expect(parsed.runnerId).toBe('runner-777');
    });

    it('should throw LabelParseError for empty label list', () => {
      expect(() => runnerLabels.parseLabels([])).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels([])).toThrow('Label list cannot be empty');
    });

    it('should throw LabelParseError for null label list', () => {
      expect(() => runnerLabels.parseLabels(null)).toThrow(runnerLabels.LabelParseError);
    });

    it('should throw LabelParseError when missing platform label', () => {
      const labels = ['self-hosted', 'fargate', 'arm', 'spot', 'runner-123'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Missing platform label');
    });

    it('should throw LabelParseError when multiple platforms specified', () => {
      const labels = ['ecs', 'ec2', 'fargate', 'arm', 'spot', 'runner-123'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Multiple platform labels');
    });

    it('should throw LabelParseError when missing compute label', () => {
      const labels = ['ecs', 'arm', 'spot', 'runner-123'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Missing compute label');
    });

    it('should throw LabelParseError when multiple compute types specified', () => {
      const labels = ['ecs', 'fargate', 'gpu', 'arm', 'spot', 'runner-123'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Multiple compute labels');
    });

    it('should throw LabelParseError when multiple architectures specified', () => {
      const labels = ['ecs', 'fargate', 'arm', 'x86', 'spot', 'runner-123'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Multiple architecture labels');
    });

    it('should throw LabelParseError when missing pricing label', () => {
      const labels = ['ecs', 'fargate', 'arm', 'runner-123'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Missing pricing label');
    });

    it('should throw LabelParseError when multiple pricing labels specified', () => {
      const labels = ['ecs', 'fargate', 'arm', 'spot', 'on-demand', 'runner-123'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Multiple pricing labels');
    });

    it('should throw LabelParseError when missing runner ID', () => {
      const labels = ['ecs', 'fargate', 'arm', 'spot'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Missing runner ID label');
    });

    it('should throw LabelParseError for invalid runner ID format', () => {
      const labels = ['ecs', 'fargate', 'arm', 'spot', 'runner-abc'];
      expect(() => runnerLabels.parseLabels(labels)).toThrow(runnerLabels.LabelParseError);
      expect(() => runnerLabels.parseLabels(labels)).toThrow('Missing runner ID label');
    });
  });

  describe('validateLabels', () => {
    it('should pass for valid ECS Fargate with arm architecture', () => {
      const parsed = {
        platform: 'ecs',
        compute: 'fargate',
        architecture: 'arm',
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).not.toThrow();
    });

    it('should pass for valid ECS Fargate with x86 architecture', () => {
      const parsed = {
        platform: 'ecs',
        compute: 'fargate',
        architecture: 'x86',
        pricing: 'on-demand',
        runnerId: 'runner-456'
      };
      expect(() => runnerLabels.validateLabels(parsed)).not.toThrow();
    });

    it('should throw LabelValidationError for ECS with invalid compute type', () => {
      const parsed = {
        platform: 'ecs',
        compute: 'gpu',
        architecture: 'arm',
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).toThrow(runnerLabels.LabelValidationError);
      expect(() => runnerLabels.validateLabels(parsed)).toThrow('ECS platform only supports compute types');
    });

    it('should throw LabelValidationError for ECS without architecture', () => {
      const parsed = {
        platform: 'ecs',
        compute: 'fargate',
        architecture: null,
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).toThrow(runnerLabels.LabelValidationError);
      expect(() => runnerLabels.validateLabels(parsed)).toThrow('ECS platform requires architecture label');
    });

    it('should throw LabelValidationError for ECS with invalid architecture', () => {
      const parsed = {
        platform: 'ecs',
        compute: 'fargate',
        architecture: 'intel',
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).toThrow(runnerLabels.LabelValidationError);
      expect(() => runnerLabels.validateLabels(parsed)).toThrow('ECS platform only supports architectures');
    });

    it('should pass for valid EC2 general-purpose with arm', () => {
      const parsed = {
        platform: 'ec2',
        compute: 'general-purpose',
        architecture: 'arm',
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).not.toThrow();
    });

    it('should pass for valid EC2 memory-optimized with intel', () => {
      const parsed = {
        platform: 'ec2',
        compute: 'memory-optimized',
        architecture: 'intel',
        pricing: 'on-demand',
        runnerId: 'runner-456'
      };
      expect(() => runnerLabels.validateLabels(parsed)).not.toThrow();
    });

    it('should pass for valid EC2 GPU without architecture', () => {
      const parsed = {
        platform: 'ec2',
        compute: 'gpu',
        architecture: null,
        pricing: 'spot',
        runnerId: 'runner-789'
      };
      expect(() => runnerLabels.validateLabels(parsed)).not.toThrow();
    });

    it('should throw LabelValidationError for EC2 with invalid compute type', () => {
      const parsed = {
        platform: 'ec2',
        compute: 'fargate',
        architecture: 'arm',
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).toThrow(runnerLabels.LabelValidationError);
      expect(() => runnerLabels.validateLabels(parsed)).toThrow('EC2 platform only supports compute types');
    });

    it('should throw LabelValidationError for EC2 general-purpose without architecture', () => {
      const parsed = {
        platform: 'ec2',
        compute: 'general-purpose',
        architecture: null,
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).toThrow(runnerLabels.LabelValidationError);
      expect(() => runnerLabels.validateLabels(parsed)).toThrow("EC2 compute type 'general-purpose' requires architecture");
    });

    it('should throw LabelValidationError for EC2 GPU with architecture', () => {
      const parsed = {
        platform: 'ec2',
        compute: 'gpu',
        architecture: 'arm',
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).toThrow(runnerLabels.LabelValidationError);
      expect(() => runnerLabels.validateLabels(parsed)).toThrow("EC2 compute type 'gpu' does not support architecture");
    });

    it('should throw LabelValidationError for EC2 FPGA with architecture', () => {
      const parsed = {
        platform: 'ec2',
        compute: 'fpga',
        architecture: 'intel',
        pricing: 'spot',
        runnerId: 'runner-123'
      };
      expect(() => runnerLabels.validateLabels(parsed)).toThrow(runnerLabels.LabelValidationError);
      expect(() => runnerLabels.validateLabels(parsed)).toThrow("EC2 compute type 'fpga' does not support architecture");
    });
  });

  describe('getInstanceType', () => {
    it('should return null for ECS platform', () => {
      const parsed = { platform: 'ecs', compute: 'fargate', architecture: 'arm' };
      expect(runnerLabels.getInstanceType(parsed)).toBeNull();
    });

    it('should return correct instance type for EC2 general-purpose arm', () => {
      const parsed = { platform: 'ec2', compute: 'general-purpose', architecture: 'arm' };
      expect(runnerLabels.getInstanceType(parsed)).toBe('m8gd.4xlarge');
    });

    it('should return correct instance type for EC2 general-purpose intel', () => {
      const parsed = { platform: 'ec2', compute: 'general-purpose', architecture: 'intel' };
      expect(runnerLabels.getInstanceType(parsed)).toBe('m7id.4xlarge');
    });

    it('should return correct instance type for EC2 general-purpose amd', () => {
      const parsed = { platform: 'ec2', compute: 'general-purpose', architecture: 'amd' };
      expect(runnerLabels.getInstanceType(parsed)).toBe('m7ad.4xlarge');
    });

    it('should return correct instance type for EC2 memory-optimized arm', () => {
      const parsed = { platform: 'ec2', compute: 'memory-optimized', architecture: 'arm' };
      expect(runnerLabels.getInstanceType(parsed)).toBe('r8gd.4xlarge');
    });

    it('should return correct instance type for EC2 GPU', () => {
      const parsed = { platform: 'ec2', compute: 'gpu', architecture: null };
      expect(runnerLabels.getInstanceType(parsed)).toBe('g6e.2xlarge');
    });

    it('should return correct instance type for EC2 FPGA', () => {
      const parsed = { platform: 'ec2', compute: 'fpga', architecture: null };
      expect(runnerLabels.getInstanceType(parsed)).toBe('f2.12xlarge');
    });

    it('should return null for unknown compute/architecture combination', () => {
      const parsed = { platform: 'ec2', compute: 'unknown', architecture: 'arm' };
      expect(runnerLabels.getInstanceType(parsed)).toBeNull();
    });
  });

  describe('getEcsConfig', () => {
    it('should return null for EC2 platform', () => {
      const parsed = { platform: 'ec2', compute: 'general-purpose', architecture: 'arm' };
      expect(runnerLabels.getEcsConfig(parsed)).toBeNull();
    });

    it('should return Fargate config for ECS Fargate', () => {
      const parsed = { platform: 'ecs', compute: 'fargate', architecture: 'arm' };
      const config = runnerLabels.getEcsConfig(parsed);

      expect(config).toBeDefined();
      expect(config.cpu).toBe('4096');
      expect(config.memory).toBe('16384');
    });

    it('should return a copy of the config object', () => {
      const parsed = { platform: 'ecs', compute: 'fargate', architecture: 'arm' };
      const config1 = runnerLabels.getEcsConfig(parsed);
      const config2 = runnerLabels.getEcsConfig(parsed);

      expect(config1).not.toBe(config2);
      expect(config1).toEqual(config2);
    });
  });

  describe('getTaskArchitecture', () => {
    it('should return null for EC2 platform', () => {
      const parsed = { platform: 'ec2', compute: 'general-purpose', architecture: 'arm' };
      expect(runnerLabels.getTaskArchitecture(parsed)).toBeNull();
    });

    it('should return null for ECS without architecture', () => {
      const parsed = { platform: 'ecs', compute: 'fargate', architecture: null };
      expect(runnerLabels.getTaskArchitecture(parsed)).toBeNull();
    });

    it('should return ARM64 for ECS arm', () => {
      const parsed = { platform: 'ecs', compute: 'fargate', architecture: 'arm' };
      expect(runnerLabels.getTaskArchitecture(parsed)).toBe('ARM64');
    });

    it('should return X86_64 for ECS x86', () => {
      const parsed = { platform: 'ecs', compute: 'fargate', architecture: 'x86' };
      expect(runnerLabels.getTaskArchitecture(parsed)).toBe('X86_64');
    });
  });

  describe('isSpot', () => {
    it('should return true for spot pricing', () => {
      const parsed = { pricing: 'spot' };
      expect(runnerLabels.isSpot(parsed)).toBe(true);
    });

    it('should return false for on-demand pricing', () => {
      const parsed = { pricing: 'on-demand' };
      expect(runnerLabels.isSpot(parsed)).toBe(false);
    });
  });

  describe('getRunnerIdNumber', () => {
    it('should extract number from runner ID', () => {
      const parsed = { runnerId: 'runner-12345' };
      expect(runnerLabels.getRunnerIdNumber(parsed)).toBe(12345);
    });

    it('should handle large runner ID numbers', () => {
      const parsed = { runnerId: 'runner-99999999' };
      expect(runnerLabels.getRunnerIdNumber(parsed)).toBe(99999999);
    });

    it('should throw LabelParseError for invalid runner ID format', () => {
      const parsed = { runnerId: 'invalid-runner-id' };
      expect(() => runnerLabels.getRunnerIdNumber(parsed)).toThrow(runnerLabels.LabelParseError);
    });
  });

  describe('exported constants', () => {
    it('should export PLATFORMS set', () => {
      expect(runnerLabels.PLATFORMS).toBeInstanceOf(Set);
      expect(runnerLabels.PLATFORMS.has('ecs')).toBe(true);
      expect(runnerLabels.PLATFORMS.has('ec2')).toBe(true);
    });

    it('should export PRICING_MODELS set', () => {
      expect(runnerLabels.PRICING_MODELS).toBeInstanceOf(Set);
      expect(runnerLabels.PRICING_MODELS.has('spot')).toBe(true);
      expect(runnerLabels.PRICING_MODELS.has('on-demand')).toBe(true);
    });

    it('should export ECS_COMPUTE set', () => {
      expect(runnerLabels.ECS_COMPUTE).toBeInstanceOf(Set);
      expect(runnerLabels.ECS_COMPUTE.has('fargate')).toBe(true);
    });

    it('should export ECS_ARCHITECTURES set', () => {
      expect(runnerLabels.ECS_ARCHITECTURES).toBeInstanceOf(Set);
      expect(runnerLabels.ECS_ARCHITECTURES.has('arm')).toBe(true);
      expect(runnerLabels.ECS_ARCHITECTURES.has('x86')).toBe(true);
    });

    it('should export EC2_COMPUTE set', () => {
      expect(runnerLabels.EC2_COMPUTE).toBeInstanceOf(Set);
      expect(runnerLabels.EC2_COMPUTE.has('general-purpose')).toBe(true);
      expect(runnerLabels.EC2_COMPUTE.has('memory-optimized')).toBe(true);
      expect(runnerLabels.EC2_COMPUTE.has('gpu')).toBe(true);
      expect(runnerLabels.EC2_COMPUTE.has('fpga')).toBe(true);
    });

    it('should export EC2_ARCHITECTURES set', () => {
      expect(runnerLabels.EC2_ARCHITECTURES).toBeInstanceOf(Set);
      expect(runnerLabels.EC2_ARCHITECTURES.has('intel')).toBe(true);
      expect(runnerLabels.EC2_ARCHITECTURES.has('amd')).toBe(true);
      expect(runnerLabels.EC2_ARCHITECTURES.has('arm')).toBe(true);
    });
  });
});
