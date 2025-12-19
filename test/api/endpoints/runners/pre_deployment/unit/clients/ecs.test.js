import { describe, it, expect, beforeEach } from 'vitest';

describe('clients/ecs', () => {
  let ecsClient;

  beforeEach(async () => {
    ecsClient = await import('clients/ecs');
    ecsClient.clearClient();
  });

  describe('getECSClient', () => {
    it('should create an ECS client', () => {
      const client = ecsClient.getECSClient();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = ecsClient.getECSClient();
      const client2 = ecsClient.getECSClient();
      expect(client1).toBe(client2);
    });
  });

  describe('clearClient', () => {
    it('should clear cached client', () => {
      const client1 = ecsClient.getECSClient();
      ecsClient.clearClient();
      const client2 = ecsClient.getECSClient();
      expect(client1).not.toBe(client2);
    });
  });
});
