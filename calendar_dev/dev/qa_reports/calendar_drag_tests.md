# ComplyEur Calendar Drag QA Report

_Date_: 11 Nov 2025  
_Tools_: Playwright 1.56.1 (Chromium 119.0.6045.105 / WebKit 18.0)

## Test Matrix

| Area | Test Result | Bug? | Root Cause | Suggested Fix |
| --- | --- | --- | --- | --- |
| Trip rendering & lane board | PASS (Chromium/WebKit) | – | Static dataset hydrates correctly; 4 employees rendered with proper handles. | None. |
| Drag move (BUG‑001 spec) | PASS (Chromium/WebKit) | – | Drag mutations now persist via `localStorage` (dev) while still updating the in-memory timeline immediately. Reloading respects the saved data. | Optional: back REST endpoint instead of `localStorage`; render trips as single spans for clarity. |
| Start-edge resize (BUG‑002 spec) | PASS | – | Handles close/open as expected; DOM snapshots show the left handle moving from 12 → 9. | None. |
| End-edge resize (BUG‑003 spec) | PASS | – | Right handle correctly moves to new end date. | None. |
| Drag-to-create trips | PASS | – | Highlight, modal, and data insertions succeed. | Persist created trips server-side. |
| Visual feedback (preview + lane highlighting) | PASS | – | `.trip-preview` ghosts and `.lane-preview` toggles work after hover adjustments. | None. |
| Stress & virtualization stability | PASS (Chromium/WebKit) | – | Added `window.__virtualizationProbe` instrumentation during drag preview so tests confirm `visibleDays.length` and rendered `.day-cell` counts never change mid-drag. | Keep probe dev-only; optionally surface to prod telemetry. |

## Methodology

* Served `dev/calendar_dev.html` through the Playwright web server and injected `window.__CALENDAR_SANDBOX_TRIPS` to avoid fetch noise.
* Authored `tests/calendar_interactions.spec.js` covering render assertions, drag, resize, drag-to-create, HUD feedback, virtualization guard, and a 50-cycle stress run across Chromium and WebKit. Pointer interactions now route exclusively through synthetic `PointerEvent`s (no `page.mouse` shortcuts) to match Safari/WebKit capture semantics.
* Captured console output, pointer snapshots, DOM state dumps, virtualization probe payloads, traces, videos, and targeted screenshots per test under `dev/qa_reports/logs` and `dev/qa_reports/screenshots`.
* Final run command: `npx playwright test` (Chromium + WebKit, headless). Execution time ~90s; all scenarios now pass.

## Detailed Findings

### 1. Drag interactions persist for the current session (BUG‑001 resolved)
* **Repro**: drag “Jonas · Spain” from 12–28 May to start on 18 May (Chromium/WebKit). Reload the page – data now sticks thanks to the new `localStorage` sync.
* **Evidence**: `dev/qa_reports/logs/bug_001_dragging_trips_should_persist_new_start_end_dates_*_bug_001_dom_state.json` shows the source cell cleared and the target cell marked `trip-pill-start`; matching screenshots live in `dev/qa_reports/screenshots`.
* **Remaining work**: For production we should replace the `localStorage` layer with the real API and consider rendering each trip as a single CSS grid span for better visual feedback.

### 2. Keyboard resizing uses inverted semantics
* **Finding**: In `DragController.handleKeydown`, `Shift+ArrowUp` calls `handleKeyboardResize(..., 'start', 1)` which moves the start _later_ and `Shift+ArrowDown` moves the end earlier. This is unintuitive (Up should expand earlier, Down later) and makes fine adjustments error-prone.
* **Fix**: swap the start/end deltas for the Up/Down branches so Up decreases start date and Down increases end date.

### 3. Drag-to-create still lacks conflict handling
* **Finding**: Drag-to-create now persists via the same storage helper, but it still doesn’t validate overlaps or enforce limits, so conflicting trips can be created.
* **Fix**: Add validation (duration checks, overlap constraints) before persisting and surface errors in the modal.

### 4. Virtualization telemetry now available
* **Finding**: WebKit’s pointer stack skipped several `page.mouse` events, making it impossible to assert that virtualization never re-trimmed the grid mid-drag.
* **Fix**: Added a dev-only hook (`window.__virtualizationProbe`) inside `handleInteractionPreview()`; the Playwright case subscribes to the hook and asserts `visibleLength`/`cellCount` remain static for the entire drag. No production side-effects because the hook is undefined outside tests.
* **Next**: Consider promoting the probe to structured logs if we ever enable real virtualization (e.g., month virtualization) so we can catch regressions from prod telemetry.

### 5. Observability improvements (still recommended)
* Console logs capture only favicon 404s, but there is no telemetry around drag lifecycles (start/move/commit). Adding structured logging around `calculatePreview` and `applyDragResult` plus dev-only HUD toggles would make diagnosing pointer math issues easier in the future.

## Artifacts

* **Screenshots**: `dev/qa_reports/screenshots/bug_001_dragging_trips_should_persist_new_start_end_dates_*` (movement attempt), `...bug_002...`, `...bug_003...`.
* **Logs & DOM snapshots**: `dev/qa_reports/logs/*.log`, `*.json` (state before/after, DOM handle presence, pointer traces).
* **Playwright traces/videos**: `playwright-test-results/**/trace.zip` & `video.webm` for each scenario (open with `npx playwright show-trace ...`).

## Next Steps

1. Replace the interim `localStorage` persistence with the real backend API (retain tests by mocking fetch).
2. Rework `renderCalendar` so each trip renders once with a column span instead of duplicating pills per day; that will make drag/resizes visually obvious and simplify DOM assertions.
3. Fix the keyboard-resize inversion and add regression tests for it.
4. Keep the new Playwright suite under `tests/calendar_interactions.spec.js` in CI; it already covers Chromium + WebKit and writes rich diagnostics for future regressions.
