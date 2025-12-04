import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    exclude: ["src/__tests__/e2e/**", "node_modules/**"],
    globals: true,
    include: ["src/__tests__/unit/**/*.test.tsx"],
    setupFiles: ["./src/__tests__/unit/setup.ts"],
  },
});
