import { defineConfig } from "vitest/config";
import path from "path";

const projectRoot = path.resolve(__dirname, "../../../..");
const testDir = path.resolve(projectRoot, "test/www/paths/home/post_deployment/integration");
const nodeModulesDir = path.resolve(__dirname, "node_modules");

export default defineConfig({
  server: {
    fs: {
      allow: [projectRoot],
    },
  },
  test: {
    alias: {
      "vitest": path.join(nodeModulesDir, "vitest"),
    },
    environment: "node",
    globals: true,
    include: [path.join(testDir, "**/*.test.ts")],
  },
});
