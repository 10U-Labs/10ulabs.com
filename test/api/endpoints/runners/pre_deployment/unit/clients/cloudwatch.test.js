import { describe, it, expect, beforeEach } from 'vitest';

describe('clients/cloudwatch', () => {
  let cloudwatchClient;

  beforeEach(async () => {
    cloudwatchClient = await import('clients/cloudwatch');
    cloudwatchClient.clearClient();
  });

  describe('getCloudWatchClient', () => {
    it('should create a CloudWatch client', () => {
      const client = cloudwatchClient.getCloudWatchClient();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = cloudwatchClient.getCloudWatchClient();
      const client2 = cloudwatchClient.getCloudWatchClient();
      expect(client1).toBe(client2);
    });
  });

  describe('clearClient', () => {
    it('should clear cached client', () => {
      const client1 = cloudwatchClient.getCloudWatchClient();
      cloudwatchClient.clearClient();
      const client2 = cloudwatchClient.getCloudWatchClient();
      expect(client1).not.toBe(client2);
    });
  });
});
