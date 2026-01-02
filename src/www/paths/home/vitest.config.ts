import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react-swc";
import path from "path";

const projectRoot = path.resolve(__dirname, "../../../..");
const srcDir = path.resolve(__dirname, "./src");
const testDir = path.resolve(projectRoot, "test/www/paths/home/pre_deployment/unit");
const nodeModulesDir = path.resolve(__dirname, "node_modules");

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": srcDir,
    },
  },
  server: {
    fs: {
      allow: [projectRoot],
    },
  },
  test: {
    alias: {
      "@testing-library/jest-dom": path.join(nodeModulesDir, "@testing-library/jest-dom"),
      "@testing-library/react": path.join(nodeModulesDir, "@testing-library/react"),
      "@testing-library/user-event": path.join(nodeModulesDir, "@testing-library/user-event"),
      "@tanstack/react-query": path.join(nodeModulesDir, "@tanstack/react-query"),
      "react-router-dom": path.join(nodeModulesDir, "react-router-dom"),
      "react-dom": path.join(nodeModulesDir, "react-dom"),
      "react": path.join(nodeModulesDir, "react"),
      "vitest": path.join(nodeModulesDir, "vitest"),
    },
    environment: "jsdom",
    exclude: ["node_modules/**"],
    globals: true,
    include: [path.join(testDir, "**/*.test.tsx")],
    setupFiles: [path.join(testDir, "setup.ts")],
  },
});
