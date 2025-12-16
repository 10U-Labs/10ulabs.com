import { vi, beforeEach, afterEach } from 'vitest';
import path from 'path';
import Module from 'module';

// Intercept require for /opt/nodejs/runners-layer and AWS SDK paths
const REPO_ROOT = path.resolve(import.meta.dirname, '../../../..');
const LAYER_PATH = path.join(REPO_ROOT, 'src/api/endpoints/runners/lambdas/layer');
const TEST_NODE_MODULES = path.join(import.meta.dirname, 'node_modules');

const originalResolveFilename = Module._resolveFilename;
Module._resolveFilename = function(request, parent, isMain, options) {
  // Redirect /opt/nodejs/runners-layer to the actual layer
  if (request === '/opt/nodejs/runners-layer') {
    return originalResolveFilename.call(this, LAYER_PATH, parent, isMain, options);
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
});

// Clean up after each test
afterEach(() => {
  vi.resetModules();
});

// Default environment variables for tests
vi.stubEnv('AWS_REGION', 'us-east-2');
vi.stubEnv('NODE_ENV', 'test');
