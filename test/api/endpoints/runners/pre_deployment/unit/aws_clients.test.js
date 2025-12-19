import { describe, it, expect, beforeEach } from 'vitest';

describe('aws_clients', () => {
  let awsClients;

  beforeEach(async () => {
    awsClients = await import('runners-layer/aws_clients.js');
    awsClients.clearClients();
  });

  describe('getECSClient', () => {
    it('should create an ECS client', () => {
      const client = awsClients.getECSClient();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = awsClients.getECSClient();
      const client2 = awsClients.getECSClient();
      expect(client1).toBe(client2);
    });
  });

  describe('getEC2Client', () => {
    it('should create an EC2 client', () => {
      const client = awsClients.getEC2Client();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = awsClients.getEC2Client();
      const client2 = awsClients.getEC2Client();
      expect(client1).toBe(client2);
    });
  });

  describe('getCloudWatchClient', () => {
    it('should create a CloudWatch client', () => {
      const client = awsClients.getCloudWatchClient();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = awsClients.getCloudWatchClient();
      const client2 = awsClients.getCloudWatchClient();
      expect(client1).toBe(client2);
    });
  });

  describe('getSSMClient', () => {
    it('should create an SSM client', () => {
      const client = awsClients.getSSMClient();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = awsClients.getSSMClient();
      const client2 = awsClients.getSSMClient();
      expect(client1).toBe(client2);
    });
  });

  describe('clearClients', () => {
    it('should clear all cached clients', () => {
      const ecs1 = awsClients.getECSClient();
      const ec2_1 = awsClients.getEC2Client();

      awsClients.clearClients();

      const ecs2 = awsClients.getECSClient();
      const ec2_2 = awsClients.getEC2Client();

      expect(ecs1).not.toBe(ecs2);
      expect(ec2_1).not.toBe(ec2_2);
    });

    it('should allow recreation of all client types', () => {
      awsClients.getECSClient();
      awsClients.getEC2Client();
      awsClients.getCloudWatchClient();
      awsClients.getSSMClient();

      awsClients.clearClients();

      const newEcs = awsClients.getECSClient();
      expect(newEcs).toBeDefined();
      expect(typeof newEcs.send).toBe('function');
    });
  });
});
