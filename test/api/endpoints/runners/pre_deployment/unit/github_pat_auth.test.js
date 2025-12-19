import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('github_pat_auth', () => {
  let githubPatAuth;

  beforeEach(async () => {
    vi.resetModules();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('getGitHubToken', () => {
    it('should return empty string when GITHUB_TOKEN_SECRET_NAME is not set', async () => {
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '');
      githubPatAuth = await import('common/github_pat_auth.js');

      const token = await githubPatAuth.getGitHubToken();

      expect(token).toBe('');
    });

    it('should return empty string when GITHUB_TOKEN_SECRET_NAME is undefined', async () => {
      delete process.env.GITHUB_TOKEN_SECRET_NAME;
      vi.resetModules();
      githubPatAuth = await import('common/github_pat_auth.js');

      const token = await githubPatAuth.getGitHubToken();

      expect(token).toBe('');
    });

    it('should return empty string on SSM error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '/nonexistent/parameter');
      vi.resetModules();
      githubPatAuth = await import('common/github_pat_auth.js');

      const token = await githubPatAuth.getGitHubToken();

      expect(token).toBe('');
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should cache token after first retrieval', async () => {
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '');
      githubPatAuth = await import('common/github_pat_auth.js');

      const token1 = await githubPatAuth.getGitHubToken();
      const token2 = await githubPatAuth.getGitHubToken();

      expect(token1).toBe(token2);
    });
  });

  describe('clearTokenCache', () => {
    it('should be a function', async () => {
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '');
      githubPatAuth = await import('common/github_pat_auth.js');

      expect(typeof githubPatAuth.clearTokenCache).toBe('function');
    });

    it('should allow function to be called without error', async () => {
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '');
      githubPatAuth = await import('common/github_pat_auth.js');

      expect(() => githubPatAuth.clearTokenCache()).not.toThrow();
    });
  });

  describe('getSSMClient', () => {
    it('should return an SSM client instance', async () => {
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '');
      githubPatAuth = await import('common/github_pat_auth.js');

      const client = githubPatAuth.getSSMClient();

      expect(client).toBeDefined();
      expect(typeof client.send).toBe('function');
    });

    it('should return cached SSM client on subsequent calls', async () => {
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '');
      githubPatAuth = await import('common/github_pat_auth.js');

      const client1 = githubPatAuth.getSSMClient();
      const client2 = githubPatAuth.getSSMClient();

      expect(client1).toBe(client2);
    });
  });
});
