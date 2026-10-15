import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
const proxy = {
  "/api": {
    target: "http://127.0.0.1:8000",
    rewrite: (path: string) => path.replace(/^\/api/, ""),
  },
};
export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
  test: {
    exclude: ["e2e/**", "node_modules/**"],
    environment: "jsdom",
    setupFiles: "./src/test-setup.ts",
    globals: true,
  },
});
