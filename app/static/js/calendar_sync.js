// # Phase 3.9 — Calendar synchronisation helpers
(function initCalendarSync(global) {
    'use strict';

    const PHASE_TAG = '[3.9-update-trip]';
    const JSON_HEADERS = {
        Accept: 'application/json',
        'Content-Type': 'application/json'
    };

    function toIsoDate(value) {
        if (value instanceof Date && !Number.isNaN(value.getTime())) {
            const year = String(value.getFullYear()).padStart(4, '0');
            const month = String(value.getMonth() + 1).padStart(2, '0');
            const day = String(value.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }
        if (typeof value === 'string') {
            return value.trim();
        }
        return '';
    }

    function normalisePayload(raw) {
        const payload = { ...(raw || {}) };
        if (payload.tripId && !payload.trip_id) {
            payload.trip_id = payload.tripId;
        }
        if (typeof payload.trip_id === 'string' && payload.trip_id.trim()) {
            const numericId = Number.parseInt(payload.trip_id, 10);
            if (Number.isFinite(numericId)) {
                payload.trip_id = numericId;
            }
        }
        if (payload.start_date instanceof Date) {
            payload.start_date = toIsoDate(payload.start_date);
        }
        if (payload.end_date instanceof Date) {
            payload.end_date = toIsoDate(payload.end_date);
        }
        return payload;
    }

    async function postJson(url, body) {
        if (typeof fetch !== 'function') {
            throw new Error(`${PHASE_TAG} Fetch API unavailable`);
        }
        const response = await fetch(url, {
            method: 'POST',
            headers: JSON_HEADERS,
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            let message = `${PHASE_TAG} Request failed (${response.status})`;
            try {
                const errorPayload = await response.json();
                if (errorPayload && typeof errorPayload.error === 'string') {
                    message = errorPayload.error;
                }
            } catch (parseError) {
                // Swallow JSON parse errors, retain fallback message.
            }
            throw new Error(message);
        }
        let payload;
        try {
            payload = await response.json();
        } catch (parseError) {
            throw new Error(`${PHASE_TAG} Invalid JSON response`);
        }
        if (payload && typeof payload.error === 'string') {
            throw new Error(payload.error);
        }
        return payload;
    }

    function emit(eventName, detail) {
        if (typeof document === 'undefined' || typeof CustomEvent !== 'function') {
            return;
        }
        try {
            document.dispatchEvent(new CustomEvent(eventName, { detail }));
        } catch (error) {
            console.warn(`${PHASE_TAG} Failed to dispatch ${eventName}`, error);
        }
    }

    const api = {
        async updateTrip(payload = {}) {
            const normalised = normalisePayload(payload);
            if (!Number.isFinite(normalised.trip_id)) {
                throw new Error(`${PHASE_TAG} trip_id is required`);
            }
            if (normalised.start_date) {
                normalised.start_date = toIsoDate(normalised.start_date);
            }
            if (normalised.end_date) {
                normalised.end_date = toIsoDate(normalised.end_date);
            }
            console.debug(`${PHASE_TAG} Posting update`, normalised);
            const response = await postJson('/api/update_trip', normalised);
            emit('calendar:sync:update', { tripId: normalised.trip_id, payload: response });
            return response;
        },
        async deleteTrip(payload = {}) {
            const normalised = normalisePayload(payload);
            if (!Number.isFinite(normalised.trip_id)) {
                throw new Error(`${PHASE_TAG} trip_id is required`);
            }
            console.debug(`${PHASE_TAG} Deleting trip`, normalised.trip_id);
            const response = await postJson('/api/delete_trip', { trip_id: normalised.trip_id });
            emit('calendar:sync:delete', { tripId: normalised.trip_id, payload: response });
            return response;
        },
        async duplicateTrip(payload = {}) {
            const normalised = normalisePayload(payload);
            if (!Number.isFinite(normalised.trip_id)) {
                throw new Error(`${PHASE_TAG} trip_id is required`);
            }
            const overrides = normalised.overrides && typeof normalised.overrides === 'object'
                ? normalised.overrides
                : {};
            console.debug(`${PHASE_TAG} Duplicating trip`, normalised.trip_id);
            const response = await postJson('/api/duplicate_trip', {
                trip_id: normalised.trip_id,
                overrides
            });
            emit('calendar:sync:duplicate', { tripId: normalised.trip_id, payload: response });
            return response;
        }
    };

    function attachController(controller) {
        if (!controller || controller.__calendarSyncAttached) {
            return controller;
        }
        controller.__calendarSyncAttached = true;

        const originalContextMenu = controller.handleTripContextMenu ? controller.handleTripContextMenu.bind(controller) : null;
        if (originalContextMenu) {
            controller.handleTripContextMenu = function patchedContextMenu(event) {
                const tripNode = event && event.target && typeof event.target.closest === 'function'
                    ? event.target.closest('.calendar-trip')
                    : null;
                const tripId = tripNode ? Number.parseInt(tripNode.getAttribute('data-trip-id') || '', 10) : null;
                emit('calendar:sync:context-open', { tripId });
                return originalContextMenu.call(this, event);
            };
        }

        const originalCloseContext = controller.closeContextMenu ? controller.closeContextMenu.bind(controller) : null;
        if (originalCloseContext) {
            controller.closeContextMenu = function patchedCloseContext(options) {
                const result = originalCloseContext.call(this, options);
                emit('calendar:sync:context-close', {
                    tripId: this && this.contextMenuState ? this.contextMenuState.tripId : null
                });
                return result;
            };
        }

        const originalUpdate = controller.updateTripDates ? controller.updateTripDates.bind(controller) : null;
        if (originalUpdate) {
            controller.updateTripDates = async function patchedUpdate(tripId, startDate, endDate) {
                emit('calendar:sync:drag-finalize', { tripId, startDate, endDate });
                return originalUpdate.call(this, tripId, startDate, endDate);
            };
        }

        console.info(`${PHASE_TAG} CalendarSync attached to controller`);
        return controller;
    }

    function bootstrapExistingController() {
        if (typeof document === 'undefined') {
            return null;
        }
        const root = document.getElementById('calendar');
        if (!root) {
            return null;
        }
        if (root.__calendarController) {
            return attachController(root.__calendarController);
        }
        return null;
    }

    function ensureInitWrapper(sync) {
        if (!global.CalendarApp || typeof global.CalendarApp.init !== 'function' || sync.__wrappedInit) {
            return;
        }
        const originalInit = global.CalendarApp.init.bind(global.CalendarApp);
        global.CalendarApp.init = function calendarSyncInit(root) {
            const controller = originalInit(root);
            attachController(controller);
            return controller;
        };
        sync.__wrappedInit = true;
    }

    const CalendarSync = global.CalendarSync || {};
    CalendarSync.api = api;
    CalendarSync.emit = emit;
    CalendarSync.attachController = attachController;
    CalendarSync.toIsoDate = toIsoDate;
    CalendarSync.bootstrapExistingController = bootstrapExistingController;
    CalendarSync.version = '3.9.0';
    CalendarSync.tag = PHASE_TAG;

    global.CalendarSync = CalendarSync;

    ensureInitWrapper(CalendarSync);
    bootstrapExistingController();
    if (typeof document !== 'undefined') {
        document.addEventListener('DOMContentLoaded', bootstrapExistingController, { once: true });
    }
})(typeof window !== 'undefined' ? window : globalThis);
