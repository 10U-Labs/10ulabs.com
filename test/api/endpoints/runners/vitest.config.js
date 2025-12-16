import { defineConfig } from 'vitest/config';
import path from 'path';

const REPO_ROOT = path.resolve(import.meta.dirname, '../../../..');
const LAMBDAS_PATH = path.join(REPO_ROOT, 'src/api/endpoints/runners/lambdas');
const LAYER_PATH = path.join(LAMBDAS_PATH, 'layer');

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
      'runners-layer': LAYER_PATH,
      lambdas: LAMBDAS_PATH,
      '/opt/nodejs/runners-layer': LAYER_PATH,
    },
  },
});
