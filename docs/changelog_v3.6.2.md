# Calendar Phase 3.6.2 Changelog

## Enhancements
- Added frame-aware scroll synchronisation: timeline header/body updates now run inside `requestAnimationFrame`, including vertical panel syncing and tooltip movement throttling.
- Cached day-cell template rows and consolidated batch DOM append, cutting calendar row render cost for 50+ employees / 200+ trips while keeping today-marker alignment accurate.
- Debounced employee search input (90 ms) and guarded event listener registration (`handlersBound`) to eliminate duplicate scroll/key listeners across re-renders.
- Introduced scroll styling updates (`scrollbar-gutter`, `contain`, `will-change`) to improve Safari/Edge smoothness and stop layout jitter under resize.
- Drag manager now defers `dragover` math with rAF, caches the latest pointer sample, and cancels pending frames on drop/cleanup for noticeably smoother overlays.

## Testing & Tooling
- Expanded Playwright coverage:
  - `tests/calendar_drag.spec.js` adds dataset integrity validation, frame jitter sampling, and opt-in drag visual snapshots.
  - `tests/calendar_scroll.spec.js` verifies listener hygiene, header/body alignment, large-dataset responsiveness, and optional timeline header snapshots.
  - `tests/calendar_interaction.spec.js` covers responsive resize behaviour, future-week “zoom”, and sequential detail selection consistency.
- Added shared helper for automated calendar login and fixture seeding, plus synthetic heavy-data loader for deterministic stress tests.

## Operational Notes
- Use `CALENDAR_VISUAL_SNAPSHOTS=1 npx playwright test` to regenerate baseline screenshots after UI tweaks.
- Large dataset tests rely on in-browser fixture injection; no backend seed required for QA runs.
- Manual smoke: `python3 run_local.py` → http://127.0.0.1:5001/calendar then verify scroll alignment, drag feedback, and detail overlays at multiple viewport sizes.
