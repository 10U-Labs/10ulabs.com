import { vi, beforeEach, afterEach } from 'vitest';
import path from 'path';
import Module from 'module';

// Intercept require for /opt/nodejs paths and AWS SDK paths
const REPO_ROOT = path.resolve(import.meta.dirname, '../../../..');
const LAYERS_PATH = path.join(REPO_ROOT, 'src/api/endpoints/runners/lambdas/layers');
const CLIENTS_PATH = path.join(LAYERS_PATH, 'clients');
const COMMON_PATH = path.join(LAYERS_PATH, 'common');
const TEST_NODE_MODULES = path.join(import.meta.dirname, 'node_modules');

const originalResolveFilename = Module._resolveFilename;
Module._resolveFilename = function(request, parent, isMain, options) {
  // Redirect client layers
  if (request === '/opt/nodejs/clients/ecs') {
    return originalResolveFilename.call(this, path.join(CLIENTS_PATH, 'ecs'), parent, isMain, options);
  }
  if (request === '/opt/nodejs/clients/ec2') {
    return originalResolveFilename.call(this, path.join(CLIENTS_PATH, 'ec2'), parent, isMain, options);
  }
  if (request === '/opt/nodejs/clients/cloudwatch') {
    return originalResolveFilename.call(this, path.join(CLIENTS_PATH, 'cloudwatch'), parent, isMain, options);
  }
  if (request === '/opt/nodejs/clients/ssm') {
    return originalResolveFilename.call(this, path.join(CLIENTS_PATH, 'ssm'), parent, isMain, options);
  }

  // Redirect common layer
  if (request === '/opt/nodejs/common') {
    return originalResolveFilename.call(this, COMMON_PATH, parent, isMain, options);
  }

  // For ALL AWS SDK requires, use test's node_modules so mocks work
  if (request.startsWith('@aws-sdk/')) {
    try {
      const resolved = path.join(TEST_NODE_MODULES, request);
      return originalResolveFilename.call(this, resolved, parent, isMain, options);
    } catch {
      // Fall through to default resolution
    }
  }

  return originalResolveFilename.call(this, request, parent, isMain, options);
};

// Reset all mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
  vi.unstubAllEnvs();
  // Re-stub default environment variables after unstubbing
  vi.stubEnv('AWS_REGION', 'us-east-2');
  vi.stubEnv('NODE_ENV', 'test');
  vi.stubEnv('ETC_PATH', path.join(REPO_ROOT, 'etc'));
});

// Clean up after each test
afterEach(() => {
  vi.resetModules();
});

// Default environment variables for tests
vi.stubEnv('AWS_REGION', 'us-east-2');
vi.stubEnv('NODE_ENV', 'test');
vi.stubEnv('ETC_PATH', path.join(REPO_ROOT, 'etc'));
