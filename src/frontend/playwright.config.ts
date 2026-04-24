import path from "node:path";

import { defineConfig, devices } from "@playwright/test";

const backendDirectory = path.resolve(__dirname, "../backend");

export default defineConfig({
  testDir: "./tests",
  testMatch: /.*\.e2e\.spec\.ts/,
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `uv run --directory "${backendDirectory}" uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:3000/prospects",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8000/api/v1",
      },
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
