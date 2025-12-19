import { defineConfig } from 'vitest/config';
import path from 'path';

const REPO_ROOT = path.resolve(import.meta.dirname, '../../../..');
const LAMBDAS_PATH = path.join(REPO_ROOT, 'src/api/endpoints/runners/lambdas');
const LAYERS_PATH = path.join(LAMBDAS_PATH, 'layers');
const CLIENTS_PATH = path.join(LAYERS_PATH, 'clients');
const COMMON_PATH = path.join(LAYERS_PATH, 'common');

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./setup.js'],
    include: ['pre_deployment/unit/**/*.test.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
  resolve: {
    alias: {
      // Client layers
      'clients/ecs': path.join(CLIENTS_PATH, 'ecs'),
      'clients/ec2': path.join(CLIENTS_PATH, 'ec2'),
      'clients/cloudwatch': path.join(CLIENTS_PATH, 'cloudwatch'),
      'clients/ssm': path.join(CLIENTS_PATH, 'ssm'),
      '/opt/nodejs/clients/ecs': path.join(CLIENTS_PATH, 'ecs'),
      '/opt/nodejs/clients/ec2': path.join(CLIENTS_PATH, 'ec2'),
      '/opt/nodejs/clients/cloudwatch': path.join(CLIENTS_PATH, 'cloudwatch'),
      '/opt/nodejs/clients/ssm': path.join(CLIENTS_PATH, 'ssm'),
      // Common layer
      common: COMMON_PATH,
      '/opt/nodejs/common': COMMON_PATH,
      // Lambda source
      lambdas: LAMBDAS_PATH,
    },
  },
});
