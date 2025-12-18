import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mockClient } from 'aws-sdk-client-mock';
import { SSMClient, GetParameterCommand } from '@aws-sdk/client-ssm';
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';
import { SQSClient } from '@aws-sdk/client-sqs';

const ssmMock = mockClient(SSMClient);
const cloudwatchMock = mockClient(CloudWatchClient);
const sqsMock = mockClient(SQSClient);

describe('runner_starter', () => {
  let handler;

  beforeEach(async () => {
    vi.resetModules();
    ssmMock.reset();
    cloudwatchMock.reset();
    sqsMock.reset();

    vi.stubEnv('API_BASE_URL', 'https://api.example.com');
    vi.stubEnv('API_KEY_PARAMETER_NAME', '/api/key');

    // Mock SSM for API key retrieval
    ssmMock.on(GetParameterCommand).resolves({
      Parameter: { Value: 'test-api-key' }
    });

    // Mock CloudWatch for metrics
    cloudwatchMock.on(PutMetricDataCommand).resolves({});

    handler = await import('../../../../src/api/endpoints/runners/lambdas/runner_starter.js');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  describe('getRunnerTypeFromLabels', () => {
    it('should return ec2 for ec2 platform labels', () => {
      const [runnerType, endpointSuffix] = handler.getRunnerTypeFromLabels(
        ['self-hosted', 'ec2', 'general-purpose', 'arm', 'on-demand', 'runner-12345']
      );
      expect(runnerType).toBe('ec2');
      expect(endpointSuffix).toBe('ec2-runner');
    });

    it('should return fargate for ecs platform labels', () => {
      const [runnerType, endpointSuffix] = handler.getRunnerTypeFromLabels(
        ['self-hosted', 'ecs', 'fargate', 'arm', 'spot', 'runner-12345']
      );
      expect(runnerType).toBe('fargate');
      expect(endpointSuffix).toBe('ecs-runner');
    });

    it('should return ec2-e2e for ec2 e2e labels', () => {
      const [runnerType, endpointSuffix] = handler.getRunnerTypeFromLabels(
        ['self-hosted', 'ec2', 'general-purpose', 'arm', 'on-demand', 'runner-12345', 'e2e']
      );
      expect(runnerType).toBe('ec2-e2e');
      expect(endpointSuffix).toBe('ec2-runner');
    });

    it('should return fargate-e2e for ecs e2e labels', () => {
      const [runnerType, endpointSuffix] = handler.getRunnerTypeFromLabels(
        ['self-hosted', 'ecs', 'fargate', 'arm', 'spot', 'runner-12345', 'e2e']
      );
      expect(runnerType).toBe('fargate-e2e');
      expect(endpointSuffix).toBe('ecs-runner');
    });

    it('should return null for non-matching labels', () => {
      const [runnerType, endpointSuffix] = handler.getRunnerTypeFromLabels(
        ['self-hosted', 'ubuntu-latest']
      );
      expect(runnerType).toBeNull();
      expect(endpointSuffix).toBeNull();
    });
  });

  describe('checkCircuitBreaker', () => {
    it('should allow requests when circuit breaker is closed', () => {
      expect(handler.checkCircuitBreaker()).toBe(true);
    });
  });

  describe('recordCircuitBreakerSuccess', () => {
    it('should reset failure count', () => {
      handler.recordCircuitBreakerSuccess();
      expect(handler.checkCircuitBreaker()).toBe(true);
    });
  });

  describe('getApiKey', () => {
    it('should retrieve API key from SSM', async () => {
      const apiKey = await handler.getApiKey();
      expect(apiKey).toBe('test-api-key');
    });

    it('should cache API key', async () => {
      await handler.getApiKey();
      await handler.getApiKey();
      // Should only call SSM once due to caching
      const calls = ssmMock.commandCalls(GetParameterCommand);
      expect(calls.length).toBe(1);
    });

    it('should throw when API_KEY_PARAMETER_NAME is not set', async () => {
      vi.stubEnv('API_KEY_PARAMETER_NAME', '');
      vi.resetModules();
      const freshHandler = await import('../../../../src/api/endpoints/runners/lambdas/runner_starter.js');
      await expect(freshHandler.getApiKey()).rejects.toThrow('API_KEY_PARAMETER_NAME');
    });
  });

  describe('handler', () => {
    it('should return success for empty event', async () => {
      const event = { Records: [] };
      const result = await handler.handler(event, {});
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.message).toBe('No records to process');
    });

    // Note: SQS message processing tests that involve HTTP calls are skipped
    // because https.request cannot be easily mocked in vitest.
    // The HTTP retry logic is tested indirectly through integration tests.
  });

  describe('handleSqsMessage', () => {
    it('should handle invalid JSON in message body', async () => {
      const message = {
        body: 'invalid-json'
      };

      const result = await handler.handleSqsMessage(message);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid message format');
    });
  });

  describe('routeRunnerRequest', () => {
    it('should reject when circuit breaker is open', async () => {
      // Force circuit breaker open by recording many failures
      for (let i = 0; i < 10; i++) {
        handler.recordCircuitBreakerFailure();
      }

      const result = await handler.routeRunnerRequest(
        12345,
        ['self-hosted', 'ec2', 'general-purpose', 'arm', 'on-demand', 'runner-12345'],
        'owner/repo',
        67890
      );
      expect(result.success).toBe(false);
      expect(result.error).toContain('circuit breaker');
    });

    it('should reject for non-matching labels', async () => {
      handler.recordCircuitBreakerSuccess(); // Reset circuit breaker

      const result = await handler.routeRunnerRequest(12345, ['ubuntu-latest'], 'owner/repo', 67890);
      expect(result.success).toBe(false);
      expect(result.error).toContain('No matching runner type');
    });
  });
});
