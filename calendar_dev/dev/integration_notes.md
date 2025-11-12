# ComplyEur Calendar – Integration Notes

## 1. Data Loading
- Replace the `fetch('calendar_mock_data.json')` call inside `loadTrips()` with `fetch('/api/trips')` (or equivalent Flask route). Expect the same payload shape as the mock JSON.
- Ensure the Flask endpoint returns ISO-8601 strings for `start_date` and `end_date` so the existing normaliser keeps working.
- Consider caching responses or passing the trip data via a `<script type="application/json">` block when server-side rendering to avoid an extra network request.

## 2. Mutations (Add / Edit / Delete)
- Wire `handleFormSubmit` to POST/PUT requests: on `this.mode === 'edit'`, send `PUT /api/trips/<id>`; on create, `POST /api/trips`.
- On success, refresh the local state by refetching trips or by updating the in-memory array with the server response (which should include the canonical `id`).
- Connect `handleDelete` to `DELETE /api/trips/<id>` prior to removing the trip client-side.
- Surface API errors in the modal (inline message) so the user understands when a save fails.

## 3. Flask Template Injection
- Move the markup from `dev/calendar_dev.html` into `templates/calendar.html`. Keep the shell structure: header, grid, and sidebar container IDs are referenced by the JS modules.
- Serve `calendar_styles.css`, `calendar_dev.js`, and `calendar_sidebar.js` from `static/`. Update `<link>`/`<script>` paths to use `url_for('static', filename='...')`.
- Ensure the script tag stays `type="module"` so the ES module import between `calendar_dev.js` and `calendar_sidebar.js` continues to work.

## 4. Flask Blueprint Hookup
- Add a dedicated blueprint/view (e.g., `@calendar_bp.route('/calendar')`) that renders the new template.
- Optionally pass the user’s default month/year or pre-fetched trips via Jinja globals for faster first paint.

## 5. Testing Checklist
- Validate rolling 180-day totals by comparing the UI output with a known dataset.
- Verify month navigation, drag-to-add, edit/delete, and tooltip interactions after the Flask wiring.
- Confirm CSRF handling on POST/PUT/DELETE if the Flask app enables CSRF protection.

## 6. Phase 3.10 Drag & Resize Patch
- **True root cause:** when the calendar re-rendered trips it stored UUID strings in `data-trip-id`, but `attachTripInteractions()` coerced the attribute with `Number(...)`. As soon as IDs stopped being numeric, every lookup returned `NaN`, so the drag listeners never attached and the reducer never saw a commit.
- **Fix:** keep IDs as strings end-to-end and update the `DragController` preview pipeline so it captures the pointer, normalises coordinates, preserves the last valid grid hit, and only commits once on pointer up. Lane targeting now keys off `.employee-lane[data-employee-id]` via `elementFromPoint`, the ghost preview mirrors the final reducer payload, and keyboard fallbacks sit behind the `ENABLE_TRIP_DND` feature flag.
- **UX & Testing:** Added resize handles, lane preview highlight, a toggleable debug HUD, and the `dev/calendar_sandbox.html` harness with stub trips. Playwright coverage (`tests/ui/calendar-dnd.spec.ts`) locks down move, resize, cross-lane drops, bounds guards, and keyboard flows.

## 7. Renderer Contract
- `CalendarApp.render()` now snapshots immutable state via `createRenderState()` and delegates to `renderCalendar(state)` so that every render derives purely from state instead of mutating DOM mid-flight.
- List/grid metadata (`visibleDays`, `dayIndexByISO`, cell metrics) are recomputed during render and cached for interaction math; mutations flow exclusively through `commitTripUpdate → applyDragResult → render()`.
- Any external caller should use the exported helpers (`bootstrapCalendar`, `renderCalendar`, `addTrip`, `updateSidebar`) rather than poking DOM directly—each helper recomputes state and schedules a full render.

## 8. Interaction Manager API
- `dev/interaction/InteractionManager.js` encapsulates the pointer FSM with states `idle`, `dragging`, `resizing_left`, `resizing_right`, `committing`.
- Constructor dependencies: `getCalendarRect`, `clientXToCellIndex`, `commitTripUpdate`, `addDays`, optional `onPreview` & `onStateChange`.
- Public methods:
  - `beginDrag(tripId, clientX, meta)` and `beginResize(tripId, edge, clientX, meta)` prime the state machine with `{ startTrip, snapWidthPx }`.
  - `updatePointer(clientX)` rAF-throttles pointer deltas and emits preview payloads `{ nextStartDate, nextEndDate, range, deltaDays }`.
- `commit()` computes the snapped date delta and calls the provided `commitTripUpdate`.
- `cancel()` aborts without committing and clears any preview callbacks.

## 9. QA Matrix (Drag/Resize)
| Root Cause | Fix | Playwright Coverage |
| --- | --- | --- |
| Pointer math depended on `elementFromPoint`, so once the cursor left the grid the controller reused stale day indexes and `shouldCommit` returned `false`, leaving trips unmoved. | InteractionManager snaps clientX to cached cell indexes via `clientXToCellIndex()` and commits deltas independent of DOM hit-testing. | `tests/calendar/drag_resize.spec.ts` cases A, B, F. |
| DOM mutated pills directly during preview; a re-render before `pointerup` replaced nodes and the underlying state never changed. | Introduced DOM-first proxy overlay + `commitTripUpdate()` so only the proxy moves during drag and state updates atomically on commit. | Cases C, D, J verify resize + overlap + virtualization stability. |
| Geometry ignored scroll offsets, devicePixelRatio, and zoom, so drags at non-100% zoom or during scroll dropped in the wrong day. | `getCalendarRect()` caches scroller bounds (including `scrollLeft/Top` and DPR) and `clientXToCellIndex` normalises coordinates before snapping. | Cases E, G, H, I cover scroll, zoom, touch, and RTL scenarios. |
| WebKit pointer synthesis via `page.mouse` skipped the browser’s capture stack, so tests couldn’t see mid-drag state and virtualization regressions went undetected. | Added optional instrumentation hook `window.__virtualizationProbe` that fires from `handleInteractionPreview()` and logs `visibleLength`/`cellCount` snapshots without mutating prod code; Playwright now records these samples while using the same pointer API as real users. | Case J asserts both `visibleLength` and DOM cell count stay constant throughout the drag. |

## 10. Instrumentation Hooks
- `window.__virtualizationProbe(payload)` – if defined, `handleInteractionPreview()` calls it every frame with `{ visibleLength, cellCount, active }`. The hook is no-op in production, but tests can collect snapshots while the drag proxy runs.
- `window.calendarAppInstance` – already exposed via `bootstrapCalendar`. Tests rely on `pointToCellIndex()` and `dayIndexByISO` for sanity checks at different zoom levels. Keep this binding when moving into Flask.
