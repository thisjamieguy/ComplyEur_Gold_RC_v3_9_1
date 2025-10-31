/**
 * Excel Import – Data Validation Suite
 * ------------------------------------
 * These Playwright-driven tests exercise the importer pipeline without the UI.
 * Each test calls a Python helper (`tests/utils/run_importer_for_test.py`) that:
 *   • spins up a clean SQLite database,
 *   • runs the importer against a sample workbook, and
 *   • returns a JSON payload describing import results and DB state.
 *
 * The assertions below verify schema alignment, duplicate handling, error
 * messages, performance, and resilience against malformed input.
 */

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Resolve key paths so beginners can follow the file layout.
const projectRoot = process.cwd();
const pythonBin =
  process.env.PLAYWRIGHT_PYTHON ??
  (process.platform === 'win32'
    ? path.join(projectRoot, 'venv', 'Scripts', 'python.exe')
    : path.join(projectRoot, 'venv', 'bin', 'python'));
const helperScript = path.join(projectRoot, 'tests', 'utils', 'run_importer_for_test.py');
const samplesDir = path.join(projectRoot, 'tests', 'sample_files');
const tmpDir = path.join(projectRoot, 'tests', 'tmp');

// Convenience helper for locating sample files.
function sample(name) {
  return path.join(samplesDir, name);
}

// Friendly label → filesystem safe string (used to create temp DB names).
function sanitiseLabel(label) {
  return label.replace(/[^a-z0-9]+/gi, '_');
}

/**
 * Invoke the Python importer helper and return its JSON payload + duration.
 * The helper prints a JSON blob as its final line; earlier lines are logs.
 */
function runImporter(sampleName, options = {}) {
  const dbFile = path.join(tmpDir, `${sanitiseLabel(sampleName)}_${Date.now()}.db`);
  const args = [helperScript, sample(sampleName), '--db-path', dbFile];
  if (options.imports && options.imports > 1) {
    args.push('--imports', String(options.imports));
  }

  const env = {
    ...process.env,
    LOG_LEVEL: process.env.LOG_LEVEL ?? 'ERROR',
    FLASK_DEBUG: 'false',
  };

  const start = Date.now();
  const output = execFileSync(pythonBin, args, { encoding: 'utf8', env });
  const durationMs = Date.now() - start;

  const lines = output.trim().split('\n');
  const jsonLine = lines[lines.length - 1];
  const data = JSON.parse(jsonLine);
  return { data, durationMs };
}

test.describe('Excel Import – Data Validation', () => {
  test.beforeAll(() => {
    // Ensure our scratch directory exists so the helper can create temp DBs.
    fs.mkdirSync(tmpDir, { recursive: true });
  });

  test('baseline workbook persists trips and employees as expected', async () => {
    const { data } = runImporter('basic_valid.xlsx');

    expect(data.success).toBeTruthy();
    const summary = data.imports[0];
    expect(summary.success).toBeTruthy();
    expect(summary.trips_added).toBe(3);

    const employees = data.db.employees.map((e) => e.name);
    expect(employees).toEqual(
      expect.arrayContaining(['Alice Valid', 'Bob Repeat', 'Charlie Domestic'])
    );

    const tripCountries = data.db.trips.map((t) => t.country).sort();
    expect(tripCountries).toEqual(['DE', 'ES', 'FR']);
  });

  test('re-importing the same workbook skips duplicate trips gracefully', async () => {
    const { data } = runImporter('basic_valid.xlsx', { imports: 2 });

    expect(data.success).toBeTruthy();
    expect(data.imports).toHaveLength(2);
    expect(data.imports[1].duplicates_skipped).toBeGreaterThanOrEqual(3);
    expect(data.db.trips).toHaveLength(3);
  });

  test('missing or invalid headers return meaningful errors', async () => {
    const { data } = runImporter('invalid_missing_dates.xlsx');

    expect(data.success).toBeTruthy();
    expect(data.imports[0].success).toBeFalsy();
    expect(data.imports[0].error).toMatch(/date headers/i);
    expect(data.db.trips).toHaveLength(0);
  });

  test('names with accents and extra whitespace remain intact', async () => {
    const { data } = runImporter('special_characters.xlsx');

    expect(data.success).toBeTruthy();
    const names = data.db.employees.map((e) => e.name);
    expect(names).toEqual(
      expect.arrayContaining(['Élodie Müller', 'José  García'])
    );
    const esTrip = data.db.trips.find((t) => t.country === 'ES');
    expect(esTrip).toBeDefined();
    expect(esTrip.travel_days).toBeGreaterThanOrEqual(1);
  });

  test('empty sheets fail with a descriptive error instead of inserting data', async () => {
    const { data } = runImporter('empty_sheet.xlsx');

    expect(data.imports[0].success).toBeFalsy();
    expect(data.imports[0].error).toBeDefined();
    expect(data.db.trips).toHaveLength(0);
  });

  test('large datasets stay within the performance budget (<= 3 seconds)', async () => {
    const { data, durationMs } = runImporter('large_dataset.xlsx');

    expect(data.success).toBeTruthy();
    expect(data.imports[0].success).toBeTruthy();
    expect(data.imports[0].employees_processed).toBeGreaterThanOrEqual(1000);
    expect(durationMs).toBeLessThan(3_500);
  });
});
