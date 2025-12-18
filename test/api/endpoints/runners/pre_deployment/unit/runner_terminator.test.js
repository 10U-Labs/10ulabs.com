import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mockClient } from 'aws-sdk-client-mock';
import { ECSClient, ListTasksCommand, DescribeTasksCommand, StopTaskCommand } from '@aws-sdk/client-ecs';
import { EC2Client, DescribeInstancesCommand, TerminateInstancesCommand } from '@aws-sdk/client-ec2';
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';

const ecsMock = mockClient(ECSClient);
const ec2Mock = mockClient(EC2Client);
const cloudwatchMock = mockClient(CloudWatchClient);

describe('runner_terminator', () => {
  let handler;

  beforeEach(async () => {
    vi.resetModules();
    ecsMock.reset();
    ec2Mock.reset();
    cloudwatchMock.reset();

    vi.stubEnv('ECS_CLUSTER', 'test-cluster');
    vi.stubEnv('EC2_MANAGED_BY_TAG', 'ec2-runner-api');

    // Mock CloudWatch for metrics
    cloudwatchMock.on(PutMetricDataCommand).resolves({});

    handler = await import('../../../../src/api/endpoints/runners/lambdas/runner_terminator.js');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  describe('findEcsTaskByRunId', () => {
    it('should return null when no ECS_CLUSTER is configured', async () => {
      vi.stubEnv('ECS_CLUSTER', '');
      vi.resetModules();
      const freshHandler = await import('../../../../src/api/endpoints/runners/lambdas/runner_terminator.js');
      const result = await freshHandler.findEcsTaskByRunId(12345);
      expect(result).toBeNull();
    });

    it('should return null when runId is not provided', async () => {
      const result = await handler.findEcsTaskByRunId(null);
      expect(result).toBeNull();
    });

    it('should return null when no tasks found', async () => {
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      const result = await handler.findEcsTaskByRunId(12345);
      expect(result).toBeNull();
    });

    it('should find task by RunId tag', async () => {
      ecsMock.on(ListTasksCommand).resolves({
        taskArns: ['arn:aws:ecs:us-east-1:123456789:task/test-cluster/abc123']
      });
      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-1:123456789:task/test-cluster/abc123',
          tags: [
            { key: 'RunId', value: '12345' },
            { key: 'Name', value: 'runner-test' }
          ]
        }]
      });

      const result = await handler.findEcsTaskByRunId(12345);
      expect(result).toEqual({
        taskArn: 'arn:aws:ecs:us-east-1:123456789:task/test-cluster/abc123',
        runnerName: 'runner-test',
        tags: { RunId: '12345', Name: 'runner-test' }
      });
    });
  });

  describe('findEc2InstanceByRunId', () => {
    it('should return null when no EC2_MANAGED_BY_TAG is configured', async () => {
      vi.stubEnv('EC2_MANAGED_BY_TAG', '');
      vi.resetModules();
      const freshHandler = await import('../../../../src/api/endpoints/runners/lambdas/runner_terminator.js');
      const result = await freshHandler.findEc2InstanceByRunId(12345);
      expect(result).toBeNull();
    });

    it('should return null when runId is not provided', async () => {
      const result = await handler.findEc2InstanceByRunId(null);
      expect(result).toBeNull();
    });

    it('should find instance by RunId tag', async () => {
      ec2Mock.on(DescribeInstancesCommand).resolves({
        Reservations: [{
          Instances: [{
            InstanceId: 'i-1234567890abcdef0',
            Tags: [
              { Key: 'RunId', Value: '12345' },
              { Key: 'Name', Value: 'runner-test' },
              { Key: 'ManagedBy', Value: 'ec2-runner-api' }
            ]
          }]
        }]
      });

      const result = await handler.findEc2InstanceByRunId(12345);
      expect(result).toEqual({
        instanceId: 'i-1234567890abcdef0',
        runnerName: 'runner-test',
        tags: { RunId: '12345', Name: 'runner-test', ManagedBy: 'ec2-runner-api' }
      });
    });

    it('should return null when no matching instances found', async () => {
      ec2Mock.on(DescribeInstancesCommand).resolves({
        Reservations: []
      });

      const result = await handler.findEc2InstanceByRunId(12345);
      expect(result).toBeNull();
    });
  });

  describe('stopEcsTask', () => {
    it('should return false when no ECS_CLUSTER is configured', async () => {
      vi.stubEnv('ECS_CLUSTER', '');
      vi.resetModules();
      const freshHandler = await import('../../../../src/api/endpoints/runners/lambdas/runner_terminator.js');
      const result = await freshHandler.stopEcsTask('task-arn', 'test reason');
      expect(result).toBe(false);
    });

    it('should stop ECS task successfully', async () => {
      ecsMock.on(StopTaskCommand).resolves({});

      const result = await handler.stopEcsTask('task-arn', 'test reason');
      expect(result).toBe(true);
    });

    it('should handle already stopped tasks gracefully', async () => {
      const error = new Error('TaskNotFound');
      error.name = 'InvalidParameterException';
      ecsMock.on(StopTaskCommand).rejects(error);

      const result = await handler.stopEcsTask('task-arn', 'test reason');
      expect(result).toBe(true);
    });
  });

  describe('terminateEc2Instance', () => {
    it('should terminate EC2 instance successfully', async () => {
      ec2Mock.on(TerminateInstancesCommand).resolves({});

      const result = await handler.terminateEc2Instance('i-1234567890', 'test reason');
      expect(result).toBe(true);
    });

    it('should handle already terminated instances gracefully', async () => {
      const error = new Error('InvalidInstanceID.NotFound');
      error.Code = 'InvalidInstanceID.NotFound';
      ec2Mock.on(TerminateInstancesCommand).rejects(error);

      const result = await handler.terminateEc2Instance('i-1234567890', 'test reason');
      expect(result).toBe(true);
    });
  });

  describe('terminateRunnerByRunId', () => {
    it('should terminate ECS task when found', async () => {
      ecsMock.on(ListTasksCommand).resolves({
        taskArns: ['arn:aws:ecs:us-east-1:123456789:task/test-cluster/abc123']
      });
      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-1:123456789:task/test-cluster/abc123',
          tags: [{ key: 'RunId', value: '12345' }]
        }]
      });
      ecsMock.on(StopTaskCommand).resolves({});

      const result = await handler.terminateRunnerByRunId(12345, 'cancelled', 99);
      expect(result.success).toBe(true);
      expect(result.type).toBe('ecs');
    });

    it('should terminate EC2 instance when ECS task not found', async () => {
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      ec2Mock.on(DescribeInstancesCommand).resolves({
        Reservations: [{
          Instances: [{
            InstanceId: 'i-1234567890abcdef0',
            Tags: [{ Key: 'RunId', Value: '12345' }]
          }]
        }]
      });
      ec2Mock.on(TerminateInstancesCommand).resolves({});

      const result = await handler.terminateRunnerByRunId(12345, 'cancelled', 99);
      expect(result.success).toBe(true);
      expect(result.type).toBe('ec2');
    });

    it('should return success with type none when no runner found', async () => {
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.terminateRunnerByRunId(12345, 'cancelled', 99);
      expect(result.success).toBe(true);
      expect(result.type).toBe('none');
    });
  });

  describe('handleCancellationMessage', () => {
    it('should process valid cancellation message', async () => {
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const message = {
        body: JSON.stringify({
          action: 'cancelled',
          job_id: 99,
          run_id: 12345,
          runner_name: 'runner-test'
        })
      };

      const result = await handler.handleCancellationMessage(message);
      expect(result.success).toBe(true);
    });

    it('should skip message without run_id', async () => {
      const message = {
        body: JSON.stringify({
          action: 'cancelled',
          job_id: 99
        })
      };

      const result = await handler.handleCancellationMessage(message);
      expect(result.success).toBe(true);
      expect(result.skipped).toBe(true);
      expect(result.reason).toBe('no_run_id');
    });

    it('should handle invalid JSON in message body', async () => {
      const message = {
        body: 'invalid-json'
      };

      const result = await handler.handleCancellationMessage(message);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid message format');
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

    it('should process cancellation messages', async () => {
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const event = {
        Records: [{
          eventSource: 'aws:sqs',
          body: JSON.stringify({
            action: 'cancelled',
            job_id: 99,
            run_id: 12345
          })
        }]
      };

      const result = await handler.handler(event, {});
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.success).toBe(1);
    });
  });
});
