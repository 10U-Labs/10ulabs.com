import { describe, it, expect, beforeEach } from 'vitest';

describe('clients/ssm', () => {
  let ssmClient;

  beforeEach(async () => {
    ssmClient = await import('clients/ssm');
    ssmClient.clearClient();
  });

  describe('getSSMClient', () => {
    it('should create an SSM client', () => {
      const client = ssmClient.getSSMClient();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = ssmClient.getSSMClient();
      const client2 = ssmClient.getSSMClient();
      expect(client1).toBe(client2);
    });
  });

  describe('clearClient', () => {
    it('should clear cached client', () => {
      const client1 = ssmClient.getSSMClient();
      ssmClient.clearClient();
      const client2 = ssmClient.getSSMClient();
      expect(client1).not.toBe(client2);
    });
  });
});
