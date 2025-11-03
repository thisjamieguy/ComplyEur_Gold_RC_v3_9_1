# Calendar Phase 3.6.3 Changelog

## Inline Layout & Cleanup
- Removed legacy references to the floating calendar shell; the calendar now renders only inside the dashboard container with refreshed spacing and shadow treatment.
- Responsive refinements collapse the employee list and timeline into a single column on tablet/mobile widths, keeping controls accessible without a pop-out view.

## Risk Layer Enhancements
- Added a rolling 90-day risk model with new palettes (`#4CAF50`, `#FFC107`, `#F44336`) and per-day heat mapping.
- Trip blocks now read from live risk data and display a gradient background plus dataset attributes for downstream integrations.
- Implemented `calculateRiskColor(employeeId, date)` + caching to surface risk insights to both day cells and trip tooltips.
- Introduced dynamic tooltips that surface “Days used: XX / 90” with accent bars and 120ms fade, supporting both trips and empty day cells.

## Styling & UX Polish
- Trip pills adopt 6px radii, softer elevation, and responsive typography for a more modern look.
- Day cells expose risk highlights with subtle gradients and inset indicators keyed to the compliance threshold they represent.
- Tooltip and calendar shell styling align with the ComplyEur visual system while remaining lightweight and inline.

## Testing & Tooling
- Added `tests/calendar_color.spec.js` to validate risk colour thresholds, tooltip content, drag integrity, and idle FPS (>55).
- Updated the phase automation script to `scripts/run_phase_3.6.3_tests.sh`, executing the new colour suite alongside existing interaction checks.
- QA helpers gained a shared navigation bootstrap to keep fixture injection consistent across specs.

## Performance & Accessibility
- Tooltip movement and scroll synchronisation are throttled through `requestAnimationFrame`, avoiding forced reflows under load.
- Each risk cell carries an ARIA label and dataset attributes for screen-reader compatibility and automation hooks.
