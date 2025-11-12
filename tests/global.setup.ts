import fs from 'fs';
import { spawnSync } from 'child_process';

export default async function globalSetup() {
  const statePath = 'tests/auth/state.json';
  if (fs.existsSync(statePath)) {
    return;
  }
  console.log('🔐 No storage state found. Generating login state headlessly...');
  const env = { ...process.env, HEADLESS_LOGIN: '1' };
  const result = spawnSync('npx', ['tsx', 'scripts/save_login_state.ts'], {
    stdio: 'inherit',
    env,
    shell: process.platform === 'win32',
  });
  if (result.status !== 0 || !fs.existsSync(statePath)) {
    throw new Error('Failed to generate storage state for Playwright tests.');
  }
}


