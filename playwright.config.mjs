import {defineConfig, devices} from '@playwright/test';
/* Сторінки відкриваються як file:// — вони самодостатні, сервер не потрібен.
   dist/ має бути зібраний заздалегідь: npm run build. */
export default defineConfig({
  testDir: 'tests/pages',
  testMatch: /.*\.spec\.mjs$/,
  timeout: 120_000,
  fullyParallel: true,
  reporter: process.env.CI ? [['list'], ['github']] : 'list',
  use: {...devices['Desktop Chrome'], deviceScaleFactor: 1},
  projects: [{name: 'chromium'}],
});
