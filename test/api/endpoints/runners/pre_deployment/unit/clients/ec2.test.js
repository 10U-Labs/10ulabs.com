import { describe, it, expect, beforeEach } from 'vitest';

describe('clients/ec2', () => {
  let ec2Client;

  beforeEach(async () => {
    ec2Client = await import('clients/ec2');
    ec2Client.clearClient();
  });

  describe('getEC2Client', () => {
    it('should create an EC2 client', () => {
      const client = ec2Client.getEC2Client();
      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached client on subsequent calls', () => {
      const client1 = ec2Client.getEC2Client();
      const client2 = ec2Client.getEC2Client();
      expect(client1).toBe(client2);
    });
  });

  describe('clearClient', () => {
    it('should clear cached client', () => {
      const client1 = ec2Client.getEC2Client();
      ec2Client.clearClient();
      const client2 = ec2Client.getEC2Client();
      expect(client1).not.toBe(client2);
    });
  });
});
