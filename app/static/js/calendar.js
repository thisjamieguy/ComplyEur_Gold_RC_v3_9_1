// Phase 3.6.1 — Drag-and-Drop Interaction — Verified ✅
(function (global) {
    'use strict';

    const DAY_IN_MS = 86_400_000;
    const DAY_WIDTH = 28;
    const ROW_HEIGHT = 60;
    const LOOKBACK_DAYS = 180;
    const DEFAULT_FUTURE_WEEKS = 6;
    const MIN_FUTURE_WEEKS = 4;
    const MAX_FUTURE_WEEKS = 10;
    const DEFAULT_WARNING_THRESHOLD = 70;
    const CRITICAL_THRESHOLD = 90;
    const BATCH_RENDER_SIZE = 5;
    const FETCH_TIMEOUT_MS = 15_000;
    const MAX_DOM_OPERATIONS = 5_000;
    const MAX_CALENDAR_DAYS = 366;
    const MAX_CALENDAR_ITERATIONS = MAX_CALENDAR_DAYS;
    const HEADER_DAY_CHUNK = 45;

    const COLORS = {
        safe: '#10b981',
        warning: '#f59e0b',
        critical: '#ef4444'
    };

    const RISK_THRESHOLDS = {
        safe: 60,
        caution: 85,
        limit: 90
    };

    const RISK_COLORS = {
        safe: COLORS.safe,
        caution: COLORS.warning,
        critical: COLORS.critical
    };

    const ALERT_COLORS = {
        YELLOW: '#facc15',
        ORANGE: '#f97316',
        RED: '#dc2626'
    };

    const VIEW_MODES = {
        CALENDAR: 'calendar',
        TIMELINE: 'timeline'
    };

    const DEBUG_CALENDAR = false;

    function debugLog(...args) {
        if (DEBUG_CALENDAR) {
            console.debug('[Calendar]', ...args);
        }
    }

    function setTimer(handler, delay) {
        if (typeof globalThis !== 'undefined' && typeof globalThis.setTimeout === 'function') {
            return globalThis.setTimeout(handler, delay);
        }
        return setTimeout(handler, delay);
    }

    function clearTimer(handle) {
        if (!handle) {
            return;
        }
        if (typeof globalThis !== 'undefined' && typeof globalThis.clearTimeout === 'function') {
            globalThis.clearTimeout(handle);
        } else {
            clearTimeout(handle);
        }
    }

    function consumeDomBudget(budget, amount = 1) {
        if (!budget) {
            return true;
        }
        if (budget.remaining - amount < 0) {
            budget.remaining = 0;
            budget.exhausted = true;
            return false;
        }
        budget.remaining -= amount;
        return true;
    }

    function sanitizeText(value) {
        return typeof value === 'string' ? value.trim() : '';
    }

    function escapeHtml(value) {
        if (value === null || value === undefined) {
            return '';
        }
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function isValidIsoDateString(value) {
        return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);
    }

    function hexToRgba(hex, alpha = 1) {
        if (typeof hex !== 'string') {
            return `rgba(76, 175, 80, ${alpha})`;
        }
        const normalized = hex.replace('#', '').trim();
        if (!/^[0-9a-fA-F]{3,6}$/.test(normalized)) {
            return `rgba(76, 175, 80, ${alpha})`;
        }
        const value = normalized.length === 3
            ? normalized.split('').map((char) => char + char).join('')
            : normalized.padEnd(6, '0');
        const bigint = Number.parseInt(value, 16);
        const r = (bigint >> 16) & 255;
        const g = (bigint >> 8) & 255;
        const b = bigint & 255;
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    function parseDate(value) {
        if (!value) {
            return null;
        }
        if (value instanceof Date) {
            return new Date(value.getTime());
        }
        const iso = typeof value === 'string' ? value.trim() : '';
        if (!iso) {
            return null;
        }
        const parsed = new Date(iso);
        if (Number.isNaN(parsed.getTime())) {
            const [year, month, day] = iso.split(/[-/]/).map(Number);
            if (!year || !month || !day) {
                return null;
            }
            const fallback = new Date(Date.UTC(year, month - 1, day));
            if (Number.isNaN(fallback.getTime())) {
                return null;
            }
            return fallback;
        }
        return parsed;
    }

    function startOfDay(date) {
        const d = new Date(date.getTime());
        d.setHours(0, 0, 0, 0);
        return d;
    }

    function addDays(date, days) {
        return new Date(startOfDay(date).getTime() + days * DAY_IN_MS);
    }

    function addMonths(date, count) {
        const d = new Date(date.getFullYear(), date.getMonth() + count, date.getDate());
        if (d.getDate() !== date.getDate()) {
            d.setDate(0);
        }
        return startOfDay(d);
    }

    function startOfMonth(date) {
        return new Date(date.getFullYear(), date.getMonth(), 1);
    }

    function endOfMonth(date) {
        return new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59, 999);
    }

    function diffInDaysInclusive(start, end) {
        return Math.floor((startOfDay(end) - startOfDay(start)) / DAY_IN_MS);
    }

    function clampDate(value, min, max) {
        if (value < min) {
            return new Date(min.getTime());
        }
        if (value > max) {
            return new Date(max.getTime());
        }
        return new Date(value.getTime());
    }

    function formatDateDdMmYyyy(date) {
        if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
            return '';
        }
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}-${month}-${year}`;
    }

    function formatDayCountLabel(value) {
        if (value === null || value === undefined || value === '') {
            return '';
        }
        const numeric = Number(value);
        if (Number.isNaN(numeric)) {
            return String(value);
        }
        const absDays = Math.abs(numeric);
        const suffix = absDays === 1 ? 'day' : 'days';
        return `${numeric} ${suffix}`;
    }

    function formatAlertTimestamp(value) {
        if (!value) {
            return { label: '', iso: '' };
        }
        try {
            let parsed = value;
            if (typeof value === 'string') {
                const normalized = value.includes('T') ? value : value.replace(' ', 'T');
                parsed = new Date(normalized.endsWith('Z') ? normalized : `${normalized}Z`);
            } else if (value instanceof Date) {
                parsed = value;
            } else {
                parsed = new Date(value);
            }
            if (parsed instanceof Date && !Number.isNaN(parsed.getTime())) {
                const label = parsed.toLocaleString(undefined, {
                    hour: '2-digit',
                    minute: '2-digit',
                    day: '2-digit',
                    month: 'short'
                });
                return {
                    label,
                    iso: parsed.toISOString()
                };
            }
        } catch (error) {
            console.warn('Unable to format alert timestamp', error);
        }
        return { label: String(value), iso: '' };
    }

    function formatRangeLabel(range) {
        const startLabel = formatDateDdMmYyyy(range.start);
        const endLabel = formatDateDdMmYyyy(range.end);
        return startLabel === endLabel ? startLabel : `${startLabel} – ${endLabel}`;
    }

    function isWithinRange(date, range) {
        return date >= range.start && date <= range.end;
    }

    function serialiseDate(date) {
        return date.toISOString().split('T')[0];
    }

    function calculateRangeDays(range) {
        if (!range) {
            return [];
        }

        const rawStart = range.start instanceof Date ? range.start : parseDate(range.start);
        const rawEnd = range.end instanceof Date ? range.end : parseDate(range.end);

        if (!(rawStart instanceof Date) || Number.isNaN(rawStart.getTime()) || !(rawEnd instanceof Date) || Number.isNaN(rawEnd.getTime())) {
            console.warn('calculateRangeDays received invalid range', range);
            return [];
        }

        const start = startOfDay(rawStart);
        const desiredEnd = startOfDay(rawEnd);
        const span = diffInDaysInclusive(start, desiredEnd);

        if (!Number.isFinite(span)) {
            console.warn('calculateRangeDays span is not finite', { start, desiredEnd, span });
            return [];
        }

        if (span < 0) {
            console.warn('calculateRangeDays received inverted range', { start, desiredEnd, span });
            return [];
        }

        if (span + 1 > MAX_CALENDAR_ITERATIONS) {
            console.warn(`Calendar range spans ${span + 1} days; clamping to safe window of ${MAX_CALENDAR_ITERATIONS}.`, {
                start,
                desiredEnd,
                span
            });
        }

        // Additional safety: cap the actual loop to prevent runaway iterations
        const maxIterations = Math.min(Math.max(span + 1, 0), MAX_CALENDAR_ITERATIONS);
        const days = [];
        for (let index = 0; index < maxIterations; index += 1) {
            const cursor = addDays(start, index);
            days.push({
                date: new Date(cursor.getTime()),
                day: cursor.getDate(),
                isMonthStart: cursor.getDate() === 1,
                isWeekStart: cursor.getDay() === 1,
                isWeekend: cursor.getDay() === 0 || cursor.getDay() === 6
            });
        }
        return days;
    }

    function normaliseTrip(trip) {
        const entry = parseDate(trip.entry_date || trip.start_date);
        const exit = parseDate(trip.exit_date || trip.end_date) || entry;
        if (!entry) {
            return null;
        }
        const start = startOfDay(entry);
        const end = exit ? startOfDay(exit) : startOfDay(entry);
        const resolvedEnd = end < start ? start : end;
        const durationDays = diffInDaysInclusive(start, resolvedEnd) + 1;
        const travelDaysValue = Number(trip.travel_days);
        const createdAt = parseDate(trip.created_at || trip.createdAt);
        const updatedAt = parseDate(trip.updated_at || trip.updatedAt);

        return {
            id: trip.id,
            employeeId: trip.employee_id,
            employeeName: trip.employee_name || trip.employee,
            country: trip.country,
            isPrivate: Boolean(trip.is_private),
            jobRef: trip.job_ref || '',
            purpose: trip.purpose || '',
            notes: trip.notes || trip.note || '',
            ghosted: Boolean(trip.ghosted),
            travelDays: Number.isFinite(travelDaysValue) ? travelDaysValue : durationDays,
            durationDays,
            start,
            end: resolvedEnd,
            createdAt,
            updatedAt,
            raw: trip
        };
    }

    function calculateTripPlacement(range, trip) {
        if (!trip || !range) {
            return {
                clampedStart: null,
                clampedEnd: null,
                offsetDays: 0,
                durationDays: 0
            };
        }
        const clampedStart = clampDate(trip.start, range.start, range.end);
        const clampedEnd = clampDate(trip.end, range.start, range.end);
        const offsetDays = Math.max(0, diffInDaysInclusive(range.start, clampedStart));
        const durationDays = Math.max(1, diffInDaysInclusive(clampedStart, clampedEnd) + 1);
        return {
            clampedStart,
            clampedEnd,
            offsetDays,
            durationDays
        };
    }

    function calculateRollingDaysUsed(trips, targetDate, limit = RISK_THRESHOLDS.limit) {
        if (!Array.isArray(trips) || !trips.length || !(targetDate instanceof Date)) {
            return 0;
        }
        const windowStart = addDays(targetDate, -(limit - 1));
        let total = 0;
        for (const trip of trips) {
            if (!trip || !(trip.start instanceof Date) || !(trip.end instanceof Date)) {
                continue;
            }
            if (trip.end < windowStart || trip.start > targetDate) {
                continue;
            }
            const overlapStart = trip.start > windowStart ? trip.start : windowStart;
            const overlapEnd = trip.end < targetDate ? trip.end : targetDate;
            if (overlapEnd < overlapStart) {
                continue;
            }
            total += diffInDaysInclusive(overlapStart, overlapEnd) + 1;
        }
        return Math.max(0, total);
    }

    function resolveRiskLevel(daysUsed) {
        if (!Number.isFinite(daysUsed)) {
            return { level: 'unknown', color: RISK_COLORS.safe };
        }
        if (daysUsed <= RISK_THRESHOLDS.safe) {
            return { level: 'safe', color: RISK_COLORS.safe };
        }
        if (daysUsed <= RISK_THRESHOLDS.caution) {
            return { level: 'caution', color: RISK_COLORS.caution };
        }
        return { level: 'critical', color: RISK_COLORS.critical };
    }

    function buildTripStatusIndex(trips, warningThreshold, criticalThreshold = CRITICAL_THRESHOLD) {
        const sorted = trips.slice().sort((a, b) => a.start - b.start || a.id - b.id);
        const index = new Map();
        const windowLength = 179;
        const activeTrips = [];

        for (const current of sorted) {
            const windowStart = addDays(current.end, -windowLength);

            while (activeTrips.length && activeTrips[0].end < windowStart) {
                activeTrips.shift();
            }

            activeTrips.push(current);

            let daysUsed = 0;
            for (let indexPointer = 0; indexPointer < activeTrips.length; indexPointer += 1) {
                const trip = activeTrips[indexPointer];
                const overlapStart = trip.start > windowStart ? trip.start : windowStart;
                const overlapEnd = trip.end < current.end ? trip.end : current.end;
                if (overlapEnd < overlapStart) {
                    continue;
                }
                daysUsed += diffInDaysInclusive(overlapStart, overlapEnd) + 1;
            }

            let status = 'safe';
            if (daysUsed >= criticalThreshold) {
                status = 'critical';
            } else if (daysUsed > warningThreshold) {
                status = 'warning';
            }

            index.set(current.id, {
                status,
                daysUsed
            });
        }

        return index;
    }

    function groupTripsByEmployee(trips) {
        const groups = new Map();
        for (const trip of trips) {
            if (!groups.has(trip.employeeId)) {
                groups.set(trip.employeeId, []);
            }
            groups.get(trip.employeeId).push(trip);
        }
        for (const list of groups.values()) {
            list.sort((a, b) => a.start - b.start || a.end - b.end || a.id - b.id);
        }
        return groups;
    }

    function deriveEmployees(employees, trips) {
        const byId = new Map();
        for (const employee of employees || []) {
            byId.set(employee.id, {
                id: employee.id,
                name: employee.name,
                active: employee.active !== false,
                trips: []
            });
        }

        for (const trip of trips) {
            if (!byId.has(trip.employeeId)) {
                byId.set(trip.employeeId, {
                    id: trip.employeeId,
                    name: trip.employeeName || `Employee ${trip.employeeId}`,
                    active: true,
                    trips: []
                });
            }
            byId.get(trip.employeeId).trips.push(trip);
        }

        const derived = Array.from(byId.values());
        derived.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }));
        return derived;
    }

    function formatDisplayDate(date) {
        return formatDateDdMmYyyy(date);
    }

    function formatDateTimeDisplay(date) {
        if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
            return '';
        }
        return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
    }

    function formatDateRangeDisplay(start, end) {
        if (!start || !end) {
            return '';
        }
        return `${formatDisplayDate(start)} → ${formatDisplayDate(end)}`;
    }

    function formatDuration(days) {
        if (!Number.isFinite(days)) {
            return '';
        }
        const absolute = Math.max(1, Math.round(days));
        return absolute === 1 ? '1 day' : `${absolute} days`;
    }

    function normaliseStatusLabel(status) {
        switch (status) {
            case 'critical':
                return 'Exceeded 90-day threshold';
            case 'warning':
                return 'Approaching 90-day limit';
            default:
                return 'Compliant trip';
        }
    }

    function filterEmployees(employees, term) {
        const value = term.trim().toLowerCase();
        if (!value) {
            return employees.slice();
        }
        return employees.filter((emp) => emp.name.toLowerCase().includes(value));
    }

    function createTooltip() {
        let tooltipEl = null;
        let visible = false;

        function ensureElement() {
            if (tooltipEl) {
                return tooltipEl;
            }
            tooltipEl = document.createElement('div');
            tooltipEl.className = 'calendar-tooltip';
            tooltipEl.setAttribute('role', 'tooltip');
            tooltipEl.setAttribute('aria-hidden', 'true');
            document.body.appendChild(tooltipEl);
            return tooltipEl;
        }

        ensureElement();

        return {
            show(content, x, y, options = {}) {
                const el = ensureElement();
                el.innerHTML = content;
                if (options && options.accent) {
                    el.style.setProperty('--calendar-tooltip-accent', options.accent);
                }
                el.style.left = `${x + 16}px`;
                el.style.top = `${y + 16}px`;
                el.classList.add('calendar-tooltip--visible');
                el.setAttribute('aria-hidden', 'false');
                visible = true;
            },
            move(x, y) {
                if (!visible || !tooltipEl) {
                    return;
                }
                tooltipEl.style.left = `${x + 16}px`;
                tooltipEl.style.top = `${y + 16}px`;
            },
            hide() {
                if (!tooltipEl) {
                    return;
                }
                tooltipEl.classList.remove('calendar-tooltip--visible');
                tooltipEl.setAttribute('aria-hidden', 'true');
                visible = false;
            }
        };
    }

    function CalendarController(root) {
        this.root = root;
        const configuredThreshold = Number.parseInt(root.dataset.warningThreshold, 10);
        const safeThreshold = Number.isFinite(configuredThreshold) ? configuredThreshold : DEFAULT_WARNING_THRESHOLD;
        this.warningThreshold = Math.min(Math.max(safeThreshold, 0), DEFAULT_WARNING_THRESHOLD);
        this.criticalThreshold = CRITICAL_THRESHOLD;
        this.focusEmployeeId = root.dataset.focusEmployee ? Number.parseInt(root.dataset.focusEmployee, 10) : null;
        this.focusEmployeeName = root.dataset.focusEmployeeName || '';
        this.today = startOfDay(new Date());
        this.futureWeeks = DEFAULT_FUTURE_WEEKS;
        this.range = this.calculateRange();
        this.state = {
            employees: [],
            filteredEmployees: [],
            trips: [],
            tripGroups: new Map(),
            tripStatus: new Map(),
            tripIndex: new Map(),
            searchTerm: '',
            isRendering: false,
            formMode: null,
            editingTripId: null,
            isSubmittingForm: false,
            alerts: [],
            alertIndex: new Map(),
            alertFilter: 'all',
            resolvingAlertId: null
        };
        this.elements = {
            toolbar: root.querySelector('.calendar-toolbar'),
            rangeLabel: root.querySelector('#calendar-range-label'),
            futureWeeksSelect: root.querySelector('#calendar-future-weeks'),
            monthRow: root.querySelector('#calendar-month-row'),
            dayRow: root.querySelector('#calendar-day-row'),
            todayMarkerHeader: root.querySelector('#calendar-today-marker'),
            todayMarkerBody: root.querySelector('#calendar-today-marker-body'),
            employeeList: root.querySelector('#calendar-employee-list'),
            timelineContainer: root.querySelector('.calendar-timeline'),
            timelineInner: root.querySelector('#calendar-timeline'),
            grid: root.querySelector('#calendar-grid'),
            loading: root.querySelector('#calendar-loading'),
            empty: root.querySelector('#calendar-empty'),
            error: root.querySelector('#calendar-error'),
            retryBtn: root.querySelector('[data-action="retry"]'),
            searchInput: root.querySelector('#calendar-search-input'),
            searchClear: root.querySelector('.calendar-search-clear'),
            timelineHeader: root.querySelector('.calendar-timeline-header'),
            detailOverlay: root.querySelector('#calendar-detail-overlay'),
            detail: root.querySelector('.calendar-detail'),
            detailClose: root.querySelector('[data-action="close-detail"]'),
            detailStatus: root.querySelector('#calendar-detail-status'),
            detailStatusDot: root.querySelector('#calendar-detail-status-dot'),
            detailTitle: root.querySelector('#calendar-detail-title'),
            detailEmployee: root.querySelector('#calendar-detail-employee'),
            detailCountry: root.querySelector('#calendar-detail-country'),
            detailDates: root.querySelector('#calendar-detail-dates'),
            detailDuration: root.querySelector('#calendar-detail-duration'),
            detailUsage: root.querySelector('#calendar-detail-usage'),
            detailRemaining: root.querySelector('#calendar-detail-remaining'),
            detailNotes: root.querySelector('#calendar-detail-notes'),
            detailPurpose: root.querySelector('#calendar-detail-purpose'),
            detailJobRef: root.querySelector('#calendar-detail-jobref'),
            detailJobRefValue: root.querySelector('#calendar-detail-jobref-value'),
            detailCreated: root.querySelector('#calendar-detail-created'),
            detailCreatedValue: root.querySelector('#calendar-detail-created-value'),
            detailUpdated: root.querySelector('#calendar-detail-updated'),
            detailUpdatedValue: root.querySelector('#calendar-detail-updated-value'),
            addTripBtn: root.querySelector('[data-action="add-trip"]'),
            editTripGlobal: root.querySelector('[data-action="edit-trip-global"]'),
            formOverlay: root.querySelector('#calendar-form-overlay'),
            form: root.querySelector('#calendar-form'),
            formTitle: root.querySelector('#calendar-form-title'),
            formSubtitle: root.querySelector('#calendar-form-subtitle'),
            formEmployee: root.querySelector('#calendar-form-employee'),
            formCountry: root.querySelector('#calendar-form-country'),
            formStart: root.querySelector('#calendar-form-start'),
            formEnd: root.querySelector('#calendar-form-end'),
            formJobRef: root.querySelector('#calendar-form-jobref'),
            formPurpose: root.querySelector('#calendar-form-purpose'),
            formFeedback: root.querySelector('#calendar-form-feedback'),
            formSubmit: root.querySelector('[data-action="submit-form"]'),
            toast: root.querySelector('#calendar-toast'),
            alertsPanel: root.querySelector('#calendar-alerts-panel'),
            alertsToggle: root.querySelector('#calendar-alerts-toggle'),
            alertsList: root.querySelector('#calendar-alerts-list'),
            alertsEmpty: root.querySelector('#calendar-alerts-empty'),
            alertsFilters: Array.from(root.querySelectorAll('[data-alert-filter]')),
            fullscreenToggle: root.querySelector('[data-action="toggle-fullscreen"]'),
            contextMenu: root.querySelector('#calendar-context-menu'),
            viewToggleButtons: Array.from(root.querySelectorAll('.calendar-view-toggle__button')),
            viewStack: root.querySelector('.calendar-view-stack'),
            viewLayers: Array.from(root.querySelectorAll('.calendar-view-layer')),
            forecastPanel: root.querySelector('#calendar-forecast-panel'),
            forecastToggle: root.querySelector('[data-forecast-action="toggle"]'),
            forecastRefresh: root.querySelector('[data-forecast-action="refresh"]'),
            forecastEmployee: root.querySelector('[data-forecast-employee]'),
            forecastStatus: root.querySelector('[data-forecast-status]'),
            forecastUsed: root.querySelector('[data-forecast-used]'),
            forecastUpcoming: root.querySelector('[data-forecast-upcoming]'),
            forecastTotal: root.querySelector('[data-forecast-total]'),
            forecastProgress: root.querySelector('[data-forecast-progress]'),
            forecastCaption: root.querySelector('[data-forecast-caption]'),
            forecastUpcomingWrapper: root.querySelector('[data-forecast-upcoming-wrapper]'),
            forecastUpcomingList: root.querySelector('[data-forecast-upcoming-list]'),
            forecastTimestamp: root.querySelector('[data-forecast-updated]')
        };
        this.tooltip = createTooltip();
        this.contextMenuState = {
            node: this.elements.contextMenu,
            isOpen: false,
            tripId: null,
            trigger: null
        };
        this.editTripButtons = Array.from(root.querySelectorAll('[data-action="edit-trip"]'));
        if (this.elements.editTripGlobal) {
            this.editTripButtons.push(this.elements.editTripGlobal);
        }
        this.formCloseButtons = Array.from(root.querySelectorAll('[data-action="close-form"]'));
        this.timelineWidth = 0;
        this.state.activeView = VIEW_MODES.CALENDAR;
        this.state.forecast = {
            employeeId: null,
            employeeName: '',
            isLoading: false
        };
        this.dataCache = null;
        this.shouldCenterOnToday = false;
        this.isDetailOpen = false;
        this.lastFocusedTrip = null;
        this.activeTripId = null;
        this.pendingCenterDate = null;
        this.pendingFocusTripId = null;
        this.resizeFrame = null;
        this.timelineHeaderFrame = null;
        this.timelineHeaderToken = null;
        this.toastTimer = null;
        this.timelineScrollFrame = null;
        this.pendingTimelineScrollLeft = 0;
        this.verticalScrollFrame = null;
        this.pendingVerticalScrollTop = 0;
        this.verticalScrollTarget = null;
        this.isSyncingVerticalScroll = false;
        this.tooltipMoveFrame = null;
        this.pendingTooltipPosition = { x: 0, y: 0 };
        this.cellTemplate = null;
        this.cellTemplateKey = '';
        this.handlersBound = false;
        this.searchDebounceTimer = null;
        this.riskCache = new Map();
        this.forecastCache = new Map();
        this.forecastAbortController = null;
        this.handleTimelineScroll = this.handleTimelineScroll.bind(this);
        this.handleTimelineVerticalScroll = this.handleTimelineVerticalScroll.bind(this);
        this.handleViewToggleClick = this.handleViewToggleClick.bind(this);
        this.handleForecastToggle = this.handleForecastToggle.bind(this);
        this.handleForecastRefresh = this.handleForecastRefresh.bind(this);
        this.handleTimelineSelectTrip = this.handleTimelineSelectTrip.bind(this);
        this.handleTimelineFocusEmployee = this.handleTimelineFocusEmployee.bind(this);
        this.handleEmployeeListClick = this.handleEmployeeListClick.bind(this);
        this.handleTripClick = this.handleTripClick.bind(this);
        this.handleTripKeydown = this.handleTripKeydown.bind(this);
        this.handleTripContextMenu = this.handleTripContextMenu.bind(this);
        this.handleTripPointerDown = this.handleTripPointerDown.bind(this);
        this.handleTripResizeMove = this.handleTripResizeMove.bind(this);
        this.handleTripResizeEnd = this.handleTripResizeEnd.bind(this);
        this.handleContextMenuClick = this.handleContextMenuClick.bind(this);
        this.handleOutsideContextPointer = this.handleOutsideContextPointer.bind(this);
        this.handleContextMenuKeydown = this.handleContextMenuKeydown.bind(this);
        this.handleOverlayInteraction = this.handleOverlayInteraction.bind(this);
        this.handleGlobalKeydown = this.handleGlobalKeydown.bind(this);
        this.handleWindowResize = this.handleWindowResize.bind(this);
        this.handleGridMouseover = this.handleGridMouseover.bind(this);
        this.handleGridMousemove = this.handleGridMousemove.bind(this);
        this.handleGridMouseout = this.handleGridMouseout.bind(this);
        this.handleFullscreenToggle = this.handleFullscreenToggle.bind(this);
        this.handleFullscreenChange = this.handleFullscreenChange.bind(this);
        this.handleDragPreview = this.handleDragPreview.bind(this);
        this.handleDragPreviewEnd = this.handleDragPreviewEnd.bind(this);
        this.emptyStateMessageNode = this.elements.empty ? this.elements.empty.querySelector('p') : null;
        this.emptyStateDefaultMessage = this.emptyStateMessageNode ? this.emptyStateMessageNode.textContent : '';
        this.resizeSession = null;
        this.attachHandlers();
        this.root.__calendarController = this;

        const DragManagerClass = global && typeof global.CalendarDragManager === 'function'
            ? global.CalendarDragManager
            : null;

        if (DragManagerClass) {
            this.dragManager = new DragManagerClass({
                grid: this.elements.grid,
                dayWidth: DAY_WIDTH,
                formatLabel: (start, end) => formatDateRangeDisplay(start, end),
                getRange: () => this.range,
                onDrop: (details) => this.handleTripDrop(details),
                onPreview: (details) => this.handleDragPreview(details),
                onPreviewEnd: (details) => this.handleDragPreviewEnd(details)
            });
        } else {
            console.warn('CalendarDragManager unavailable; drag-and-drop disabled.');
            this.dragManager = null;
        }
    }

    CalendarController.prototype.attachHandlers = function attachHandlers() {
        if (this.handlersBound) {
            return;
        }
        this.handlersBound = true;
        const prevBtn = this.root.querySelector('[data-action="prev"]');
        const nextBtn = this.root.querySelector('[data-action="next"]');
        const todayBtn = this.root.querySelector('[data-action="today"]');

        if (this.elements.addTripBtn) {
            this.elements.addTripBtn.addEventListener('click', () => this.openForm('create'));
        }
        if (this.editTripButtons && this.editTripButtons.length) {
            this.editTripButtons.forEach((button) => {
                button.addEventListener('click', (event) => {
                    if (!Number.isFinite(this.activeTripId)) {
                        return;
                    }
                    if (button.matches('[data-action="edit-trip-global"]') && (button.disabled || button.getAttribute('aria-disabled') === 'true')) {
                        event.preventDefault();
                        return;
                    }
                    this.openForm('edit', this.activeTripId);
                });
            });
        }
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.shiftRange(-1));
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.shiftRange(1));
        }
        if (todayBtn) {
            todayBtn.addEventListener('click', () => this.resetToToday());
        }
        if (this.elements.retryBtn) {
            this.elements.retryBtn.addEventListener('click', () => {
                this.loadData({ force: true }).catch((error) => {
                    console.error('Retry load failed', error);
                });
            });
        }
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (event) => {
                const term = event.target.value || '';
                if (this.searchDebounceTimer) {
                    clearTimer(this.searchDebounceTimer);
                }
                this.searchDebounceTimer = setTimer(() => {
                    this.state.searchTerm = term;
                    this.updateSearchUI();
                    this.applyFilters();
                    this.searchDebounceTimer = null;
                }, 90);
            });
        }
        if (this.elements.searchClear) {
            this.elements.searchClear.addEventListener('click', () => {
                clearTimer(this.searchDebounceTimer);
                this.searchDebounceTimer = null;
                this.state.searchTerm = '';
                if (this.elements.searchInput) {
                    this.elements.searchInput.value = '';
                }
                this.updateSearchUI();
                this.applyFilters();
            });
        }
        if (this.elements.viewToggleButtons && this.elements.viewToggleButtons.length) {
            this.elements.viewToggleButtons.forEach((button) => {
                button.addEventListener('click', this.handleViewToggleClick);
            });
        }
        if (this.elements.timelineContainer) {
            this.elements.timelineContainer.addEventListener('scroll', this.handleTimelineScroll, { passive: true });
            this.elements.timelineContainer.addEventListener('scroll', this.handleTimelineVerticalScroll, { passive: true });
        }
        if (this.elements.employeeList) {
            this.elements.employeeList.addEventListener('scroll', this.handleTimelineVerticalScroll, { passive: true });
            this.elements.employeeList.addEventListener('click', this.handleEmployeeListClick);
        }
        if (this.elements.grid) {
            this.elements.grid.addEventListener('mouseover', (event) => this.handleGridMouseover(event));
            this.elements.grid.addEventListener('mousemove', this.handleGridMousemove);
            this.elements.grid.addEventListener('mouseout', (event) => this.handleGridMouseout(event));
            this.elements.grid.addEventListener('click', this.handleTripClick);
            this.elements.grid.addEventListener('keydown', this.handleTripKeydown);
            this.elements.grid.addEventListener('contextmenu', this.handleTripContextMenu);
            this.elements.grid.addEventListener('pointerdown', this.handleTripPointerDown, { passive: false });
        }
        if (this.elements.detailOverlay) {
            this.elements.detailOverlay.addEventListener('click', this.handleOverlayInteraction);
        }
        if (this.elements.detailClose) {
            this.elements.detailClose.addEventListener('click', () => this.closeTripDetail());
        }
        if (this.formCloseButtons && this.formCloseButtons.length) {
            this.formCloseButtons.forEach((btn) => {
                btn.addEventListener('click', () => this.closeForm());
            });
        }
        if (this.elements.formOverlay) {
            this.elements.formOverlay.addEventListener('click', (event) => {
                if (event.target === this.elements.formOverlay) {
                    this.closeForm();
                }
            });
        }
        if (this.elements.form) {
            this.elements.form.addEventListener('submit', (event) => this.handleFormSubmit(event));
            this.elements.form.addEventListener('input', () => this.clearFormFeedback());
        }
        if (this.elements.alertsFilters && this.elements.alertsFilters.length) {
            this.elements.alertsFilters.forEach((button) => {
                button.addEventListener('click', () => {
                    const filter = button.getAttribute('data-alert-filter') || 'all';
                    this.setAlertFilter(filter);
                });
            });
        }
        if (this.elements.alertsList) {
            this.elements.alertsList.addEventListener('click', (event) => {
                const trigger = event.target.closest('[data-action="resolve-alert"]');
                if (!trigger) {
                    return;
                }
                const alertId = Number.parseInt(trigger.getAttribute('data-alert-id'), 10);
                const employeeId = Number.parseInt(trigger.getAttribute('data-employee-id'), 10);
                if (Number.isFinite(alertId)) {
                    this.resolveAlert(alertId, Number.isFinite(employeeId) ? employeeId : null, trigger);
                }
            });
        }
        if (this.contextMenuState.node) {
            this.contextMenuState.node.addEventListener('click', this.handleContextMenuClick);
            this.contextMenuState.node.addEventListener('keydown', this.handleContextMenuKeydown);
        }
        if (this.elements.fullscreenToggle) {
            this.elements.fullscreenToggle.addEventListener('click', this.handleFullscreenToggle);
            this.syncFullscreenButton();
        }
        if (this.elements.alertsToggle) {
            this.elements.alertsToggle.addEventListener('click', () => {
                this.toggleAlertsPanel();
            });
        }
        if (this.elements.forecastToggle) {
            this.elements.forecastToggle.addEventListener('click', this.handleForecastToggle);
        }
        if (this.elements.forecastRefresh) {
            this.elements.forecastRefresh.addEventListener('click', this.handleForecastRefresh);
        }
        if (this.root) {
            this.root.addEventListener('timeline:select-trip', this.handleTimelineSelectTrip);
            this.root.addEventListener('timeline:focus-employee', this.handleTimelineFocusEmployee);
        }
        this.updateGlobalEditButtonState();
        window.addEventListener('resize', this.handleWindowResize, { passive: true });
        document.addEventListener('keydown', this.handleGlobalKeydown);
        document.addEventListener('fullscreenchange', this.handleFullscreenChange);
    };

    CalendarController.prototype.handleTimelineScroll = function handleTimelineScroll(event) {
        this.closeContextMenu();
        if (!this.elements.monthRow || !this.elements.dayRow) {
            return;
        }
        this.pendingTimelineScrollLeft = event.target.scrollLeft;
        if (this.timelineScrollFrame) {
            return;
        }
        this.timelineScrollFrame = requestAnimationFrame(() => {
            this.timelineScrollFrame = null;
            const scrollLeft = this.pendingTimelineScrollLeft;
            this.elements.monthRow.style.transform = `translateX(${-scrollLeft}px)`;
            this.elements.dayRow.style.transform = `translateX(${-scrollLeft}px)`;
        });
    };

    CalendarController.prototype.handleTimelineVerticalScroll = function handleTimelineVerticalScroll(event) {
        this.closeContextMenu();
        if (!this.elements.timelineContainer || !this.elements.employeeList) {
            return;
        }
        if (this.isSyncingVerticalScroll) {
            return;
        }
        const source = event.target;
        const partner = source === this.elements.timelineContainer
            ? this.elements.employeeList
            : source === this.elements.employeeList
                ? this.elements.timelineContainer
                : null;
        if (!partner) {
            return;
        }
        const scrollTop = source.scrollTop;
        if (partner.scrollTop === scrollTop) {
            return;
        }
        this.pendingVerticalScrollTop = scrollTop;
        this.verticalScrollTarget = partner;
        if (this.verticalScrollFrame) {
            return;
        }
        this.verticalScrollFrame = requestAnimationFrame(() => {
            const target = this.verticalScrollTarget;
            this.verticalScrollFrame = null;
            this.verticalScrollTarget = null;
            if (!target) {
                return;
            }
            this.isSyncingVerticalScroll = true;
            if (target.scrollTop !== this.pendingVerticalScrollTop) {
                target.scrollTop = this.pendingVerticalScrollTop;
            }
            this.isSyncingVerticalScroll = false;
        });
    };

    CalendarController.prototype.handleViewToggleClick = function handleViewToggleClick(event) {
        const button = event.currentTarget || event.target;
        if (!button || !button.dataset) {
            return;
        }
        const targetView = button.dataset.viewTarget || VIEW_MODES.CALENDAR;
        this.setActiveView(targetView);
    };

    CalendarController.prototype.setActiveView = function setActiveView(view) {
        const target = view === VIEW_MODES.TIMELINE ? VIEW_MODES.TIMELINE : VIEW_MODES.CALENDAR;
        if (this.state.activeView === target) {
            return;
        }
        this.state.activeView = target;
        this.updateViewToggleUI();
        if (this.elements.viewStack) {
            this.elements.viewStack.dataset.activeView = target;
        }
        if (this.elements.viewLayers && this.elements.viewLayers.length) {
            this.elements.viewLayers.forEach((layer) => {
                const layerView = layer.getAttribute('data-view-layer');
                const isActive = layerView === target;
                layer.classList.toggle('is-active', isActive);
                layer.setAttribute('aria-hidden', isActive ? 'false' : 'true');
            });
        }
        if (target === VIEW_MODES.TIMELINE && typeof globalThis.TimelineView !== 'undefined') {
            if (typeof globalThis.TimelineView.sync === 'function') {
                this.syncTimelineView({ reason: 'view-switch' });
            }
            if (typeof globalThis.TimelineView.activate === 'function') {
                globalThis.TimelineView.activate();
            }
        }
    };

    CalendarController.prototype.updateViewToggleUI = function updateViewToggleUI() {
        if (!this.elements.viewToggleButtons || !this.elements.viewToggleButtons.length) {
            return;
        }
        this.elements.viewToggleButtons.forEach((button) => {
            const buttonView = button.dataset.viewTarget || VIEW_MODES.CALENDAR;
            const isActive = buttonView === this.state.activeView;
            button.classList.toggle('is-active', isActive);
            button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
    };

    CalendarController.prototype.handleForecastToggle = function handleForecastToggle(event) {
        event.preventDefault();
        this.toggleForecastPanel();
    };

    CalendarController.prototype.toggleForecastPanel = function toggleForecastPanel(forceState) {
        if (!this.elements.forecastPanel || !this.elements.forecastToggle) {
            return;
        }
        const current = this.elements.forecastPanel.getAttribute('data-forecast-state') || 'open';
        const next = forceState === 'open' || forceState === 'closed'
            ? forceState
            : current === 'open'
                ? 'closed'
                : 'open';
        this.elements.forecastPanel.setAttribute('data-forecast-state', next);
        this.elements.forecastToggle.setAttribute('aria-expanded', next === 'open' ? 'true' : 'false');
        const toggleLabel = this.elements.forecastToggle.querySelector('.visually-hidden');
        if (toggleLabel) {
            toggleLabel.textContent = next === 'open' ? 'Collapse mini forecast panel' : 'Expand mini forecast panel';
        }
    };

    CalendarController.prototype.handleForecastRefresh = function handleForecastRefresh(event) {
        event.preventDefault();
        const employeeId = this.state.forecast && Number.isFinite(this.state.forecast.employeeId)
            ? this.state.forecast.employeeId
            : null;
        if (Number.isFinite(employeeId)) {
            this.setForecastEmployee(employeeId, { force: true, bypassCache: true, reason: 'manual-refresh' });
        }
    };

    CalendarController.prototype.handleEmployeeListClick = function handleEmployeeListClick(event) {
        if (event.target.closest('a')) {
            return;
        }
        const item = event.target.closest('.calendar-employee-item');
        if (!item) {
            return;
        }
        const employeeId = Number.parseInt(item.getAttribute('data-employee-id'), 10);
        if (!Number.isFinite(employeeId)) {
            return;
        }
        this.focusEmployeeId = employeeId;
        this.setForecastEmployee(employeeId, { reason: 'employee-list' });
        this.highlightEmployee(employeeId);
    };

    CalendarController.prototype.handleTimelineSelectTrip = function handleTimelineSelectTrip(event) {
        if (!event || !event.detail) {
            return;
        }
        const tripId = Number.parseInt(event.detail.tripId, 10);
        if (!Number.isFinite(tripId)) {
            return;
        }
        this.openTripDetail(tripId);
    };

    CalendarController.prototype.handleTimelineFocusEmployee = function handleTimelineFocusEmployee(event) {
        if (!event || !event.detail) {
            return;
        }
        const employeeId = Number.parseInt(event.detail.employeeId, 10);
        if (!Number.isFinite(employeeId)) {
            return;
        }
        this.setForecastEmployee(employeeId, { reason: 'timeline' });
        this.focusEmployeeId = employeeId;
        this.highlightEmployee(employeeId);
    };

    CalendarController.prototype.handleGridMouseover = function handleGridMouseover(event) {
        if (this.isDetailOpen || !this.tooltip) {
            return;
        }
        const tripTarget = event.target.closest('.calendar-trip');
        if (tripTarget) {
            const employee = sanitizeText(tripTarget.getAttribute('data-employee') || '');
            const country = sanitizeText(tripTarget.getAttribute('data-country') || 'Trip');
            const startIso = tripTarget.getAttribute('data-start');
            const endIso = tripTarget.getAttribute('data-end');
            const previewLabel = tripTarget.getAttribute('data-preview-label');
            const jobRef = sanitizeText(tripTarget.getAttribute('data-job-ref') || '');
            const statusLabel = sanitizeText(tripTarget.getAttribute('data-status-label') || '');
            const riskDays = sanitizeText(tripTarget.getAttribute('data-risk-days-used') || tripTarget.getAttribute('data-days-used') || '0');
            const riskColor = tripTarget.getAttribute('data-risk-color') || RISK_COLORS.safe;
            const daysRemainingAttr = sanitizeText(tripTarget.getAttribute('data-days-remaining') || '');
            const forecastRemainingAttr = sanitizeText(tripTarget.getAttribute('data-forecast-remaining') || '');
            const projectedRemaining = forecastRemainingAttr || daysRemainingAttr;

            const startDateValue = parseDate(startIso);
            const endDateValue = parseDate(endIso);
            const rangeLabel = previewLabel || formatDateRangeDisplay(startDateValue, endDateValue);
            const duration = startDateValue && endDateValue ? diffInDaysInclusive(startDateValue, endDateValue) + 1 : null;

            const tooltipContent = `
                <div class="calendar-tooltip__header">
                    <span class="calendar-tooltip__title">${escapeHtml(country || 'Trip')}</span>
                    ${statusLabel ? `<span class="calendar-tooltip__badge">${escapeHtml(statusLabel)}</span>` : ''}
                </div>
                <div class="calendar-tooltip__body">
                    ${employee ? `<span class="calendar-tooltip__employee">${escapeHtml(employee)}</span>` : ''}
                    ${rangeLabel ? `<span class="calendar-tooltip__dates">${escapeHtml(rangeLabel)}</span>` : ''}
                </div>
                <div class="calendar-tooltip__meta">
                    <span class="calendar-tooltip__metric">Days used: ${escapeHtml(riskDays)} / ${RISK_THRESHOLDS.limit}</span>
                    ${duration ? `<span class="calendar-tooltip__metric">Duration: ${escapeHtml(String(duration))} day${duration === 1 ? '' : 's'}</span>` : ''}
                    ${projectedRemaining ? `<span class="calendar-tooltip__metric">Forecast remaining: ${escapeHtml(formatDayCountLabel(projectedRemaining))}</span>` : ''}
                    ${jobRef ? `<span class="calendar-tooltip__metric">Job: ${escapeHtml(jobRef)}</span>` : ''}
                </div>
            `.trim();

            this.tooltip.show(tooltipContent, event.pageX, event.pageY, { accent: riskColor });
            return;
        }

        const cellTarget = event.target.closest('.calendar-cell');
        if (cellTarget) {
            const riskDays = cellTarget.dataset.riskDaysUsed || '0';
            const riskLevel = cellTarget.dataset.riskLevel || 'safe';
            const riskColor = cellTarget.dataset.riskColor || RISK_COLORS.safe;
            const dateValue = sanitizeText(cellTarget.dataset.calendarDate || '');
            const label = riskLevel === 'safe' ? 'Compliant window' : riskLevel === 'caution' ? 'Approaching limit' : 'Non-compliant';
            const employeeName = sanitizeText(cellTarget.dataset.employeeName || '');

            const tooltipContent = `
                <div class="calendar-tooltip__header">
                    <span class="calendar-tooltip__title">${escapeHtml(label)}</span>
                </div>
                <div class="calendar-tooltip__body">
                    ${employeeName ? `<span class="calendar-tooltip__employee">${escapeHtml(employeeName)}</span>` : ''}
                    ${dateValue ? `<span class="calendar-tooltip__dates">${escapeHtml(dateValue)}</span>` : ''}
                </div>
                <div class="calendar-tooltip__meta">
                    <span class="calendar-tooltip__metric">Days used: ${escapeHtml(riskDays)} / ${RISK_THRESHOLDS.limit}</span>
                </div>
            `.trim();

            this.tooltip.show(tooltipContent, event.pageX, event.pageY, { accent: riskColor });
            return;
        }
    };

    CalendarController.prototype.handleGridMousemove = function handleGridMousemove(event) {
        if (!this.tooltip || typeof this.tooltip.move !== 'function') {
            return;
        }
        this.pendingTooltipPosition.x = event.pageX;
        this.pendingTooltipPosition.y = event.pageY;
        if (this.tooltipMoveFrame) {
            return;
        }
        this.tooltipMoveFrame = requestAnimationFrame(() => {
            this.tooltipMoveFrame = null;
            this.tooltip.move(this.pendingTooltipPosition.x, this.pendingTooltipPosition.y);
        });
    };

    CalendarController.prototype.handleGridMouseout = function handleGridMouseout(event) {
        const nextTarget = event.relatedTarget;
        if (nextTarget && (nextTarget.closest('.calendar-trip') || nextTarget.closest('.calendar-cell'))) {
            return;
        }
        if (this.tooltipMoveFrame) {
            cancelAnimationFrame(this.tooltipMoveFrame);
            this.tooltipMoveFrame = null;
        }
        if (this.tooltip) {
            this.tooltip.hide();
        }
    };

    CalendarController.prototype.handleTripClick = function handleTripClick(event) {
        const target = event.target.closest('.calendar-trip');
        if (!target) {
            return;
        }
        event.preventDefault();
        const tripId = Number.parseInt(target.getAttribute('data-trip-id'), 10);
        if (!Number.isFinite(tripId)) {
            return;
        }
        this.closeContextMenu();
        this.lastFocusedTrip = target;
        this.openTripDetail(tripId, target);
    };

    CalendarController.prototype.handleTripKeydown = function handleTripKeydown(event) {
        const target = event.target.closest('.calendar-trip');
        if (!target) {
            return;
        }
        if (event.key === 'ContextMenu' || (event.shiftKey && (event.key === 'F10' || event.key === 'f10'))) {
            event.preventDefault();
            const rect = target.getBoundingClientRect();
            const x = rect.left + (rect.width / 2) + window.pageXOffset;
            const y = rect.top + rect.height + window.pageYOffset;
            this.openContextMenu(target, { x, y });
            return;
        }
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            const tripId = Number.parseInt(target.getAttribute('data-trip-id'), 10);
            if (!Number.isFinite(tripId)) {
                return;
            }
            this.closeContextMenu();
            this.lastFocusedTrip = target;
            this.openTripDetail(tripId, target);
        }
    };

    CalendarController.prototype.handleTripContextMenu = function handleTripContextMenu(event) {
        const trigger = event.target.closest('.calendar-trip');
        if (!trigger) {
            return;
        }
        event.preventDefault();
        this.openContextMenu(trigger, { x: event.pageX, y: event.pageY });
    };

    CalendarController.prototype.openContextMenu = function openContextMenu(trigger, coordinates = null) {
        if (!trigger || !this.contextMenuState || !this.contextMenuState.node) {
            return;
        }
        const tripId = Number.parseInt(trigger.getAttribute('data-trip-id'), 10);
        if (!Number.isFinite(tripId)) {
            return;
        }
        if (this.contextMenuState.isOpen && this.contextMenuState.tripId === tripId && trigger === this.contextMenuState.trigger) {
            return;
        }
        this.closeContextMenu();

        const menu = this.contextMenuState.node;
        this.contextMenuState.isOpen = true;
        this.contextMenuState.tripId = tripId;
        this.contextMenuState.trigger = trigger;

        menu.hidden = false;
        menu.setAttribute('aria-hidden', 'false');
        menu.setAttribute('data-trip-id', String(tripId));
        menu.dataset.tripId = String(tripId);
        menu.style.visibility = 'hidden';
        menu.style.display = 'block';

        let { x, y } = coordinates || {};
        if (!Number.isFinite(x) || !Number.isFinite(y)) {
            const rect = trigger.getBoundingClientRect();
            x = rect.left + (rect.width / 2) + window.pageXOffset;
            y = rect.top + rect.height + window.pageYOffset;
        }

        const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
        const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
        const menuRect = menu.getBoundingClientRect();
        const margin = 12;
        let left = x;
        let top = y;
        if (left + menuRect.width > viewportWidth - margin) {
            left = Math.max(margin, viewportWidth - menuRect.width - margin);
        }
        if (top + menuRect.height > viewportHeight - margin) {
            top = Math.max(margin, viewportHeight - menuRect.height - margin);
        }
        menu.style.left = `${left}px`;
        menu.style.top = `${top}px`;
        menu.style.visibility = 'visible';
        menu.focus({ preventScroll: true });
        const firstItem = menu.querySelector('.calendar-context-menu__item');
        if (firstItem) {
            firstItem.focus({ preventScroll: true });
        }

        document.addEventListener('pointerdown', this.handleOutsideContextPointer, true);
        document.addEventListener('contextmenu', this.handleOutsideContextPointer, true);
        if (document && document.body && document.body.dataset) {
            document.body.dataset.calendarContextMenuOpen = 'true';
        }
    };

    CalendarController.prototype.closeContextMenu = function closeContextMenu(options = {}) {
        if (!this.contextMenuState || !this.contextMenuState.node || !this.contextMenuState.isOpen) {
            return;
        }
        const { restoreFocus = false } = options;
        const menu = this.contextMenuState.node;
        menu.hidden = true;
        menu.setAttribute('aria-hidden', 'true');
        menu.style.display = 'none';
        menu.style.left = '';
        menu.style.top = '';
        menu.style.visibility = '';
        menu.removeAttribute('data-trip-id');

        document.removeEventListener('pointerdown', this.handleOutsideContextPointer, true);
        document.removeEventListener('contextmenu', this.handleOutsideContextPointer, true);
        if (document && document.body && document.body.dataset) {
            delete document.body.dataset.calendarContextMenuOpen;
        }

        const trigger = this.contextMenuState.trigger;
        this.contextMenuState.isOpen = false;
        this.contextMenuState.tripId = null;
        this.contextMenuState.trigger = null;

        if (restoreFocus && trigger && typeof trigger.focus === 'function') {
            trigger.focus();
        }
    };

    CalendarController.prototype.handleContextMenuClick = function handleContextMenuClick(event) {
        if (!this.contextMenuState || !this.contextMenuState.isOpen) {
            return;
        }
        const actionTarget = event.target.closest('.calendar-context-menu__item');
        if (!actionTarget) {
            return;
        }
        event.preventDefault();
        const action = actionTarget.getAttribute('data-menu-action');
        this.executeContextMenuAction(action);
    };

    CalendarController.prototype.executeContextMenuAction = function executeContextMenuAction(action) {
        if (!action || !this.contextMenuState) {
            this.closeContextMenu();
            return;
        }
        const tripId = this.contextMenuState.tripId;
        const trigger = this.contextMenuState.trigger;
        if (!Number.isFinite(tripId)) {
            this.closeContextMenu();
            return;
        }
        switch (action) {
            case 'edit':
                this.closeContextMenu();
                this.openForm('edit', tripId);
                break;
            case 'details':
            case 'summary':
                this.closeContextMenu();
                this.lastFocusedTrip = trigger;
                this.openTripDetail(tripId, trigger);
                break;
            case 'duplicate':
                this.closeContextMenu({ restoreFocus: true });
                this.duplicateTrip(tripId).catch((error) => {
                    console.error('[3.9-update-trip] Trip duplication failed', error);
                    this.showToast('Unable to duplicate trip ❌');
                });
                break;
            case 'delete':
                this.closeContextMenu();
                this.confirmAndDeleteTrip(tripId, trigger);
                break;
            default:
                this.closeContextMenu({ restoreFocus: true });
                break;
        }
    };

    CalendarController.prototype.handleOutsideContextPointer = function handleOutsideContextPointer(event) {
        if (!this.contextMenuState || !this.contextMenuState.isOpen) {
            return;
        }
        const menu = this.contextMenuState.node;
        const trigger = this.contextMenuState.trigger;
        const target = event.target;
        if (menu && menu.contains(target)) {
            return;
        }
        if (trigger && trigger.contains && trigger.contains(target)) {
            return;
        }
        this.closeContextMenu();
    };

    CalendarController.prototype.handleContextMenuKeydown = function handleContextMenuKeydown(event) {
        if (!this.contextMenuState || !this.contextMenuState.isOpen || !this.contextMenuState.node) {
            return;
        }
        const menu = this.contextMenuState.node;
        const items = Array.from(menu.querySelectorAll('.calendar-context-menu__item'));
        if (!items.length) {
            return;
        }
        const currentIndex = items.indexOf(document.activeElement);
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % items.length;
            items[nextIndex].focus();
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            const prevIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
            items[prevIndex].focus();
        } else if (event.key === 'Home') {
            event.preventDefault();
            items[0].focus();
        } else if (event.key === 'End') {
            event.preventDefault();
            items[items.length - 1].focus();
        } else if (event.key === 'Tab') {
            event.preventDefault();
            if (event.shiftKey) {
                const prevIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
                items[prevIndex].focus();
            } else {
                const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % items.length;
                items[nextIndex].focus();
            }
        } else if (event.key === 'Escape') {
            event.preventDefault();
            this.closeContextMenu({ restoreFocus: true });
        }
    };

    CalendarController.prototype.setForecastEmployee = function setForecastEmployee(employeeId, options = {}) {
        if (!this.elements.forecastPanel) {
            return;
        }
        const resolvedId = Number.isFinite(employeeId) ? employeeId : null;
        const employeeName = resolvedId ? this.resolveEmployeeName(resolvedId) : '';
        if (!resolvedId) {
            this.state.forecast.employeeId = null;
            this.state.forecast.employeeName = '';
            this.renderForecastEmpty('Select an employee to view forecast');
            return;
        }

        const previouslySelected = this.state.forecast.employeeId;
        this.state.forecast.employeeId = resolvedId;
        this.state.forecast.employeeName = employeeName;
        const shouldForce = options.force === true;
        const bypassCache = options.bypassCache === true;

        if (!shouldForce && !bypassCache && previouslySelected === resolvedId && this.forecastCache.has(resolvedId)) {
            this.renderForecastData(this.forecastCache.get(resolvedId));
            return;
        }

        this.renderForecastLoading(employeeName || `Employee ${resolvedId}`);
        this.fetchForecast(resolvedId, { bypassCache }).catch((error) => {
            console.error('Forecast fetch failed', error);
            this.renderForecastError(employeeName || `Employee ${resolvedId}`);
        });
    };

    CalendarController.prototype.resolveEmployeeName = function resolveEmployeeName(employeeId) {
        if (!Number.isFinite(employeeId)) {
            return '';
        }
        const list = Array.isArray(this.state.employees) ? this.state.employees : [];
        const match = list.find((employee) => employee.id === employeeId);
        return match ? match.name : '';
    };

    CalendarController.prototype.renderForecastLoading = function renderForecastLoading(employeeName) {
        if (!this.elements.forecastPanel) {
            return;
        }
        this.state.forecast.isLoading = true;
        this.elements.forecastPanel.classList.add('forecast-panel--loading');
        if (this.elements.forecastEmployee) {
            this.elements.forecastEmployee.textContent = employeeName ? `Loading ${employeeName}…` : 'Loading forecast…';
        }
        if (this.elements.forecastStatus) {
            this.elements.forecastStatus.textContent = 'Loading';
            this.elements.forecastStatus.classList.remove('forecast-panel__badge--warning', 'forecast-panel__badge--danger');
        }
        if (this.elements.forecastUsed) {
            this.elements.forecastUsed.textContent = '—';
        }
        if (this.elements.forecastUpcoming) {
            this.elements.forecastUpcoming.textContent = '—';
        }
        if (this.elements.forecastTotal) {
            this.elements.forecastTotal.textContent = '—';
        }
        if (this.elements.forecastProgress) {
            this.elements.forecastProgress.style.setProperty('--forecast-progress', '0%');
            this.elements.forecastProgress.style.background = '';
        }
        if (this.elements.forecastCaption) {
            this.elements.forecastCaption.textContent = 'Calculating usage…';
        }
        if (this.elements.forecastUpcomingWrapper) {
            this.elements.forecastUpcomingWrapper.hidden = true;
        }
        if (this.elements.forecastUpcomingList) {
            this.elements.forecastUpcomingList.innerHTML = '';
        }
        if (this.elements.forecastTimestamp) {
            this.elements.forecastTimestamp.textContent = 'Updating…';
            this.elements.forecastTimestamp.dateTime = '';
        }
    };

    CalendarController.prototype.renderForecastData = function renderForecastData(payload) {
        if (!this.elements.forecastPanel) {
            return;
        }
        if (!payload || typeof payload !== 'object') {
            this.renderForecastError(this.state.forecast.employeeName || '');
            return;
        }
        this.state.forecast.isLoading = false;
        this.elements.forecastPanel.classList.remove('forecast-panel--loading');

        const employeeName = (payload.employee && payload.employee.name) || this.state.forecast.employeeName || '';
        const riskLevel = payload.risk_level || 'safe';
        const usedDays = Number.isFinite(payload.used_days) ? payload.used_days : 0;
        const upcomingDays = Number.isFinite(payload.upcoming_days) ? payload.upcoming_days : 0;
        const projectedTotal = Number.isFinite(payload.projected_total) ? payload.projected_total : usedDays + upcomingDays;
        const updatedIso = payload.generated_at || payload.updated_at || new Date().toISOString();

        if (this.elements.forecastEmployee) {
            this.elements.forecastEmployee.textContent = employeeName ? `${employeeName}` : 'Forecast';
        }

        if (this.elements.forecastStatus) {
            const badge = this.elements.forecastStatus;
            badge.textContent = riskLevel === 'danger' ? 'High risk' : riskLevel === 'warning' ? 'Monitor' : 'Safe';
            badge.classList.remove('forecast-panel__badge--warning', 'forecast-panel__badge--danger');
            if (riskLevel === 'warning') {
                badge.classList.add('forecast-panel__badge--warning');
            } else if (riskLevel === 'danger') {
                badge.classList.add('forecast-panel__badge--danger');
            }
        }

        if (this.elements.forecastUsed) {
            this.elements.forecastUsed.textContent = `${usedDays} day${usedDays === 1 ? '' : 's'}`;
        }
        if (this.elements.forecastUpcoming) {
            this.elements.forecastUpcoming.textContent = `${upcomingDays} day${upcomingDays === 1 ? '' : 's'}`;
        }
        if (this.elements.forecastTotal) {
            this.elements.forecastTotal.textContent = `${projectedTotal} / 90 days`;
        }

        if (this.elements.forecastProgress) {
            const percent = Math.max(0, Math.min(100, Math.round((projectedTotal / RISK_THRESHOLDS.limit) * 100)));
            this.elements.forecastProgress.style.setProperty('--forecast-progress', `${percent}%`);
            let gradientStart = COLORS.safe;
            if (riskLevel === 'warning') {
                gradientStart = COLORS.warning;
            } else if (riskLevel === 'danger') {
                gradientStart = COLORS.critical;
            }
            this.elements.forecastProgress.style.background = `linear-gradient(90deg, ${gradientStart}, rgba(15, 23, 42, 0.12))`;
        }

        if (this.elements.forecastCaption) {
            let caption = 'Within 90-day limit';
            if (riskLevel === 'warning') {
                caption = 'Approaching 90-day limit';
            } else if (riskLevel === 'danger') {
                caption = 'Exceeds 90-day limit';
            }
            this.elements.forecastCaption.textContent = caption;
        }

        if (this.elements.forecastUpcomingWrapper && this.elements.forecastUpcomingList) {
            const upcomingTrips = Array.isArray(payload.upcoming_trips) ? payload.upcoming_trips : [];
            if (upcomingTrips.length) {
                const fragment = document.createDocumentFragment();
                upcomingTrips.forEach((trip) => {
                    const item = document.createElement('li');
                    const country = sanitizeText(trip.country || 'Trip');
                    const startIso = sanitizeText(trip.start_date || trip.entry_date || '');
                    const endIso = sanitizeText(trip.end_date || trip.exit_date || startIso);
                    const startDate = parseDate(startIso);
                    const endDate = parseDate(endIso);
                    const rangeLabel = formatDateRangeDisplay(startDate, endDate) || `${startIso} → ${endIso}`;
                    const duration = Number.isFinite(trip.duration_days) ? trip.duration_days : (startDate && endDate ? diffInDaysInclusive(startDate, endDate) + 1 : null);
                    item.innerHTML = `
                        <span class="forecast-panel__trip-destination">${escapeHtml(country)}</span>
                        <span class="forecast-panel__trip-range">${escapeHtml(rangeLabel)}</span>
                        ${duration ? `<span class="forecast-panel__trip-duration">${duration} day${duration === 1 ? '' : 's'}</span>` : ''}
                    `;
                    fragment.appendChild(item);
                });
                this.elements.forecastUpcomingWrapper.hidden = false;
                this.elements.forecastUpcomingList.innerHTML = '';
                this.elements.forecastUpcomingList.appendChild(fragment);
            } else {
                this.elements.forecastUpcomingWrapper.hidden = true;
                this.elements.forecastUpcomingList.innerHTML = '';
            }
        }

        if (this.elements.forecastTimestamp) {
            const updatedDate = parseDate(updatedIso);
            if (updatedDate instanceof Date && !Number.isNaN(updatedDate.getTime())) {
                this.elements.forecastTimestamp.dateTime = updatedDate.toISOString();
                this.elements.forecastTimestamp.textContent = formatDateTimeDisplay(updatedDate);
            } else {
                this.elements.forecastTimestamp.dateTime = '';
                this.elements.forecastTimestamp.textContent = 'Updated just now';
            }
        }

        if (!this.forecastCache) {
            this.forecastCache = new Map();
        }
        const activeEmployeeId = this.state.forecast.employeeId;
        if (Number.isFinite(activeEmployeeId)) {
            this.forecastCache.set(activeEmployeeId, payload);
        }
    };

    CalendarController.prototype.renderForecastEmpty = function renderForecastEmpty(message) {
        if (!this.elements.forecastPanel) {
            return;
        }
        this.state.forecast.isLoading = false;
        this.elements.forecastPanel.classList.remove('forecast-panel--loading');
        if (this.elements.forecastEmployee) {
            this.elements.forecastEmployee.textContent = message || 'No employee selected';
        }
        if (this.elements.forecastStatus) {
            this.elements.forecastStatus.textContent = '—';
            this.elements.forecastStatus.classList.remove('forecast-panel__badge--warning', 'forecast-panel__badge--danger');
        }
        if (this.elements.forecastUsed) {
            this.elements.forecastUsed.textContent = '—';
        }
        if (this.elements.forecastUpcoming) {
            this.elements.forecastUpcoming.textContent = '—';
        }
        if (this.elements.forecastTotal) {
            this.elements.forecastTotal.textContent = '—';
        }
        if (this.elements.forecastProgress) {
            this.elements.forecastProgress.style.setProperty('--forecast-progress', '0%');
            this.elements.forecastProgress.style.background = '';
        }
        if (this.elements.forecastCaption) {
            this.elements.forecastCaption.textContent = 'Forecast unavailable';
        }
        if (this.elements.forecastUpcomingWrapper) {
            this.elements.forecastUpcomingWrapper.hidden = true;
        }
        if (this.elements.forecastUpcomingList) {
            this.elements.forecastUpcomingList.innerHTML = '';
        }
        if (this.elements.forecastTimestamp) {
            this.elements.forecastTimestamp.textContent = '';
            this.elements.forecastTimestamp.dateTime = '';
        }
    };

    CalendarController.prototype.renderForecastError = function renderForecastError(employeeName) {
        this.renderForecastEmpty(employeeName ? `Unable to load forecast for ${employeeName}` : 'Unable to load forecast');
    };

    CalendarController.prototype.fetchForecast = async function fetchForecast(employeeId, options = {}) {
        if (!Number.isFinite(employeeId)) {
            return null;
        }
        if (!this.forecastCache) {
            this.forecastCache = new Map();
        }
        const bypassCache = options && options.bypassCache === true;
        if (!bypassCache && this.forecastCache.has(employeeId)) {
            const cached = this.forecastCache.get(employeeId);
            this.renderForecastData(cached);
            return cached;
        }

        if (this.forecastAbortController && typeof this.forecastAbortController.abort === 'function') {
            this.forecastAbortController.abort();
        }
        this.forecastAbortController = typeof AbortController === 'function' ? new AbortController() : null;
        const signal = this.forecastAbortController ? this.forecastAbortController.signal : undefined;

        try {
            const response = await fetch(`/api/forecast/${employeeId}`, {
                headers: { Accept: 'application/json' },
                signal
            });
            if (!response.ok) {
                throw new Error(`Forecast request failed (${response.status})`);
            }
            const payload = await response.json();
            this.renderForecastData(payload);
            return payload;
        } catch (error) {
            if (error && error.name === 'AbortError') {
                return null;
            }
            throw error;
        } finally {
            if (this.forecastAbortController && this.forecastAbortController.signal === signal) {
                this.forecastAbortController = null;
            }
        }
    };

    CalendarController.prototype.invalidateForecastForEmployee = function invalidateForecastForEmployee(employeeId) {
        if (!this.forecastCache || !Number.isFinite(employeeId)) {
            return;
        }
        this.forecastCache.delete(employeeId);
    };

    CalendarController.prototype.refreshForecastContext = function refreshForecastContext(options = {}) {
        const employees = Array.isArray(this.state.filteredEmployees) ? this.state.filteredEmployees : [];
        if (!employees.length) {
            this.renderForecastEmpty('No employees available');
            return;
        }
        const activeId = this.state.forecast.employeeId;
        const availableIds = new Set(employees.map((employee) => employee.id));
        if (Number.isFinite(activeId) && availableIds.has(activeId)) {
            if (options.force) {
                this.setForecastEmployee(activeId, { force: true, bypassCache: options.bypassCache });
            }
            return;
        }
        let fallbackId = null;
        if (Number.isFinite(this.focusEmployeeId) && availableIds.has(this.focusEmployeeId)) {
            fallbackId = this.focusEmployeeId;
        } else if (employees.length) {
            fallbackId = employees[0].id;
        }
        if (Number.isFinite(fallbackId)) {
            this.setForecastEmployee(fallbackId, { force: true });
        } else {
            this.renderForecastEmpty('No employees available');
        }
    };

    CalendarController.prototype.confirmAndDeleteTrip = function confirmAndDeleteTrip(tripId, trigger) {
        if (!Number.isFinite(tripId)) {
            return;
        }
        const trip = this.state.tripIndex.get(tripId);
        const employee = trip && trip.employeeName ? trip.employeeName : 'this employee';
        const country = trip && trip.country ? `${trip.country} trip` : 'trip';
        const confirmed = typeof window !== 'undefined' && typeof window.confirm === 'function'
            ? window.confirm(`Delete ${country} for ${employee}? This action cannot be undone.`)
            : true;
        if (!confirmed) {
            if (trigger && typeof trigger.focus === 'function') {
                trigger.focus();
            }
            return;
        }
        this.deleteTrip(tripId).catch((error) => {
            console.error('[3.9-update-trip] Trip deletion failed', error);
            this.showToast('Unable to delete trip ❌');
        });
    };

    CalendarController.prototype.deleteTrip = async function deleteTrip(tripId) {
        if (!Number.isFinite(tripId)) {
            return;
        }
        const existingTrip = this.state.tripIndex.get(tripId);
        const employeeId = existingTrip && Number.isFinite(existingTrip.employeeId) ? existingTrip.employeeId : null;
        if (Number.isFinite(employeeId)) {
            this.invalidateForecastForEmployee(employeeId);
        }
        const legacyDelete = async () => {
            const fallback = await fetch(`/api/trips/${tripId}`, {
                method: 'DELETE',
                headers: { Accept: 'application/json' }
            });
            if (!fallback.ok) {
                let fallbackMessage = `Delete failed (${fallback.status})`;
                try {
                    const fallbackPayload = await fallback.json();
                    if (fallbackPayload && typeof fallbackPayload.error === 'string') {
                        fallbackMessage = fallbackPayload.error;
                    }
                } catch (fallbackParseError) {
                    // Ignore legacy parse failures.
                }
                throw new Error(fallbackMessage);
            }
        };

        // # Phase 3.9 — prefer unified calendar sync API when present
        // # Phase 3.9 — prefer unified calendar sync API when present
        // # Phase 3.9 — prefer unified calendar sync API when present
        // # Phase 3.9 — prefer unified calendar sync API when present
        const syncApi = typeof window !== 'undefined' ? window.CalendarSync && window.CalendarSync.api : null;
        if (syncApi && typeof syncApi.deleteTrip === 'function') {
            await syncApi.deleteTrip({ trip_id: tripId });
        } else {
            let response;
            try {
                response = await fetch('/api/delete_trip', {
                    method: 'POST',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ trip_id: tripId })
                });
            } catch (networkError) {
                throw networkError;
            }
            if (!response.ok) {
                if (response.status === 404) {
                    await legacyDelete();
                } else {
                    let message = `Delete failed (${response.status})`;
                    try {
                        const payload = await response.json();
                        if (payload && typeof payload.error === 'string') {
                            message = payload.error;
                        }
                    } catch (parseError) {
                        // Ignore parse errors, retain fallback message.
                    }
                    throw new Error(message);
                }
            } else {
                try {
                    const payload = await response.json();
                    if (payload && typeof payload.error === 'string') {
                        throw new Error(payload.error);
                    }
                } catch (parseError) {
                    // Ignore JSON parse errors when payload not present.
                }
            }
        }

        if (this.isDetailOpen && this.activeTripId === tripId) {
            this.closeTripDetail({ skipFocus: true });
        }

        await this.loadData({ force: true, centerOnToday: false });
        if (Number.isFinite(employeeId)) {
            this.setForecastEmployee(employeeId, { force: true, bypassCache: true, reason: 'delete' });
        } else {
            this.refreshForecastContext({ force: true });
        }
        console.info('[3.9-update-trip] Trip %s deleted', tripId);
        this.showToast('Trip deleted ✅');
    };

    CalendarController.prototype.duplicateTrip = async function duplicateTrip(tripId) {
        if (!Number.isFinite(tripId)) {
            throw new Error('Invalid trip identifier.');
        }
        let sourceTrip = this.state.tripIndex.get(tripId);
        if (!sourceTrip) {
            try {
                const lookup = await fetch(`/api/trips/${tripId}`, { headers: { Accept: 'application/json' } });
                if (lookup.ok) {
                    const payload = await lookup.json();
                    const normalised = normaliseTrip(payload);
                    if (normalised) {
                        sourceTrip = normalised;
                        this.state.tripIndex.set(normalised.id, normalised);
                    }
                }
            } catch (error) {
                console.error('Trip lookup failed during duplication', error);
            }
        }
        if (!sourceTrip) {
            throw new Error('Trip not found for duplication.');
        }

        const payload = {
            employee_id: sourceTrip.employeeId,
            country: sourceTrip.country,
            start_date: serialiseDate(sourceTrip.start),
            end_date: serialiseDate(sourceTrip.end)
        };
        if (sourceTrip.jobRef) {
            payload.job_ref = sourceTrip.jobRef;
        }
        if (sourceTrip.purpose) {
            payload.purpose = sourceTrip.purpose;
        }

        const syncApi = typeof window !== 'undefined' ? window.CalendarSync && window.CalendarSync.api : null;
        let result;
        if (syncApi && typeof syncApi.duplicateTrip === 'function') {
            result = await syncApi.duplicateTrip({ trip_id: tripId, overrides: payload });
        } else {
            let response;
            try {
                response = await fetch('/api/duplicate_trip', {
                    method: 'POST',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ trip_id: tripId, overrides: payload })
                });
            } catch (networkError) {
                throw networkError;
            }
            if (!response.ok) {
                if (response.status === 404) {
                    response = await fetch('/api/trips', {
                        method: 'POST',
                        headers: {
                            Accept: 'application/json',
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });
                    if (!response.ok) {
                        let legacyMessage = `Duplicate failed (${response.status})`;
                        try {
                            const legacyErrorPayload = await response.json();
                            if (legacyErrorPayload && typeof legacyErrorPayload.error === 'string') {
                                legacyMessage = legacyErrorPayload.error;
                            }
                        } catch (legacyParseError) {
                            // Ignore parse failures for legacy flow.
                        }
                        throw new Error(legacyMessage);
                    }
                } else {
                    let message = `Duplicate failed (${response.status})`;
                    try {
                        const errorPayload = await response.json();
                        if (errorPayload && typeof errorPayload.error === 'string') {
                            message = errorPayload.error;
                        }
                    } catch (parseError) {
                        // Ignore parse errors and retain fallback message.
                    }
                    throw new Error(message);
                }
            }
            result = await response.json();
        }
        const normalised = normaliseTrip(result);
        if (!normalised) {
            throw new Error('Unexpected duplicate payload.');
        }
        this.pendingCenterDate = normalised.start instanceof Date ? normalised.start : parseDate(normalised.start);
        this.pendingFocusTripId = normalised.id;
        this.invalidateForecastForEmployee(normalised.employeeId);
        await this.loadData({
            force: true,
            centerOnToday: false,
            centerOnDate: this.pendingCenterDate instanceof Date ? this.pendingCenterDate : null
        });
        if (Number.isFinite(normalised.employeeId)) {
            this.setForecastEmployee(normalised.employeeId, { force: true, bypassCache: true, reason: 'duplicate' });
        }
        if (this.pendingCenterDate instanceof Date) {
            this.centerOnDate(this.pendingCenterDate);
            this.pendingCenterDate = null;
        }
        if (Number.isFinite(this.pendingFocusTripId)) {
            this.openTripDetail(this.pendingFocusTripId);
            this.pendingFocusTripId = null;
        }
        this.showToast('Trip duplicated ✅');
        console.info('[3.9-update-trip] Trip %s duplicated as %s', tripId, normalised.id);
    };

    CalendarController.prototype.isFullscreen = function isFullscreen() {
        if (typeof document === 'undefined') {
            return false;
        }
        return Boolean(document.fullscreenElement);
    };

    CalendarController.prototype.getFullscreenTarget = function getFullscreenTarget() {
        return document && document.documentElement ? document.documentElement : null;
    };

    CalendarController.prototype.enterFullscreen = async function enterFullscreen() {
        const target = this.getFullscreenTarget();
        if (!target || typeof target.requestFullscreen !== 'function') {
            this.showToast('Fullscreen is not supported in this browser ❌');
            return;
        }
        try {
            await target.requestFullscreen({ navigationUI: 'hide' });
        } catch (error) {
            try {
                await target.requestFullscreen();
            } catch (fallbackError) {
                console.error('Fullscreen request failed', fallbackError || error);
                this.showToast('Unable to enter full screen ❌');
            }
        }
    };

    CalendarController.prototype.exitFullscreen = async function exitFullscreen() {
        if (typeof document === 'undefined' || typeof document.exitFullscreen !== 'function') {
            return;
        }
        try {
            await document.exitFullscreen();
        } catch (error) {
            console.error('Fullscreen exit failed', error);
        }
    };

    CalendarController.prototype.handleFullscreenToggle = function handleFullscreenToggle(event) {
        if (event) {
            event.preventDefault();
        }
        this.closeContextMenu();
        if (this.isFullscreen()) {
            this.exitFullscreen();
        } else {
            this.enterFullscreen();
        }
    };

    CalendarController.prototype.handleFullscreenChange = function handleFullscreenChange() {
        const active = this.isFullscreen();
        if (this.root) {
            this.root.classList.toggle('calendar-shell--fullscreen', active);
        }
        if (document && document.body) {
            document.body.classList.toggle('calendar-body--fullscreen', active);
        }
        this.syncFullscreenButton();
    };

    CalendarController.prototype.toggleAlertsPanel = function toggleAlertsPanel() {
        if (!this.elements.alertsPanel || !this.elements.alertsToggle) {
            return;
        }
        const isCollapsed = this.elements.alertsPanel.classList.contains('collapsed');
        if (isCollapsed) {
            this.elements.alertsPanel.classList.remove('collapsed');
            this.elements.alertsToggle.textContent = '×';
            this.elements.alertsToggle.setAttribute('title', 'Hide alerts panel');
            this.elements.alertsToggle.setAttribute('aria-label', 'Hide alerts panel');
        } else {
            this.elements.alertsPanel.classList.add('collapsed');
            this.elements.alertsToggle.textContent = '☰';
            this.elements.alertsToggle.setAttribute('title', 'Show alerts panel');
            this.elements.alertsToggle.setAttribute('aria-label', 'Show alerts panel');
        }
    };

    CalendarController.prototype.syncFullscreenButton = function syncFullscreenButton() {
        if (!this.elements.fullscreenToggle) {
            return;
        }
        const active = this.isFullscreen();
        const label = active ? 'Exit full screen' : 'Enter full screen';
        this.elements.fullscreenToggle.setAttribute('aria-pressed', active ? 'true' : 'false');
        this.elements.fullscreenToggle.setAttribute('aria-label', label);
        this.elements.fullscreenToggle.classList.toggle('is-active', active);
        const labelNode = this.elements.fullscreenToggle.querySelector('.calendar-btn-label');
        if (labelNode) {
            labelNode.textContent = active ? 'Exit' : 'Full Screen';
        }
    };

    CalendarController.prototype.handleOverlayInteraction = function handleOverlayInteraction(event) {
        if (event.target === this.elements.detailOverlay) {
            this.closeTripDetail();
        }
    };

    CalendarController.prototype.handleGlobalKeydown = function handleGlobalKeydown(event) {
        if (event.key !== 'Escape') {
            return;
        }
        if (this.contextMenuState && this.contextMenuState.isOpen) {
            event.preventDefault();
            this.closeContextMenu({ restoreFocus: true });
            return;
        }
        if (this.state.formMode) {
            event.preventDefault();
            this.closeForm();
            return;
        }
        if (this.isDetailOpen) {
            event.preventDefault();
            this.closeTripDetail();
        }
    };

    CalendarController.prototype.handleWindowResize = function handleWindowResize() {
        this.closeContextMenu();
        if (this.resizeFrame) {
            cancelAnimationFrame(this.resizeFrame);
        }
        this.resizeFrame = window.requestAnimationFrame(() => {
            this.updateTodayMarker();
            this.resizeFrame = null;
        });
    };

    CalendarController.prototype.openTripDetail = function openTripDetail(tripId, originElement) {
        if (!this.elements.detailOverlay) {
            return;
        }
        this.closeContextMenu();
        const targetElement = originElement || (this.elements.grid ? this.elements.grid.querySelector(`.calendar-trip[data-trip-id="${tripId}"]`) : null);
        const detailDataRemaining = targetElement && targetElement.dataset ? targetElement.dataset.daysRemaining || '' : '';
        const detailForecastRemaining = targetElement && targetElement.dataset ? targetElement.dataset.forecastRemaining || '' : '';
        let trip = this.state.tripIndex.get(tripId);
        let status = this.state.tripStatus.get(tripId);
        if (!trip && targetElement) {
            const dataset = targetElement.dataset || {};
            const startIso = dataset.start;
            const endIso = dataset.end;
            const startDate = parseDate(startIso);
            const endDate = parseDate(endIso);
            const fallbackDuration = startDate && endDate ? diffInDaysInclusive(startDate, endDate) + 1 : null;
            trip = {
                id: tripId,
                employeeId: Number.parseInt(dataset.employeeId || '', 10) || null,
                employeeName: dataset.employee || 'Unknown employee',
                country: dataset.country || '',
                jobRef: dataset.jobRef || '',
                purpose: dataset.purpose || '',
                ghosted: targetElement.classList.contains('calendar-trip--ghosted'),
                travelDays: Number.parseInt(dataset.daysUsed || '', 10),
                durationDays: Number.isFinite(fallbackDuration) ? fallbackDuration : null,
                start: startDate || null,
                end: endDate || startDate || null,
                createdAt: null,
                updatedAt: null
            };
            if (!Number.isFinite(trip.travelDays) && Number.isFinite(trip.durationDays)) {
                trip.travelDays = trip.durationDays;
            }
            if (!status) {
                status = {
                    status: dataset.compliance || 'safe',
                    daysUsed: Number.parseInt(dataset.daysUsed || '', 10)
                };
            }
            this.state.tripIndex.set(tripId, trip);
            if (status && !this.state.tripStatus.has(tripId)) {
                this.state.tripStatus.set(tripId, status);
            }
        }
        if (!trip) {
            return;
        }
        const statusData = status || this.state.tripStatus.get(tripId) || { status: 'safe', daysUsed: trip.travelDays };
        const statusKey = typeof statusData.status === 'string' ? statusData.status : 'safe';
        const statusLabel = normaliseStatusLabel(statusKey);
        const statusColor = COLORS[statusKey] || COLORS.safe;
        const employeeName = trip.employeeName || 'Unknown employee';

        if (this.elements.detailStatus) {
            this.elements.detailStatus.textContent = statusLabel;
            this.elements.detailStatus.classList.remove('calendar-detail-label--safe', 'calendar-detail-label--warning', 'calendar-detail-label--critical');
            this.elements.detailStatus.classList.add(`calendar-detail-label--${statusKey}`);
        }
        if (this.elements.detailStatusDot) {
            this.elements.detailStatusDot.classList.remove('trip-color--safe', 'trip-color--warning', 'trip-color--critical');
            this.elements.detailStatusDot.classList.add(`trip-color--${statusKey}`);
            this.elements.detailStatusDot.style.backgroundColor = statusColor;
            this.elements.detailStatusDot.setAttribute('data-status', statusKey);
        }
        if (this.elements.detailEmployee) {
            this.elements.detailEmployee.textContent = employeeName;
        }
        if (this.elements.detailCountry) {
            this.elements.detailCountry.textContent = trip.country || '—';
        }
        if (this.elements.detailTitle) {
            this.elements.detailTitle.textContent = trip.country ? `Trip to ${trip.country}` : 'Trip details';
        }
        if (this.elements.detailDates) {
            this.elements.detailDates.textContent = formatDateRangeDisplay(trip.start, trip.end) || '—';
        }
        if (this.elements.detailDuration) {
            this.elements.detailDuration.textContent = formatDuration(trip.durationDays) || '—';
        }
        if (this.elements.detailUsage) {
            const daysUsedValue = Number.isFinite(statusData.daysUsed) ? statusData.daysUsed : trip.travelDays;
            const daysUsedLabel = Number.isFinite(daysUsedValue)
                ? `${daysUsedValue} day${daysUsedValue === 1 ? '' : 's'}`
                : '—';
            this.elements.detailUsage.textContent = daysUsedLabel === '—' ? statusLabel : `${daysUsedLabel} (${statusLabel})`;
        }
        if (this.elements.detailRemaining) {
            let remainingValue = null;
            const attrValue = detailForecastRemaining || detailDataRemaining;
            if (attrValue && attrValue.trim().length) {
                const parsed = Number(attrValue);
                remainingValue = Number.isFinite(parsed) ? parsed : attrValue;
            } else if (Number.isFinite(statusData.daysUsed)) {
                remainingValue = RISK_THRESHOLDS.limit - statusData.daysUsed;
            }
            if (typeof remainingValue === 'number') {
                this.elements.detailRemaining.textContent = formatDayCountLabel(remainingValue);
                const statusKeyForRemaining = remainingValue <= 0
                    ? 'critical'
                    : remainingValue < this.warningThreshold
                        ? 'warning'
                        : 'safe';
                this.elements.detailRemaining.dataset.status = statusKeyForRemaining;
            } else if (typeof remainingValue === 'string' && remainingValue.trim().length) {
                this.elements.detailRemaining.textContent = remainingValue;
                this.elements.detailRemaining.dataset.status = 'unknown';
            } else {
                this.elements.detailRemaining.textContent = '—';
                this.elements.detailRemaining.dataset.status = 'unknown';
            }
        }

        const noteCopy = trip.purpose || trip.notes || '';
        if (this.elements.detailNotes && this.elements.detailPurpose) {
            if (noteCopy) {
                this.elements.detailNotes.hidden = false;
                this.elements.detailPurpose.textContent = noteCopy;
            } else {
                this.elements.detailNotes.hidden = true;
                this.elements.detailPurpose.textContent = '';
            }
        }

        if (this.elements.detailJobRef && this.elements.detailJobRefValue) {
            if (trip.jobRef) {
                this.elements.detailJobRef.hidden = false;
                this.elements.detailJobRefValue.textContent = trip.jobRef;
            } else {
                this.elements.detailJobRef.hidden = true;
                this.elements.detailJobRefValue.textContent = '';
            }
        }

        if (this.elements.detailCreated && this.elements.detailCreatedValue) {
            const createdText = formatDateTimeDisplay(trip.createdAt);
            this.elements.detailCreated.hidden = !createdText;
            this.elements.detailCreatedValue.textContent = createdText || '';
        }

        if (this.elements.detailUpdated && this.elements.detailUpdatedValue) {
            const updatedText = formatDateTimeDisplay(trip.updatedAt);
            this.elements.detailUpdated.hidden = !updatedText;
            this.elements.detailUpdatedValue.textContent = updatedText || '';
        }

        this.elements.detailOverlay.hidden = false;
        this.isDetailOpen = true;
        this.activeTripId = tripId;
        this.updateGlobalEditButtonState();
        this.tooltip.hide();

        if (Number.isFinite(trip.employeeId)) {
            this.setForecastEmployee(trip.employeeId, { reason: 'trip-detail' });
        }

        if (typeof document !== 'undefined' && document.body) {
            document.body.dataset.calendarDetailOpen = 'true';
        }
        this.updateBodyScrollLock();

        window.requestAnimationFrame(() => {
            if (this.elements.detail) {
                this.elements.detail.focus();
            } else if (this.elements.detailClose) {
                this.elements.detailClose.focus();
            }
        });
    };

    CalendarController.prototype.closeTripDetail = function closeTripDetail(options = {}) {
        if (!this.isDetailOpen) {
            return;
        }
        if (this.elements.detailOverlay) {
            this.elements.detailOverlay.hidden = true;
        }
        if (typeof document !== 'undefined' && document.body) {
            delete document.body.dataset.calendarDetailOpen;
        }
        this.isDetailOpen = false;
        this.activeTripId = null;
        this.updateGlobalEditButtonState();
        this.updateBodyScrollLock();
        if (!options.skipFocus && this.lastFocusedTrip && typeof this.lastFocusedTrip.focus === 'function') {
            this.lastFocusedTrip.focus();
        }
    };

    CalendarController.prototype.updateBodyScrollLock = function updateBodyScrollLock() {
        if (typeof document === 'undefined' || !document.body) {
            return;
        }
        const shouldLock = this.isDetailOpen || Boolean(this.state.formMode);
        if (shouldLock) {
            document.body.style.overflow = 'hidden';
            document.body.dataset.calendarModalOpen = 'true';
        } else {
            document.body.style.overflow = '';
            delete document.body.dataset.calendarModalOpen;
        }
    };

    // Displays a transient toast message for positive feedback — Author: GPT-5 Codex
    CalendarController.prototype.showToast = function showToast(message) {
        const toast = this.elements.toast;
        if (!toast) {
            return;
        }
        const copy = typeof message === 'string' && message.trim().length ? message : 'Data updated successfully ✅';
        if (this.toastTimer) {
            window.clearTimeout(this.toastTimer);
            this.toastTimer = null;
        }
        toast.textContent = copy;
        toast.setAttribute('aria-hidden', 'false');
        toast.classList.add('calendar-toast--visible');
        this.toastTimer = window.setTimeout(() => {
            this.hideToast();
        }, 3000);
    };

    // Hides the active toast message to keep UI uncluttered — Author: GPT-5 Codex
    CalendarController.prototype.hideToast = function hideToast() {
        const toast = this.elements.toast;
        if (!toast) {
            return;
        }
        if (this.toastTimer) {
            window.clearTimeout(this.toastTimer);
            this.toastTimer = null;
        }
        toast.classList.remove('calendar-toast--visible');
        toast.setAttribute('aria-hidden', 'true');
    };

    // Syncs the global edit button state with the current selection — Author: GPT-5 Codex
    CalendarController.prototype.updateGlobalEditButtonState = function updateGlobalEditButtonState() {
        const button = this.elements.editTripGlobal;
        if (!button) {
            return;
        }
        const hasActiveTrip = Number.isFinite(this.activeTripId);
        button.disabled = !hasActiveTrip;
        if (hasActiveTrip) {
            button.removeAttribute('aria-disabled');
        } else {
            button.setAttribute('aria-disabled', 'true');
        }
    };

    CalendarController.prototype.clearFormFeedback = function clearFormFeedback() {
        if (!this.elements.formFeedback) {
            return;
        }
        this.elements.formFeedback.textContent = '';
        this.elements.formFeedback.hidden = true;
        this.elements.formFeedback.removeAttribute('role');
        this.elements.formFeedback.classList.remove('calendar-form-feedback--success', 'calendar-form-feedback--info');
    };

    CalendarController.prototype.showFormFeedback = function showFormFeedback(message, tone = 'error') {
        if (!this.elements.formFeedback) {
            return;
        }
        this.elements.formFeedback.textContent = message;
        this.elements.formFeedback.hidden = false;
        this.elements.formFeedback.classList.remove('calendar-form-feedback--success', 'calendar-form-feedback--info');
        if (tone === 'success') {
            this.elements.formFeedback.classList.add('calendar-form-feedback--success');
            this.elements.formFeedback.setAttribute('role', 'status');
        } else if (tone === 'info') {
            this.elements.formFeedback.classList.add('calendar-form-feedback--info');
            this.elements.formFeedback.setAttribute('role', 'status');
        } else {
            this.elements.formFeedback.setAttribute('role', 'alert');
        }
    };

    CalendarController.prototype.populateEmployeeSelect = function populateEmployeeSelect(selectedId) {
        if (!this.elements.formEmployee) {
            return;
        }
        const select = this.elements.formEmployee;
        const targetValue = typeof selectedId === 'number' ? String(selectedId) : (selectedId ? String(selectedId) : '');
        const employees = Array.isArray(this.state.employees) ? this.state.employees : [];

        select.innerHTML = '';

        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = employees.length ? 'Select employee…' : 'No employees available';
        placeholder.disabled = true;
        placeholder.hidden = true;
        select.appendChild(placeholder);

        employees.forEach((employee) => {
            const option = document.createElement('option');
            option.value = String(employee.id);
            option.textContent = employee.active ? employee.name : `${employee.name} (inactive)`;
            option.dataset.active = employee.active ? 'true' : 'false';
            select.appendChild(option);
        });

        if (targetValue && select.querySelector(`option[value="${targetValue}"]`)) {
            select.value = targetValue;
        } else {
            select.value = '';
        }
        select.disabled = employees.length === 0;
        if (employees.length > 0 && this.state.formMode) {
            this.clearFormFeedback();
        }
    };

    CalendarController.prototype.rebuildAlertIndex = function rebuildAlertIndex() {
        const alerts = Array.isArray(this.state.alerts) ? this.state.alerts : [];
        const index = new Map();
        for (const alert of alerts) {
            if (!alert) {
                continue;
            }
            const employeeId = Number.parseInt(alert.employee_id, 10);
            if (Number.isNaN(employeeId)) {
                continue;
            }
            index.set(employeeId, alert);
        }
        this.state.alertIndex = index;
    };

    CalendarController.prototype.setAlertFilter = function setAlertFilter(filter) {
        const allowed = new Set(['all', 'warning', 'critical', 'yellow', 'orange', 'red']);
        const resolved = typeof filter === 'string' ? filter.toLowerCase() : 'all';
        const target = allowed.has(resolved) ? resolved : 'all';
        if (this.state.alertFilter === target) {
            this.updateAlertFilterUI();
            this.renderAlertsPanel();
            return;
        }
        this.state.alertFilter = target;
        this.updateAlertFilterUI();
        this.renderAlertsPanel();
    };

    CalendarController.prototype.updateAlertFilterUI = function updateAlertFilterUI() {
        if (!this.elements.alertsFilters || !this.elements.alertsFilters.length) {
            return;
        }
        const filter = this.state.alertFilter || 'all';
        this.elements.alertsFilters.forEach((button) => {
            const value = button.getAttribute('data-alert-filter') || 'all';
            const isActive = value === filter;
            button.classList.toggle('is-active', isActive);
            button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
    };

    CalendarController.prototype.renderAlertsPanel = function renderAlertsPanel() {
        if (!this.elements.alertsList) {
            return;
        }
        const alerts = Array.isArray(this.state.alerts) ? this.state.alerts : [];
        const filter = this.state.alertFilter || 'all';
        const normalizedAlerts = alerts.map((alert) => ({
            ...alert,
            risk_level: typeof alert.risk_level === 'string' ? alert.risk_level.toUpperCase() : ''
        }));

        const filtered = normalizedAlerts.filter((alert) => {
            const level = alert.risk_level;
            switch (filter) {
                case 'critical':
                case 'red':
                    return level === 'RED';
                case 'warning':
                    return level === 'YELLOW' || level === 'ORANGE';
                case 'orange':
                    return level === 'ORANGE';
                case 'yellow':
                    return level === 'YELLOW';
                case 'all':
                case 'green':
                default:
                    return true;
            }
        });

        const totals = {
            all: normalizedAlerts.length,
            warning: normalizedAlerts.filter((alert) => alert.risk_level === 'YELLOW' || alert.risk_level === 'ORANGE').length,
            critical: normalizedAlerts.filter((alert) => alert.risk_level === 'RED').length,
            yellow: normalizedAlerts.filter((alert) => alert.risk_level === 'YELLOW').length,
            orange: normalizedAlerts.filter((alert) => alert.risk_level === 'ORANGE').length,
            red: normalizedAlerts.filter((alert) => alert.risk_level === 'RED').length
        };

        if (this.elements.alertsFilters && this.elements.alertsFilters.length) {
            this.elements.alertsFilters.forEach((button) => {
                const value = button.getAttribute('data-alert-filter') || 'all';
                const count =
                    totals[value] !== undefined
                        ? totals[value]
                        : value === 'all'
                            ? totals.all
                            : 0;
                button.dataset.count = String(count);
                const badge = button.querySelector('.calendar-alerts-filter-count');
                if (badge) {
                    badge.textContent = String(count);
                }
            });
        }

        this.elements.alertsList.innerHTML = '';
        if (this.elements.alertsEmpty) {
            this.elements.alertsEmpty.hidden = filtered.length !== 0;
        }

        if (!filtered.length) {
            this.updateAlertFilterUI();
            return;
        }

        const fragment = document.createDocumentFragment();
        for (const alert of filtered) {
            const item = document.createElement('li');
            const levelKey = alert.risk_level || 'YELLOW';
            item.className = `calendar-alerts-item calendar-alerts-item--${levelKey.toLowerCase()}`;
            item.setAttribute('data-alert-id', String(alert.id));
            item.setAttribute('data-employee-id', String(alert.employee_id));
            item.tabIndex = -1;

            const content = document.createElement('div');
            content.className = 'calendar-alerts-item-content';

            const meta = document.createElement('div');
            meta.className = 'calendar-alerts-item-meta';

            const pill = document.createElement('span');
            pill.className = `calendar-alerts-item-pill calendar-alerts-item-pill--${levelKey.toLowerCase()}`;
            const riskLabel = levelKey === 'RED' ? 'Critical' : levelKey === 'ORANGE' ? 'High warning' : 'Warning';
            pill.textContent = riskLabel;
            meta.appendChild(pill);

            if (alert.created_at) {
                const timestamp = formatAlertTimestamp(alert.created_at);
                if (timestamp.label) {
                    const time = document.createElement('time');
                    time.className = 'calendar-alerts-item-time';
                    if (timestamp.iso) {
                        time.setAttribute('datetime', timestamp.iso);
                    }
                    time.textContent = timestamp.label;
                    meta.appendChild(time);
                }
            }

            content.appendChild(meta);

            const title = document.createElement('h3');
            title.className = 'calendar-alerts-item-title';
            title.textContent = sanitizeText(alert.employee_name || 'Employee');
            content.appendChild(title);

            const message = document.createElement('p');
            message.className = 'calendar-alerts-item-message';
            message.textContent = sanitizeText(alert.message || '');
            content.appendChild(message);

            const alertDaysUsed = Number(alert.days_used);
            if (Number.isFinite(alertDaysUsed)) {
                const usage = document.createElement('p');
                usage.className = 'calendar-alerts-item-usage';
                const daysRemaining = Number.isFinite(Number(alert.days_remaining))
                    ? Number(alert.days_remaining)
                    : (RISK_THRESHOLDS.limit - alertDaysUsed);
                const remainingLabel = daysRemaining >= 0
                    ? `${daysRemaining} days remaining`
                    : `${Math.abs(daysRemaining)} days over limit`;
                usage.textContent = `${alertDaysUsed}/${RISK_THRESHOLDS.limit} days used · ${remainingLabel}`;
                content.appendChild(usage);
            }

            item.appendChild(content);

            const actions = document.createElement('div');
            actions.className = 'calendar-alerts-item-actions';

            const resolveBtn = document.createElement('button');
            resolveBtn.type = 'button';
            resolveBtn.className = 'calendar-alerts-resolve';
            resolveBtn.setAttribute('data-action', 'resolve-alert');
            resolveBtn.setAttribute('data-alert-id', String(alert.id));
            resolveBtn.setAttribute('data-employee-id', String(alert.employee_id));
            resolveBtn.textContent = 'Resolve';
            actions.appendChild(resolveBtn);

            item.appendChild(actions);
            fragment.appendChild(item);
        }

        this.elements.alertsList.appendChild(fragment);
        this.updateAlertFilterUI();
    };

    CalendarController.prototype.createAlertIcon = function createAlertIcon(alert) {
        if (!alert) {
            return null;
        }
        const level = typeof alert.risk_level === 'string' ? alert.risk_level.toUpperCase() : null;
        if (!level) {
            return null;
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `calendar-employee-alert calendar-employee-alert--${level.toLowerCase()}`;
        button.setAttribute('data-alert-level', level);
        button.setAttribute('data-employee-id', String(alert.employee_id));
        button.innerHTML = '<span aria-hidden="true">⚠️</span>';

        const statusLabel = level === 'RED' ? 'Critical risk' : level === 'ORANGE' ? 'High risk' : 'Warning';
        const employeeName = sanitizeText(alert.employee_name || '');
        const safeMessage = sanitizeText(alert.message || '');
        const ariaLabelParts = [
            statusLabel,
            employeeName ? `for ${employeeName}` : '',
            safeMessage
        ].filter(Boolean);
        button.setAttribute('aria-label', ariaLabelParts.join('. '));

        const accent = ALERT_COLORS[level] || ALERT_COLORS.YELLOW;
        const showTooltip = (event) => {
            if (!this.tooltip) {
                return;
            }
            const tooltipContent = `
                <div class="calendar-alert-tooltip-heading">${escapeHtml(statusLabel)}</div>
                <div class="calendar-alert-tooltip-body">${escapeHtml(safeMessage)}</div>
            `;
            this.tooltip.show(tooltipContent, event.pageX, event.pageY, { accent });
        };
        const moveTooltip = (event) => {
            if (!this.tooltip) {
                return;
            }
            this.tooltip.move(event.pageX, event.pageY);
        };
        const hideTooltip = () => {
            if (this.tooltip) {
                this.tooltip.hide();
            }
        };

        button.addEventListener('mouseenter', showTooltip);
        button.addEventListener('focus', showTooltip);
        button.addEventListener('mousemove', moveTooltip);
        button.addEventListener('mouseleave', hideTooltip);
        button.addEventListener('blur', hideTooltip);
        button.addEventListener('click', (event) => {
            event.preventDefault();
            this.focusAlertForEmployee(Number.parseInt(alert.employee_id, 10));
        });

        requestAnimationFrame(() => {
            button.classList.add('calendar-employee-alert--visible');
        });

        return button;
    };

    CalendarController.prototype.highlightAlertForEmployee = function highlightAlertForEmployee(employeeId) {
        if (!Number.isFinite(employeeId) || !this.elements.alertsList) {
            return;
        }
        const node = this.elements.alertsList.querySelector(`[data-employee-id="${employeeId}"]`);
        if (!node) {
            return;
        }
        node.classList.add('calendar-alerts-item--pulse');
        if (typeof node.focus === 'function') {
            node.focus({ preventScroll: true });
        }
        if (typeof node.scrollIntoView === 'function') {
            node.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        setTimeout(() => {
            node.classList.remove('calendar-alerts-item--pulse');
        }, 700);
    };

    CalendarController.prototype.focusAlertForEmployee = function focusAlertForEmployee(employeeId) {
        if (!Number.isFinite(employeeId)) {
            return;
        }
        const alert = this.state.alertIndex instanceof Map ? this.state.alertIndex.get(employeeId) : null;
        let targetFilter = this.state.alertFilter || 'all';
        if (alert) {
            const level = typeof alert.risk_level === 'string' ? alert.risk_level.toUpperCase() : '';
            targetFilter = level === 'RED' ? 'critical' : 'warning';
        } else {
            targetFilter = 'all';
        }
        const previousFilter = this.state.alertFilter;
        this.state.alertFilter = targetFilter;
        if (previousFilter !== targetFilter) {
            this.updateAlertFilterUI();
            this.renderAlertsPanel();
        } else {
            this.renderAlertsPanel();
        }
        setTimeout(() => this.highlightAlertForEmployee(employeeId), 120);
    };

    CalendarController.prototype.removeEmployeeAlertIndicator = function removeEmployeeAlertIndicator(employeeId) {
        if (!Number.isFinite(employeeId) || !this.elements.employeeList) {
            return;
        }
        const item = this.elements.employeeList.querySelector(`.calendar-employee-item[data-employee-id="${employeeId}"]`);
        if (!item) {
            return;
        }
        item.classList.remove('calendar-employee-item--alert');
        const badge = item.querySelector('.calendar-employee-alert');
        if (badge) {
            badge.classList.remove('calendar-employee-alert--visible');
            setTimeout(() => {
                if (badge.parentNode) {
                    badge.parentNode.removeChild(badge);
                }
            }, 180);
        }
    };

    CalendarController.prototype.resolveAlert = async function resolveAlert(alertId, employeeId, trigger) {
        if (!Number.isFinite(alertId)) {
            return;
        }
        if (this.state.resolvingAlertId === alertId) {
            return;
        }
        this.state.resolvingAlertId = alertId;
        if (trigger) {
            trigger.disabled = true;
            trigger.setAttribute('aria-busy', 'true');
        }
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: {
                    Accept: 'application/json'
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            this.state.alerts = (this.state.alerts || []).filter((alert) => alert.id !== alertId);
            this.rebuildAlertIndex();
            if (this.dataCache && typeof this.dataCache === 'object') {
                this.dataCache.alerts = Array.isArray(this.state.alerts) ? this.state.alerts.slice() : [];
            }
            if (trigger) {
                trigger.removeAttribute('aria-busy');
                trigger.disabled = false;
            }
            this.renderAlertsPanel();
            if (Number.isFinite(employeeId)) {
                this.removeEmployeeAlertIndicator(employeeId);
            }
            this.showToast('Alert resolved ✅');
        } catch (error) {
            console.error('Failed to resolve alert', error);
            this.showToast('Unable to resolve alert ❌');
            if (trigger) {
                trigger.disabled = false;
                trigger.removeAttribute('aria-busy');
            }
        } finally {
            this.state.resolvingAlertId = null;
        }
    };

    CalendarController.prototype.toggleFormSubmitting = function toggleFormSubmitting(isSubmitting) {
        const submitting = Boolean(isSubmitting);
        this.state.isSubmittingForm = submitting;
        if (this.elements.formSubmit) {
            this.elements.formSubmit.disabled = submitting;
            if (submitting) {
                this.elements.formSubmit.textContent = 'Saving…';
                this.elements.formSubmit.setAttribute('aria-busy', 'true');
            } else {
                this.elements.formSubmit.textContent = this.state.formMode === 'edit' ? 'Save Changes' : 'Save Trip';
                this.elements.formSubmit.removeAttribute('aria-busy');
            }
        }
    };

    CalendarController.prototype.openForm = function openForm(mode, tripId) {
        if (!this.elements.formOverlay || !this.elements.form) {
            return;
        }
        this.hideToast();
        const resolvedMode = mode === 'edit' ? 'edit' : 'create';
        let targetTrip = null;
        if (resolvedMode === 'edit') {
            if (!Number.isFinite(tripId)) {
                console.warn('Edit request ignored: invalid trip id', tripId);
                return;
            }
            targetTrip = this.state.tripIndex.get(tripId);
            if (!targetTrip) {
                console.warn('Edit request ignored: trip not found in state', tripId);
                return;
            }
            this.closeTripDetail({ skipFocus: true });
        }

        let defaultEmployee = this.focusEmployeeId;
        if (!targetTrip && Number.isFinite(this.activeTripId)) {
            const activeTrip = this.state.tripIndex.get(this.activeTripId);
            if (activeTrip) {
                defaultEmployee = activeTrip.employeeId;
            }
        }
        this.state.formMode = resolvedMode;
        this.state.editingTripId = targetTrip ? targetTrip.id : null;
        this.state.isSubmittingForm = false;
        this.elements.form.reset();
        const employeeForForm = targetTrip ? targetTrip.employeeId : defaultEmployee;
        this.populateEmployeeSelect(employeeForForm);

        if (this.elements.formTitle) {
            this.elements.formTitle.textContent = resolvedMode === 'edit' ? 'Edit trip' : 'Add trip';
        }
        if (this.elements.formSubtitle) {
            if (resolvedMode === 'edit' && targetTrip) {
                const employeeName = targetTrip.employeeName || 'trip record';
                this.elements.formSubtitle.textContent = `Updating ${employeeName}`;
            } else {
                this.elements.formSubtitle.textContent = 'Create a new travel record';
            }
        }

        const todayIso = serialiseDate(this.today);
        if (this.elements.formEmployee) {
            this.elements.formEmployee.value = targetTrip ? String(targetTrip.employeeId) : (employeeForForm ? String(employeeForForm) : '');
        }
        if (this.elements.formCountry) {
            this.elements.formCountry.value = targetTrip ? sanitizeText(targetTrip.country || '') : '';
        }
        if (this.elements.formStart) {
            this.elements.formStart.value = targetTrip ? serialiseDate(targetTrip.start) : todayIso;
        }
        if (this.elements.formEnd) {
            this.elements.formEnd.value = targetTrip ? serialiseDate(targetTrip.end) : todayIso;
        }
        if (this.elements.formJobRef) {
            this.elements.formJobRef.value = targetTrip ? sanitizeText(targetTrip.jobRef || '') : '';
        }
        if (this.elements.formPurpose) {
            const detailCopy = targetTrip && (targetTrip.purpose || targetTrip.notes);
            this.elements.formPurpose.value = detailCopy ? sanitizeText(detailCopy) : '';
        }
        if (this.elements.formSubmit) {
            this.elements.formSubmit.disabled = false;
            this.elements.formSubmit.textContent = resolvedMode === 'edit' ? 'Save Changes' : 'Save Trip';
            this.elements.formSubmit.removeAttribute('aria-busy');
        }

        this.clearFormFeedback();
        if (!this.state.employees.length) {
            this.showFormFeedback('Employees are still loading. Complete the remaining details and select an employee once available.', 'info');
        }

        this.elements.formOverlay.hidden = false;
        if (typeof document !== 'undefined' && document.body) {
            document.body.dataset.calendarFormOpen = 'true';
        }
        this.updateBodyScrollLock();
        window.requestAnimationFrame(() => {
            if (this.elements.formEmployee && !this.elements.formEmployee.disabled) {
                this.elements.formEmployee.focus();
            } else if (this.elements.formCountry) {
                this.elements.formCountry.focus();
            }
        });
    };

    CalendarController.prototype.closeForm = function closeForm() {
        if (!this.elements.formOverlay) {
            return;
        }
        if (this.elements.formOverlay.hidden && !this.state.formMode) {
            return;
        }
        this.elements.formOverlay.hidden = true;
        if (this.elements.form) {
            this.elements.form.reset();
        }
        if (typeof document !== 'undefined' && document.body) {
            delete document.body.dataset.calendarFormOpen;
        }
        this.state.formMode = null;
        this.state.editingTripId = null;
        this.state.isSubmittingForm = false;
        this.clearFormFeedback();
        this.updateBodyScrollLock();
    };

    CalendarController.prototype.handleFormSubmit = async function handleFormSubmit(event) {
        event.preventDefault();
        if (!this.state.formMode) {
            return;
        }
        if (!this.elements.form) {
            return;
        }
        if (this.state.isSubmittingForm) {
            return;
        }

        const formData = new FormData(this.elements.form);
        const employeeIdRaw = formData.get('employee_id');
        const country = sanitizeText(formData.get('country'));
        const startDate = sanitizeText(formData.get('start_date'));
        const endDate = sanitizeText(formData.get('end_date'));
        const jobRef = sanitizeText(formData.get('job_ref'));
        const purpose = sanitizeText(formData.get('purpose'));

        const payload = {};
        const errors = [];

        const employeeId = Number.parseInt(employeeIdRaw, 10);
        if (!Number.isFinite(employeeId)) {
            errors.push('Select an employee.');
        } else {
            payload.employee_id = employeeId;
        }

        if (!country) {
            errors.push('Country is required.');
        } else {
            payload.country = country;
        }

        if (!isValidIsoDateString(startDate)) {
            errors.push('Entry date is required.');
        } else {
            payload.start_date = startDate;
        }

        if (!isValidIsoDateString(endDate)) {
            errors.push('Exit date is required.');
        } else {
            payload.end_date = endDate;
        }

        if (!errors.length) {
            const startValue = parseDate(startDate);
            const endValue = parseDate(endDate);
            if (!startValue || !endValue) {
                errors.push('Dates must be valid calendar days.');
            } else if (endValue < startValue) {
                errors.push('Exit date cannot be before entry date.');
            }
        }

        if (jobRef) {
            payload.job_ref = jobRef;
        }
        if (purpose) {
            payload.purpose = purpose;
        }

        if (errors.length) {
            this.showFormFeedback(errors[0]);
            return;
        }

        this.toggleFormSubmitting(true);
        this.clearFormFeedback();

        try {
            let result;
            if (this.state.formMode === 'edit' && Number.isFinite(this.state.editingTripId)) {
                // # Phase 3.9 — prefer unified calendar sync API when present
                const syncApi = typeof window !== 'undefined' ? window.CalendarSync && window.CalendarSync.api : null;
                if (syncApi && typeof syncApi.updateTrip === 'function') {
                    result = await syncApi.updateTrip({ ...payload, trip_id: this.state.editingTripId });
                } else {
                    let response = await fetch('/api/update_trip', {
                        method: 'POST',
                        headers: {
                            Accept: 'application/json',
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ ...payload, trip_id: this.state.editingTripId })
                    });
                    if (!response.ok) {
                        if (response.status === 404) {
                            response = await fetch(`/api/trips/${this.state.editingTripId}`, {
                                method: 'PATCH',
                                headers: {
                                    Accept: 'application/json',
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(payload)
                            });
                        }
                        if (!response.ok) {
                            let message = `Request failed (${response.status})`;
                            try {
                                const errorPayload = await response.json();
                                if (errorPayload && typeof errorPayload.error === 'string') {
                                    message = errorPayload.error;
                                }
                            } catch (readError) {
                                // Ignore JSON parse errors and keep fallback message.
                            }
                            throw new Error(message);
                        }
                    }
                    result = await response.json();
                }
            } else {
                const response = await fetch('/api/trips', {
                    method: 'POST',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                if (!response.ok) {
                    let message = `Request failed (${response.status})`;
                    try {
                        const errorPayload = await response.json();
                        if (errorPayload && typeof errorPayload.error === 'string') {
                            message = errorPayload.error;
                        }
                    } catch (readError) {
                        // Ignore JSON parse errors and keep fallback message.
                    }
                    throw new Error(message);
                }
                result = await response.json();
            }

            const normalised = normaliseTrip(result);
            if (!normalised) {
                throw new Error('Unexpected response payload from server.');
            }

            this.focusEmployeeId = normalised.employeeId;
            this.pendingCenterDate = normalised.start instanceof Date ? normalised.start : parseDate(normalised.start);
            this.pendingFocusTripId = normalised.id;
            const successMessage = this.state.formMode === 'edit' ? 'Trip updated successfully ✅' : 'Trip added successfully ✅';
            this.invalidateForecastForEmployee(normalised.employeeId);

            await this.loadData({
                force: true,
                centerOnToday: false,
                centerOnDate: this.pendingCenterDate instanceof Date ? this.pendingCenterDate : null
            });

            if (Number.isFinite(normalised.employeeId)) {
                this.setForecastEmployee(normalised.employeeId, { force: true, bypassCache: true, reason: 'form-submit' });
            }

            this.closeForm();
            this.showToast(successMessage);
            console.info('[3.9-update-trip] Trip %s saved via form (%s)', normalised.id, this.state.formMode);

            if (this.pendingCenterDate instanceof Date) {
                this.centerOnDate(this.pendingCenterDate);
                this.shouldCenterOnToday = false;
                this.pendingCenterDate = null;
            }
            if (Number.isFinite(this.pendingFocusTripId)) {
                this.openTripDetail(this.pendingFocusTripId);
                this.pendingFocusTripId = null;
            }
        } catch (error) {
            console.error('[3.9-update-trip] Trip save failed', error);
            this.showFormFeedback(error.message || 'Unable to save trip.');
            return;
        } finally {
            this.toggleFormSubmitting(false);
        }
    };

    CalendarController.prototype.calculateRange = function calculateRange() {
        const start = addDays(this.today, -LOOKBACK_DAYS);
        const end = addDays(this.today, this.futureWeeks * 7);
        return { start, end };
    };

    CalendarController.prototype.shiftRange = function shiftRange(step) {
        if (!Number.isFinite(step) || step === 0) {
            return;
        }

        if (this.state && this.state.isRendering) {
            const reschedule = () => this.shiftRange(step);
            if (typeof requestAnimationFrame === 'function') {
                requestAnimationFrame(reschedule);
            } else {
                setTimeout(reschedule, 16);
            }
            return;
        }

        if (!this.range) {
            this.range = this.calculateRange();
        }

        const currentStart = this.range && this.range.start instanceof Date ? this.range.start : parseDate(this.range && this.range.start);
        const currentEnd = this.range && this.range.end instanceof Date ? this.range.end : parseDate(this.range && this.range.end);

        if (!(currentStart instanceof Date) || Number.isNaN(currentStart.getTime()) || !(currentEnd instanceof Date) || Number.isNaN(currentEnd.getTime())) {
            console.warn('Cannot shift calendar range — invalid state detected', this.range);
            return;
        }

        const direction = step > 0 ? 1 : -1;
        const magnitude = Math.max(1, Math.abs(Math.trunc(step)));
        const spanDays = diffInDaysInclusive(currentStart, currentEnd);

        let nextStart = new Date(currentStart.getTime());
        for (let index = 0; index < magnitude; index += 1) {
            nextStart = addMonths(nextStart, direction);
        }

        const nextEnd = addDays(nextStart, spanDays);

        this.range = {
            start: startOfDay(nextStart),
            end: startOfDay(nextEnd)
        };

        this.shouldCenterOnToday = false;
        this.pendingCenterDate = addDays(this.range.start, LOOKBACK_DAYS);

        if (this.elements && this.elements.timelineContainer) {
            this.elements.timelineContainer.scrollLeft = 0;
        }

        this.renderCalendar();
    };

    CalendarController.prototype.resetToToday = function resetToToday() {
        this.range = this.calculateRange();
        this.pendingCenterDate = this.today;
        this.shouldCenterOnToday = true;
        this.renderCalendar();
        this.centerOnDate(this.today);
    };

    CalendarController.prototype.setFutureWeeks = function setFutureWeeks(weeks) {
        const clampedWeeks = Math.min(Math.max(weeks, MIN_FUTURE_WEEKS), MAX_FUTURE_WEEKS);
        if (this.futureWeeks !== clampedWeeks) {
            this.futureWeeks = clampedWeeks;
            this.range = this.calculateRange();
            this.renderCalendar();
        }
    };

    CalendarController.prototype.updateSearchUI = function updateSearchUI() {
        if (!this.elements.searchClear) {
            return;
        }
        const hasTerm = Boolean(this.state.searchTerm && this.state.searchTerm.trim().length > 0);
        this.elements.searchClear.hidden = !hasTerm;
    };

    CalendarController.prototype.applyFilters = function applyFilters() {
        const filtered = filterEmployees(this.state.employees, this.state.searchTerm);
        this.state.filteredEmployees = filtered;
        this.renderRows();
        this.syncTimelineView({ reason: 'filter' });
        this.refreshForecastContext();
    };

    // Fetches trip data with a guard timeout so the UI thread never waits indefinitely.
    CalendarController.prototype.fetchTrips = async function fetchTrips(options = {}) {
        const { force = false } = options;
        if (this.dataCache && !force) {
            return this.dataCache;
        }
        if (typeof fetch !== 'function') {
            throw new Error('Fetch API not available.');
        }

        const controller = typeof AbortController === 'function' ? new AbortController() : null;
        let timeoutId = null;
        const timeoutError = new Error('Calendar request timed out.');
        const timeoutPromise = new Promise((_, reject) => {
            timeoutId = setTimeout(() => {
                if (controller) {
                    controller.abort();
                }
                reject(timeoutError);
            }, FETCH_TIMEOUT_MS);
        });

        try {
            const response = await Promise.race([
                fetch('/api/trips', {
                    headers: { Accept: 'application/json' },
                    signal: controller ? controller.signal : undefined
                }),
                timeoutPromise
            ]);
            if (timeoutId !== null) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            if (!response || typeof response !== 'object' || typeof response.ok !== 'boolean') {
                throw timeoutError;
            }
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const payload = await response.json();
            this.dataCache = payload;
            return payload;
        } catch (error) {
            if (error === timeoutError || (error && error.name === 'AbortError')) {
                throw timeoutError;
            }
            throw error;
        } finally {
            if (timeoutId !== null) {
                clearTimeout(timeoutId);
            }
        }
    };

    CalendarController.prototype.loadData = async function loadData(options = {}) {
        const { force = false, centerOnToday = true, centerOnDate = null } = options;
        debugLog('Loading calendar data...', { force, centerOnToday });
        this.setError(false);
        let payload = null;
        try {
            if (this.dataCache && !force) {
                debugLog('Using cached data');
                payload = this.dataCache;
            } else {
                debugLog('Fetching fresh data...');
                this.setLoading(true);
                payload = await this.fetchTrips({ force });
                debugLog('Data fetched', payload ? Object.keys(payload) : 'null');
            }
            if (!payload || typeof payload !== 'object') {
                throw new Error('Invalid calendar payload.');
            }
            debugLog('Hydrating from payload...');
            this.hydrateFromPayload(payload, { centerOnToday, centerOnDate });
            debugLog('Calendar data loaded successfully');
            return payload;
        } catch (error) {
            console.error('Failed to load calendar data', error);
            this.setError(true);
            throw error;
        } finally {
            this.setLoading(false);
        }
    };

    CalendarController.prototype.hydrateFromPayload = function hydrateFromPayload(payload, options = {}) {
        debugLog('Hydrating payload...', payload);
        const rawTrips = Array.isArray(payload.trips) ? payload.trips : [];
        debugLog('Raw trips count:', rawTrips.length);

        const normalisedTrips = rawTrips
            .map(normaliseTrip)
            .filter(Boolean);

        debugLog('Normalised trips:', normalisedTrips.length);

        const tripGroups = groupTripsByEmployee(normalisedTrips);
        const tripStatus = new Map();
        const tripIndex = new Map();

        for (const trip of normalisedTrips) {
            tripIndex.set(trip.id, trip);
        }

        debugLog('Building trip status index...');
        for (const trips of tripGroups.values()) {
            const statusIndex = buildTripStatusIndex(trips, this.warningThreshold, this.criticalThreshold);
            for (const [tripId, status] of statusIndex.entries()) {
                tripStatus.set(tripId, status);
            }
        }

        let employees = deriveEmployees(payload.employees || [], normalisedTrips);
        debugLog('Derived employees:', employees.length);

        this.state.trips = normalisedTrips;
        this.state.tripGroups = tripGroups;
        this.state.tripStatus = tripStatus;
        this.state.tripIndex = tripIndex;
        this.state.employees = employees;
        this.state.filteredEmployees = employees.slice();
        this.state.alerts = Array.isArray(payload.alerts) ? payload.alerts : [];
        this.rebuildAlertIndex();

        this.activeTripId = null;
        this.updateGlobalEditButtonState();
        if (this.riskCache) {
            this.riskCache.clear();
        }
        if (options.centerOnToday === false) {
            this.shouldCenterOnToday = false;
            if (options.centerOnDate instanceof Date) {
                this.pendingCenterDate = options.centerOnDate;
            }
        } else {
            this.shouldCenterOnToday = true;
        }
        debugLog('About to render calendar...');
        this.renderCalendar();
        this.updateSearchUI();
        this.populateEmployeeSelect();
        this.renderAlertsPanel();
        this.syncTimelineView({ reason: 'hydrate' });
        this.refreshForecastContext({ force: true });
        debugLog('Hydration complete');
    };

    CalendarController.prototype.setLoading = function setLoading(isLoading) {
        if (!this.elements.loading) {
            return;
        }
        this.elements.loading.hidden = !isLoading;
        if (isLoading) {
            this.elements.loading.setAttribute('role', 'status');
            this.elements.loading.setAttribute('aria-live', 'polite');
        } else {
            this.elements.loading.removeAttribute('role');
            this.elements.loading.removeAttribute('aria-live');
        }
    };

    CalendarController.prototype.setError = function setError(hasError) {
        if (!this.elements.error) {
            return;
        }
        this.elements.error.hidden = !hasError;
        if (hasError) {
            this.elements.error.setAttribute('role', 'alert');
        } else {
            this.elements.error.removeAttribute('role');
        }
    };

    CalendarController.prototype.renderCalendar = function renderCalendar() {
        debugLog('renderCalendar() called');
        if (!this.elements.rangeLabel) {
            console.warn('Missing rangeLabel element');
            return;
        }
        debugLog('Setting range label...');
        this.elements.rangeLabel.textContent = formatRangeLabel(this.range);
        debugLog('Calling updateTimelineHeader...');
        this.updateTimelineHeader();
        debugLog('Calling renderRows...');
        try {
            this.renderRows();
            this.syncTimelineView({ reason: 'render' });
            debugLog('renderCalendar() complete');
        } catch (error) {
            console.error('renderRows failed', error);
        }
    };

    CalendarController.prototype.updateTimelineHeader = function updateTimelineHeader() {
        debugLog('Updating timeline header...');
        const days = calculateRangeDays(this.range);
        // Cache the current day breakdown so row rendering can reuse it without recomputing.
        this.rangeDays = days;
        const timelineWidth = (days.length + 1) * DAY_WIDTH;
        this.timelineWidth = timelineWidth;

        if (!this.elements.monthRow || !this.elements.dayRow) {
            console.warn('Timeline header elements missing.');
            return;
        }

        if (this.timelineHeaderFrame) {
            cancelAnimationFrame(this.timelineHeaderFrame);
            this.timelineHeaderFrame = null;
        }

        this.timelineHeaderToken = Symbol('timeline-header-render');
        const renderToken = this.timelineHeaderToken;

        this.elements.monthRow.innerHTML = '';
        this.elements.monthRow.style.width = `${timelineWidth}px`;
        this.elements.dayRow.innerHTML = '';
        this.elements.dayRow.style.width = `${timelineWidth}px`;

        const monthNodes = [];
        const dayNodes = [];
        let monthCursor = null;
        let monthStartIndex = 0;

        const finalize = () => {
            if (this.timelineHeaderToken !== renderToken) {
                return;
            }
            const monthFragment = document.createDocumentFragment();
            for (const node of monthNodes) {
                monthFragment.appendChild(node);
            }
            const dayFragment = document.createDocumentFragment();
            for (const node of dayNodes) {
                dayFragment.appendChild(node);
            }
            this.elements.monthRow.appendChild(monthFragment);
            this.elements.dayRow.appendChild(dayFragment);
            this.timelineHeaderFrame = null;
            debugLog('Timeline header updated');
            this.updateTodayMarker();
        };

        const renderChunk = (startIndex) => {
            if (this.timelineHeaderToken !== renderToken) {
                return;
            }

            const chunkEnd = Math.min(startIndex + HEADER_DAY_CHUNK, days.length);
            debugLog('Rendering timeline chunk', startIndex, '→', chunkEnd, 'of', days.length);
            for (let index = startIndex; index < chunkEnd; index += 1) {
                const day = days[index];

                if (!monthCursor || day.date.getMonth() !== monthCursor.getMonth()) {
                    if (monthCursor) {
                        const monthDays = index - monthStartIndex;
                        const monthCell = document.createElement('div');
                        monthCell.className = 'calendar-month-cell';
                        monthCell.style.width = `${monthDays * DAY_WIDTH}px`;
                        monthCell.textContent = monthCursor.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
                        monthNodes.push(monthCell);
                    }
                    monthCursor = day.date;
                    monthStartIndex = index;
                }

                const dayCell = document.createElement('div');
                dayCell.className = 'calendar-day-cell';
                dayCell.style.width = `${DAY_WIDTH}px`;
                dayCell.textContent = day.day;
                if (day.isWeekend) {
                    dayCell.classList.add('calendar-day-cell--weekend');
                }
                if (day.isMonthStart) {
                    dayCell.classList.add('calendar-day-cell--month-start');
                }
                if (day.isWeekStart) {
                    dayCell.classList.add('calendar-day-cell--week-start');
                }
                dayNodes.push(dayCell);
            }

            if (chunkEnd < days.length) {
                this.timelineHeaderFrame = requestAnimationFrame(() => renderChunk(chunkEnd));
            } else {
                debugLog('Timeline header chunks complete, finalizing.');
                if (monthCursor) {
                    const monthDays = days.length - monthStartIndex;
                    const monthCell = document.createElement('div');
                    monthCell.className = 'calendar-month-cell';
                    monthCell.style.width = `${monthDays * DAY_WIDTH}px`;
                    monthCell.textContent = monthCursor.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
                    monthNodes.push(monthCell);
                }
                finalize();
            }
        };

        renderChunk(0);
    };

    CalendarController.prototype.updateTodayMarker = function updateTodayMarker() {
        const containsToday = isWithinRange(this.today, this.range);
        const offset = containsToday ? (diffInDaysInclusive(this.range.start, this.today) + 0.5) * DAY_WIDTH : null;

        if (this.elements.todayMarkerHeader) {
            this.elements.todayMarkerHeader.style.display = containsToday ? 'block' : 'none';
            if (containsToday && offset !== null) {
                this.elements.todayMarkerHeader.style.transform = `translateX(${offset}px)`;
            }
        }

        if (this.elements.todayMarkerBody) {
            this.elements.todayMarkerBody.style.display = containsToday ? 'block' : 'none';
            if (containsToday && offset !== null) {
                this.elements.todayMarkerBody.style.transform = `translateX(${offset}px)`;
                this.elements.todayMarkerBody.style.height = `${this.elements.grid ? this.elements.grid.scrollHeight : 0}px`;
            }
        }
    };

    // Incremental row rendering with a DOM budget to avoid runaway layouts.
    CalendarController.prototype.renderRows = function renderRows() {
        if (!this.elements.employeeList || !this.elements.grid) {
            console.warn('Missing DOM elements for rendering');
            return;
        }

        if (this.state.isRendering) {
            debugLog('Already rendering, skipping');
            return;
        }
        debugLog('Starting row rendering...', this.state.filteredEmployees.length, 'employees');
        this.state.isRendering = true;

        this.elements.employeeList.innerHTML = '';
        this.elements.grid.innerHTML = '';

        const employees = this.state.filteredEmployees;
        const totalToRender = employees.length;
        if (!employees.length) {
            this.state.isRendering = false;
            this.setEmptyState(true);
            this.updateTodayMarker();
            return;
        }

        let anyTripsVisible = false;
        const width = Math.max(this.timelineWidth, DAY_WIDTH);

        if (this.elements.timelineInner) {
            this.elements.timelineInner.style.width = `${width}px`;
        }
        this.elements.grid.style.width = `${width}px`;

        const renderBudget = { remaining: MAX_DOM_OPERATIONS, exhausted: false };
        const rangeDays = Array.isArray(this.rangeDays) && this.rangeDays.length
            ? this.rangeDays
            : calculateRangeDays(this.range);

        const finalize = (reachedLimit = false) => {
            this.state.isRendering = false;
            if (reachedLimit) {
                this.handleRenderOverflow(anyTripsVisible);
            } else {
                this.setEmptyState(!anyTripsVisible);
            }
            this.updateTodayMarker();
            if (this.pendingCenterDate instanceof Date) {
                this.centerOnDate(this.pendingCenterDate);
                this.pendingCenterDate = null;
                this.shouldCenterOnToday = false;
            } else if (this.shouldCenterOnToday) {
                this.centerOnDate(this.today);
                this.shouldCenterOnToday = false;
            }
            if (this.focusEmployeeId) {
                this.highlightEmployee(this.focusEmployeeId);
            }
            if (Number.isFinite(this.pendingFocusTripId) && this.state.tripIndex.has(this.pendingFocusTripId)) {
                this.openTripDetail(this.pendingFocusTripId);
                this.pendingFocusTripId = null;
            }
        };

        const processBatch = (startIndex) => {
            if (renderBudget.exhausted) {
                finalize(true);
                return;
            }

            const batchEnd = Math.min(startIndex + BATCH_RENDER_SIZE, totalToRender);
            const employeeFragment = document.createDocumentFragment();
            const gridFragment = document.createDocumentFragment();
            let nextIndex = startIndex;

            while (nextIndex < batchEnd && !renderBudget.exhausted) {
                if (renderBudget.remaining <= 0) {
                    renderBudget.exhausted = true;
                    break;
                }

                const employee = employees[nextIndex];
                const rowResult = this.buildRow(employee, width, renderBudget, rangeDays);
                if (rowResult) {
                    debugLog('Rendered employee row', {
                        employee: employee.name,
                        trips: (this.state.tripGroups.get(employee.id) || []).length,
                        visibleTrips: rowResult.hasVisibleTrips,
                        truncated: rowResult.truncated
                    });
                }
                if (!rowResult) {
                    renderBudget.exhausted = true;
                    break;
                }

                if (rowResult.hasVisibleTrips) {
                    anyTripsVisible = true;
                }

                if (!consumeDomBudget(renderBudget, 2)) {
                    renderBudget.exhausted = true;
                    break;
                }
                employeeFragment.appendChild(rowResult.employeeNode);
                gridFragment.appendChild(rowResult.timelineNode);

                if (rowResult.truncated) {
                    renderBudget.exhausted = true;
                }

                nextIndex += 1;
                if (rowResult.truncated) {
                    break;
                }
            }

            if (employeeFragment.childNodes.length) {
                this.elements.employeeList.appendChild(employeeFragment);
            }
            if (gridFragment.childNodes.length) {
                this.elements.grid.appendChild(gridFragment);
            }

            if (renderBudget.exhausted || nextIndex >= totalToRender) {
                finalize(renderBudget.exhausted);
            } else {
                requestAnimationFrame(() => processBatch(nextIndex));
            }
        };

        processBatch(0);
    };

    CalendarController.prototype.syncTimelineView = function syncTimelineView(options = {}) {
        if (typeof globalThis.TimelineView === 'undefined' || typeof globalThis.TimelineView.sync !== 'function') {
            return;
        }
        const dataset = this.buildTimelineDataset();
        globalThis.TimelineView.sync(dataset, options);
    };

    CalendarController.prototype.buildTimelineDataset = function buildTimelineDataset() {
        if (!this.range) {
            return null;
        }
        const rangeDays = Array.isArray(this.rangeDays) && this.rangeDays.length
            ? this.rangeDays
            : calculateRangeDays(this.range);
        const rangeStartDate = this.range.start instanceof Date ? this.range.start : parseDate(this.range.start);
        const rangeEndDate = this.range.end instanceof Date ? this.range.end : parseDate(this.range.end);
        const startIso = rangeStartDate instanceof Date ? serialiseDate(rangeStartDate) : '';
        const endIso = rangeEndDate instanceof Date ? serialiseDate(rangeEndDate) : '';
        const todayIso = this.today instanceof Date ? serialiseDate(this.today) : '';

        const dayDescriptors = rangeDays.map((day) => ({
            iso: serialiseDate(day.date),
            day: day.day,
            isWeekend: day.isWeekend,
            isMonthStart: day.isMonthStart,
            isWeekStart: day.isWeekStart,
            monthLabel: day.date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
        }));

        const employees = Array.isArray(this.state.filteredEmployees) ? this.state.filteredEmployees : [];
        const employeePayload = employees.map((employee) => {
            const trips = this.state.tripGroups.get(employee.id) || [];
            const timelineTrips = [];
            for (const trip of trips) {
                if (trip.end < this.range.start || trip.start > this.range.end) {
                    continue;
                }
                const placement = calculateTripPlacement(this.range, trip);
                if (!placement || !Number.isFinite(placement.durationDays) || placement.durationDays <= 0) {
                    continue;
                }
                const status = this.state.tripStatus.get(trip.id) || { status: 'safe', daysUsed: trip.travelDays };
                const statusKey = typeof status.status === 'string' ? status.status : 'safe';
                const riskSnapshot = this.getRiskSnapshot(employee.id, placement.clampedEnd || trip.end);
                const color = riskSnapshot.color || COLORS[statusKey] || COLORS.safe;
                timelineTrips.push({
                    id: trip.id,
                    employeeId: employee.id,
                    country: trip.country || 'Trip',
                    startIso: serialiseDate(trip.start),
                    endIso: serialiseDate(trip.end),
                    offsetDays: placement.offsetDays,
                    durationDays: placement.durationDays,
                    status: statusKey,
                    statusLabel: normaliseStatusLabel(statusKey),
                    riskLevel: riskSnapshot.level,
                    riskColor: riskSnapshot.color,
                    color,
                    daysUsed: status.daysUsed,
                    tooltip: `${trip.country || 'Trip'} · ${formatDateRangeDisplay(trip.start, trip.end)}`
                });
            }
            const todayRisk = this.getRiskSnapshot(employee.id, this.today);
            const timelineRiskLevel = todayRisk.level === 'caution'
                ? 'warning'
                : todayRisk.level === 'critical'
                    ? 'critical'
                    : 'safe';
            return {
                id: employee.id,
                name: employee.name,
                active: employee.active !== false,
                riskLevel: timelineRiskLevel,
                riskColor: todayRisk.color,
                trips: timelineTrips
            };
        });

        return {
            range: {
                start: startIso,
                end: endIso,
                days: dayDescriptors
            },
            today: todayIso,
            employees: employeePayload,
            dayWidth: DAY_WIDTH
        };
    };

    CalendarController.prototype.getRiskSnapshot = function getRiskSnapshot(employeeId, date) {
        if (!Number.isFinite(employeeId)) {
            return { level: 'unknown', color: RISK_COLORS.safe, daysUsed: 0 };
        }
        const targetDate = date instanceof Date ? date : parseDate(date);
        if (!(targetDate instanceof Date) || Number.isNaN(targetDate.getTime())) {
            return { level: 'unknown', color: RISK_COLORS.safe, daysUsed: 0 };
        }
        if (!this.riskCache) {
            this.riskCache = new Map();
        }
        const iso = serialiseDate(targetDate);
        const cacheKey = `${employeeId}:${iso}`;
        if (this.riskCache.has(cacheKey)) {
            return this.riskCache.get(cacheKey);
        }
        const trips = this.state.tripGroups.get(employeeId) || [];
        const rolling = calculateRollingDaysUsed(trips, targetDate, RISK_THRESHOLDS.limit);
        const { level, color } = resolveRiskLevel(rolling);
        const snapshot = { level, color, daysUsed: rolling };
        this.riskCache.set(cacheKey, snapshot);
        return snapshot;
    };

    CalendarController.prototype.calculateRiskColor = function calculateRiskColor(employeeId, date) {
        const snapshot = this.getRiskSnapshot(employeeId, date);
        return snapshot.color;
    };

    CalendarController.prototype.invalidateRiskCacheForEmployee = function invalidateRiskCacheForEmployee(employeeId) {
        if (!this.riskCache || !Number.isFinite(employeeId)) {
            return;
        }
        const prefix = `${employeeId}:`;
        for (const key of Array.from(this.riskCache.keys())) {
            if (key.startsWith(prefix)) {
                this.riskCache.delete(key);
            }
        }
    };

    // Cache a template of day cells so each row can clone it without rebuilding all nodes.
    CalendarController.prototype.ensureCellTemplate = function ensureCellTemplate(rangeDays) {
        if (!Array.isArray(rangeDays) || !rangeDays.length) {
            this.cellTemplate = null;
            this.cellTemplateKey = '';
            return null;
        }

        const first = serialiseDate(rangeDays[0].date);
        const last = serialiseDate(rangeDays[rangeDays.length - 1].date);
        const key = `${first}:${last}:${rangeDays.length}`;

        if (this.cellTemplate && this.cellTemplateKey === key) {
            return this.cellTemplate;
        }

        const template = document.createElement('template');
        let markup = '';

        for (let index = 0; index < rangeDays.length; index += 1) {
            const day = rangeDays[index];
            const classes = ['calendar-cell'];
            if (day.isWeekend) {
                classes.push('calendar-cell--weekend');
            }
            if (day.isMonthStart) {
                classes.push('calendar-cell--month-start');
            }
            if (day.isWeekStart) {
                classes.push('calendar-cell--week-start');
            }
            markup += `<div class="${classes.join(' ')}" data-calendar-date="${serialiseDate(day.date)}" data-day-index="${index}" role="presentation"></div>`;
        }

        template.innerHTML = markup;
        this.cellTemplate = template;
        this.cellTemplateKey = key;
        return this.cellTemplate;
    };

    CalendarController.prototype.buildRow = function buildRow(employee, width, budget, rangeDays) {
        const employeeItem = document.createElement('div');
        employeeItem.className = 'calendar-employee-item';
        employeeItem.style.height = `${ROW_HEIGHT}px`;
        employeeItem.setAttribute('role', 'option');
        employeeItem.setAttribute('data-employee-id', String(employee.id));

        const profileLink = document.createElement('a');
        profileLink.href = `/employee/${employee.id}`;
        profileLink.textContent = employee.name;
        profileLink.className = 'calendar-employee-link';
        profileLink.title = `Open ${employee.name}'s profile`;
        if (!consumeDomBudget(budget)) {
            return null;
        }
        employeeItem.appendChild(profileLink);

        const alertIndex = this.state.alertIndex instanceof Map ? this.state.alertIndex : null;
        const activeAlert = alertIndex && alertIndex.get(employee.id);
        if (activeAlert) {
            const alertBadge = this.createAlertIcon(activeAlert);
            if (alertBadge) {
                employeeItem.classList.add('calendar-employee-item--alert');
                employeeItem.appendChild(alertBadge);
            }
        }

        if (!employee.active) {
            employeeItem.classList.add('calendar-employee-item--inactive');
        }

        const timelineRow = document.createElement('div');
        timelineRow.className = 'calendar-grid-row';
        timelineRow.style.height = `${ROW_HEIGHT}px`;
        timelineRow.setAttribute('data-employee-id', String(employee.id));

        const background = document.createElement('div');
        background.className = 'calendar-grid-background';
        background.style.width = `${width}px`;
        if (!consumeDomBudget(budget)) {
            return null;
        }
        timelineRow.appendChild(background);

        // Provide explicit day cells so existing automation and keyboard affordances
        // can target consistent slots instead of relying on background gradients.
        const cellLayer = document.createElement('div');
        cellLayer.className = 'calendar-cell-layer';
        cellLayer.style.width = `${width}px`;
        cellLayer.style.height = `${ROW_HEIGHT}px`;
        cellLayer.dataset.employeeId = String(employee.id);
        if (!consumeDomBudget(budget)) {
            return null;
        }
        timelineRow.appendChild(cellLayer);

        const days = Array.isArray(rangeDays) && rangeDays.length ? rangeDays : calculateRangeDays(this.range);
        if (days.length) {
            const template = this.ensureCellTemplate(days);
            if (template) {
                const fragment = template.content.cloneNode(true);
                cellLayer.appendChild(fragment);
                const cells = cellLayer.querySelectorAll('.calendar-cell');
                cells.forEach((cell, index) => {
                    const day = days[index];
                    const risk = this.getRiskSnapshot(employee.id, day.date);
                    cell.dataset.employeeId = String(employee.id);
                    cell.dataset.calendarDate = serialiseDate(day.date);
                    cell.dataset.dayIndex = String(index);
                    cell.dataset.employeeName = employee.name;
                    cell.dataset.riskDaysUsed = String(risk.daysUsed);
                    cell.dataset.riskLevel = risk.level;
                    cell.dataset.riskColor = risk.color;
                    cell.style.setProperty('--calendar-cell-risk', risk.color);
                    const tintAlpha = risk.level === 'critical' ? 0.32 : risk.level === 'caution' ? 0.22 : 0.12;
                    const tint = hexToRgba(risk.color, tintAlpha);
                    cell.style.background = `linear-gradient(180deg, ${tint} 0%, rgba(255, 255, 255, 0) 100%)`;
                    cell.classList.add('calendar-cell--risk');
                    if (!cell.hasAttribute('aria-label')) {
                        cell.setAttribute('aria-label', `Risk usage ${risk.daysUsed} of ${RISK_THRESHOLDS.limit} days`);
                    }
                });
            }
        }

        const tripLayer = document.createElement('div');
        tripLayer.className = 'calendar-trip-layer';
        tripLayer.style.width = `${width}px`;
        tripLayer.style.height = `${ROW_HEIGHT}px`;
        if (!consumeDomBudget(budget)) {
            return null;
        }
        timelineRow.appendChild(tripLayer);
        
        // Register trip layer for drag-and-drop
        if (this.dragManager) {
            this.dragManager.registerRow(tripLayer);
        }

        const trips = this.state.tripGroups.get(employee.id) || [];
        debugLog('Building row for employee', employee.name, 'with', trips.length, 'trips');
        let hasVisibleTrips = false;
        let truncated = false;

        for (const trip of trips) {
            if (trip.end < this.range.start || trip.start > this.range.end) {
                continue;
            }

            const placement = calculateTripPlacement(this.range, trip);
            const positionLeft = placement.offsetDays * DAY_WIDTH;
            const widthPx = Math.max(placement.durationDays * DAY_WIDTH, DAY_WIDTH / 2);

            const tripBlock = document.createElement('div');
            const status = this.state.tripStatus.get(trip.id) || { status: 'safe', daysUsed: trip.travelDays };
            const statusKey = typeof status.status === 'string' ? status.status : 'safe';
            const statusLabel = normaliseStatusLabel(statusKey);
            const riskSnapshot = this.getRiskSnapshot(employee.id, placement.clampedEnd || trip.end);
            const statusColor = riskSnapshot.color || COLORS[statusKey] || COLORS.safe;
            tripBlock.className = `calendar-trip calendar-trip--${statusKey}`;
            tripBlock.classList.add('trip-bar', `trip-bar--${statusKey}`);
            tripBlock.style.left = `${positionLeft}px`;
            tripBlock.style.width = `${widthPx}px`;
            tripBlock.style.top = '8px';
            tripBlock.style.height = `${ROW_HEIGHT - 16}px`;
            const tripTintAlpha = riskSnapshot.level === 'critical' ? 0.42 : riskSnapshot.level === 'caution' ? 0.34 : 0.26;
            const tripTint = hexToRgba(statusColor, tripTintAlpha);
            tripBlock.style.background = `linear-gradient(135deg, ${tripTint} 0%, ${statusColor} 100%)`;
            tripBlock.textContent = '';
            this.decorateTripNode(tripBlock, trip);

            tripBlock.setAttribute('data-trip-id', String(trip.id));
            tripBlock.setAttribute('data-employee', employee.name);
            tripBlock.setAttribute('data-employee-id', String(employee.id));
            tripBlock.setAttribute('data-country', trip.country || 'Unknown');
            tripBlock.setAttribute('data-start', serialiseDate(trip.start));
            tripBlock.setAttribute('data-end', serialiseDate(trip.end));
            tripBlock.setAttribute('data-job-ref', trip.jobRef || '');
            tripBlock.setAttribute('data-days-used', Number.isFinite(status.daysUsed) ? String(status.daysUsed) : '');
            tripBlock.setAttribute('data-risk-days-used', String(riskSnapshot.daysUsed));
            tripBlock.setAttribute('data-risk-level', riskSnapshot.level);
            tripBlock.setAttribute('data-compliance', statusKey);
            tripBlock.setAttribute('data-status-label', statusLabel);
            let projectedRemaining = '';
            if (Number.isFinite(status.daysUsed)) {
                projectedRemaining = RISK_THRESHOLDS.limit - status.daysUsed;
            } else if (Number.isFinite(riskSnapshot.daysUsed)) {
                projectedRemaining = RISK_THRESHOLDS.limit - riskSnapshot.daysUsed;
            }
            if (projectedRemaining !== '') {
                tripBlock.setAttribute('data-days-remaining', String(projectedRemaining));
                if (trip.start > this.today) {
                    tripBlock.setAttribute('data-forecast-remaining', String(projectedRemaining));
                } else {
                    tripBlock.removeAttribute('data-forecast-remaining');
                }
            } else {
                tripBlock.removeAttribute('data-days-remaining');
                tripBlock.removeAttribute('data-forecast-remaining');
            }
            tripBlock.setAttribute('tabindex', '0');
            tripBlock.setAttribute('role', 'button');
            tripBlock.style.setProperty('--calendar-trip-color', statusColor);

            const ariaParts = [
                trip.country ? `${trip.country} trip` : 'Trip',
                `for ${employee.name}`,
                formatDateRangeDisplay(trip.start, trip.end),
                statusLabel,
                `Usage ${riskSnapshot.daysUsed} of ${RISK_THRESHOLDS.limit} days`
            ].filter(Boolean);
            tripBlock.setAttribute('aria-label', ariaParts.join('. '));

            if (trip.start < this.range.start) {
                tripBlock.classList.add('calendar-trip--overflow-start', 'trip-bar--overflow-start');
            }
            if (trip.end > this.range.end) {
                tripBlock.classList.add('calendar-trip--overflow-end', 'trip-bar--overflow-end');
            }
            if (trip.ghosted) {
                tripBlock.classList.add('calendar-trip--ghosted', 'trip-bar--ghosted');
            }

            if (!consumeDomBudget(budget)) {
                truncated = true;
                break;
            }
            tripLayer.appendChild(tripBlock);
            this.prepareTripForDrag(tripBlock, trip);
            hasVisibleTrips = true;
        }

        return {
            employeeNode: employeeItem,
            timelineNode: timelineRow,
            hasVisibleTrips,
            truncated
        };
    };

    // Stubs drag handles for future drag-and-drop capability (Phase 3.6.1) — Author: GPT-5 Codex
    CalendarController.prototype.prepareTripForDrag = function prepareTripForDrag(node, trip) {
        if (!node || !trip) {
            return;
        }

        const locked = node.dataset.dragDisabled === 'true'
            || node.dataset.locked === 'true'
            || Boolean(trip.locked);

        node.dataset.tripId = trip.id ? String(trip.id) : '';
        node.dataset.dragInteraction = locked ? 'disabled' : 'ready';

        if (locked || !this.dragManager) {
            node.setAttribute('draggable', 'false');
            node.setAttribute('aria-grabbed', 'false');
            return;
        }

        this.dragManager.registerTrip(node, {
            id: trip.id,
            employeeId: trip.employeeId,
            start: trip.start,
            end: trip.end,
            durationDays: trip.durationDays,
            locked: false
        });
    };

    CalendarController.prototype.decorateTripNode = function decorateTripNode(node, trip) {
        if (!node) {
            return;
        }
        const ensureHandle = (modifier) => {
            let handle = node.querySelector(`.calendar-trip-handle--${modifier}`);
            if (!handle) {
                handle = document.createElement('span');
                handle.className = `calendar-trip-handle calendar-trip-handle--${modifier}`;
                handle.dataset.resize = modifier === 'end' ? 'end' : 'start';
                handle.setAttribute('aria-hidden', 'true');
                handle.setAttribute('draggable', 'false');
                node.appendChild(handle);
            }
            return handle;
        };
        let label = node.querySelector('.calendar-trip-label');
        if (!label) {
            node.textContent = '';
            label = document.createElement('span');
            label.className = 'calendar-trip-label';
            node.appendChild(label);
        }
        if (trip) {
            label.textContent = trip.country || 'Trip';
        }
        ensureHandle('start');
        ensureHandle('end');
    };

    CalendarController.prototype.handleTripDrop = async function handleTripDrop(details) {
        this.closeContextMenu();
        if (!details || !Number.isFinite(details.tripId)) {
            if (details && typeof details.revert === 'function') {
                details.revert();
            }
            return;
        }

        const {
            tripId,
            employeeId,
            element,
            nextStart,
            nextEnd,
            nextIndex,
            nextLeft,
            revert
        } = details;

        const trip = this.state.tripIndex.get(tripId);
        if (!trip) {
            if (typeof revert === 'function') {
                revert();
            }
            return;
        }

        if (!(nextStart instanceof Date) || Number.isNaN(nextStart.getTime()) || !(nextEnd instanceof Date) || Number.isNaN(nextEnd.getTime())) {
            if (typeof revert === 'function') {
                revert();
            }
            return;
        }

        const rangeStart = this.range && this.range.start instanceof Date ? startOfDay(this.range.start) : null;
        const rangeEnd = this.range && this.range.end instanceof Date ? startOfDay(this.range.end) : null;
        if (rangeStart && nextStart < rangeStart) {
            if (typeof revert === 'function') {
                revert();
            }
            this.showToast('Trips cannot start before the visible range ❌');
            return;
        }
        if (rangeEnd && nextEnd > rangeEnd) {
            if (typeof revert === 'function') {
                revert();
            }
            this.showToast('Trips cannot extend beyond the visible range ❌');
            return;
        }

        const unchanged = trip.start.getTime() === nextStart.getTime() && trip.end.getTime() === nextEnd.getTime();
        const targetElement = element || this.elements.grid.querySelector(`.calendar-trip[data-trip-id="${tripId}"]`);

        if (unchanged) {
            if (targetElement && Number.isFinite(details.originalLeft)) {
                targetElement.style.left = `${details.originalLeft}px`;
            }
            return;
        }

        if (targetElement) {
            targetElement.classList.add('calendar-trip--updating');
            const previewLeft = Number.isFinite(nextLeft)
                ? Math.max(0, nextLeft)
                : Number.isFinite(nextIndex)
                    ? Math.max(0, nextIndex * DAY_WIDTH)
                    : null;
            if (previewLeft !== null) {
                targetElement.style.left = `${previewLeft}px`;
            }
        }

        try {
            const updatedTrip = await this.updateTripDates(tripId, nextStart, nextEnd);
            this.integrateTripUpdate(updatedTrip);
            const statusIndex = this.recalculateEmployeeStatuses(updatedTrip.employeeId);
            this.applyStatusUpdatesToEmployee(updatedTrip.employeeId, statusIndex);

            if (this.isDetailOpen && this.activeTripId === updatedTrip.id) {
                this.openTripDetail(updatedTrip.id);
            }

            this.showToast('Trip updated successfully ✅');
        } catch (error) {
            console.error('[3.9-update-trip] Drag-and-drop update failed', error);
            if (typeof revert === 'function') {
                revert();
            }
            if (targetElement) {
                targetElement.classList.remove('calendar-trip--updating');
            }
            this.showToast('Unable to update trip. Changes reverted ❌');
            return;
        }

        if (targetElement) {
            targetElement.classList.remove('calendar-trip--updating');
            targetElement.setAttribute('aria-grabbed', 'false');
        }
    };

    CalendarController.prototype.updateTripDates = async function updateTripDates(tripId, startDate, endDate) {
        if (!Number.isFinite(tripId)) {
            throw new Error('Invalid trip identifier.');
        }

        if (!(startDate instanceof Date) || Number.isNaN(startDate.getTime()) || !(endDate instanceof Date) || Number.isNaN(endDate.getTime())) {
            throw new Error('Drag update failed: invalid dates.');
        }

        if (endDate < startDate) {
            throw new Error('Drag update failed: end date cannot be before start date.');
        }

        if (typeof fetch !== 'function') {
            throw new Error('Fetch API is unavailable in this environment.');
        }

        const payload = {
            trip_id: tripId,
            start_date: serialiseDate(startDate),
            end_date: serialiseDate(endDate)
        };

        const syncApi = typeof window !== 'undefined' ? window.CalendarSync && window.CalendarSync.api : null;
        let result;
        if (syncApi && typeof syncApi.updateTrip === 'function') {
            result = await syncApi.updateTrip({ ...payload });
        } else {
            let response;
            try {
                response = await fetch('/api/update_trip', {
                    method: 'POST',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
            } catch (networkError) {
                throw networkError;
            }
            if (!response.ok) {
                if (response.status === 404) {
                    response = await fetch('/api/update_trip_dates', {
                        method: 'POST',
                        headers: {
                            Accept: 'application/json',
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });
                }
                if (!response.ok) {
                    let message = `Trip update failed (${response.status})`;
                    try {
                        const errorPayload = await response.json();
                        if (errorPayload && typeof errorPayload.error === 'string') {
                            message = errorPayload.error;
                        }
                    } catch (parseError) {
                        // Ignore JSON parse errors and retain fallback message.
                    }
                    throw new Error(message);
                }
            }
            result = await response.json();
        }
        const normalised = normaliseTrip(result);
        if (!normalised) {
            throw new Error('Unexpected payload received from server.');
        }
        console.info('[3.9-update-trip] Trip %s rescheduled to %s → %s', tripId, payload.start_date, payload.end_date);

        return normalised;
    };

    CalendarController.prototype.handleDragPreview = function handleDragPreview(details) {
        if (!details || !details.element) {
            return;
        }
        const element = details.element;
        const nextStart = details.nextStart instanceof Date ? details.nextStart : null;
        const nextEnd = details.nextEnd instanceof Date ? details.nextEnd : nextStart;
        if (!nextStart || !nextEnd) {
            return;
        }
        this.closeContextMenu();
        if (!element.dataset.dragOriginalStart) {
            element.dataset.dragOriginalStart = element.getAttribute('data-start') || '';
        }
        if (!element.dataset.dragOriginalEnd) {
            element.dataset.dragOriginalEnd = element.getAttribute('data-end') || '';
        }
        if (!element.dataset.dragOriginalAria) {
            element.dataset.dragOriginalAria = element.getAttribute('aria-label') || '';
        }
        const startIso = serialiseDate(nextStart);
        const endIso = serialiseDate(nextEnd);
        const previewLabel = formatDateRangeDisplay(nextStart, nextEnd);
        element.dataset.previewStart = startIso;
        element.dataset.previewEnd = endIso;
        element.dataset.previewLabel = previewLabel;
        element.setAttribute('data-preview-label', previewLabel);
        element.setAttribute('data-start', startIso);
        element.setAttribute('data-end', endIso);
        const statusLabel = element.getAttribute('data-status-label') || '';
        const employee = element.getAttribute('data-employee') || 'Unknown employee';
        const country = element.getAttribute('data-country') || 'Trip';
        const ariaLabelParts = [
            country ? `${country} trip` : 'Trip',
            `for ${employee}`,
            previewLabel,
            statusLabel
        ].filter(Boolean);
        element.setAttribute('aria-label', ariaLabelParts.join('. '));
    };

    CalendarController.prototype.handleDragPreviewEnd = function handleDragPreviewEnd(details) {
        if (!details || !details.element) {
            return;
        }
        const element = details.element;
        const originalStart = element.dataset.dragOriginalStart || (details.originalStart instanceof Date ? serialiseDate(details.originalStart) : null);
        const originalEnd = element.dataset.dragOriginalEnd || (details.originalEnd instanceof Date ? serialiseDate(details.originalEnd) : null);
        const originalAria = element.dataset.dragOriginalAria || null;

        if (originalStart !== null) {
            element.setAttribute('data-start', originalStart);
        } else {
            element.removeAttribute('data-start');
        }
        if (originalEnd !== null) {
            element.setAttribute('data-end', originalEnd);
        } else {
            element.removeAttribute('data-end');
        }
        if (originalAria !== null) {
            element.setAttribute('aria-label', originalAria);
        }

        delete element.dataset.previewStart;
        delete element.dataset.previewEnd;
        delete element.dataset.previewLabel;
        delete element.dataset.dragOriginalStart;
        delete element.dataset.dragOriginalEnd;
        delete element.dataset.dragOriginalAria;
        element.removeAttribute('data-preview-label');
    };

    CalendarController.prototype.integrateTripUpdate = function integrateTripUpdate(updatedTrip) {
        if (!updatedTrip) {
            return;
        }

        this.invalidateRiskCacheForEmployee(updatedTrip.employeeId);

        this.state.tripIndex.set(updatedTrip.id, updatedTrip);

        const group = this.state.tripGroups.get(updatedTrip.employeeId) || [];
        const existingIndex = group.findIndex((item) => item.id === updatedTrip.id);
        if (existingIndex === -1) {
            group.push(updatedTrip);
        } else {
            group.splice(existingIndex, 1, updatedTrip);
        }
        group.sort((a, b) => a.start - b.start || a.end - b.end || a.id - b.id);
        this.state.tripGroups.set(updatedTrip.employeeId, group);

        const globalIndex = this.state.trips.findIndex((item) => item.id === updatedTrip.id);
        if (globalIndex === -1) {
            this.state.trips.push(updatedTrip);
        } else {
            this.state.trips.splice(globalIndex, 1, updatedTrip);
        }
        this.state.trips.sort((a, b) => a.start - b.start || a.end - b.end || a.id - b.id);

        if (this.dataCache && Array.isArray(this.dataCache.trips)) {
            const cacheIndex = this.dataCache.trips.findIndex((item) => item.id === updatedTrip.id);
            if (cacheIndex !== -1) {
                this.dataCache.trips.splice(cacheIndex, 1, updatedTrip.raw || {
                    ...this.dataCache.trips[cacheIndex],
                    start_date: serialiseDate(updatedTrip.start),
                    end_date: serialiseDate(updatedTrip.end),
                    entry_date: serialiseDate(updatedTrip.start),
                    exit_date: serialiseDate(updatedTrip.end),
                    travel_days: updatedTrip.durationDays
                });
            }
        }
    };

    CalendarController.prototype.recalculateEmployeeStatuses = function recalculateEmployeeStatuses(employeeId) {
        const trips = this.state.tripGroups.get(employeeId);
        if (!trips || !trips.length) {
            return new Map();
        }

        const statusIndex = buildTripStatusIndex(trips, this.warningThreshold, this.criticalThreshold);
        for (const [tripId, status] of statusIndex.entries()) {
            this.state.tripStatus.set(tripId, status);
        }
        return statusIndex;
    };

    CalendarController.prototype.applyStatusUpdatesToEmployee = function applyStatusUpdatesToEmployee(employeeId, statusIndex) {
        if (!statusIndex || !(statusIndex instanceof Map)) {
            return;
        }

        this.invalidateRiskCacheForEmployee(employeeId);

        for (const [tripId, status] of statusIndex.entries()) {
            const trip = this.state.tripIndex.get(tripId);
            if (!trip) {
                continue;
            }
            const node = this.elements.grid.querySelector(`.calendar-trip[data-trip-id="${tripId}"]`);
            if (node) {
                this.updateTripElementAppearance(node, trip, status);
            }
        }
    };

    CalendarController.prototype.updateTripElementAppearance = function updateTripElementAppearance(node, trip, status) {
        if (!node || !trip) {
            return;
        }

        const placement = calculateTripPlacement(this.range, trip);
        const statusKey = status && typeof status.status === 'string' ? status.status : 'safe';
        const statusLabel = normaliseStatusLabel(statusKey);
        const riskSnapshot = this.getRiskSnapshot(trip.employeeId, placement.clampedEnd || trip.end);
        const statusColor = riskSnapshot.color || COLORS[statusKey] || COLORS.safe;

        node.style.left = `${placement.offsetDays * DAY_WIDTH}px`;
        node.style.width = `${Math.max(placement.durationDays * DAY_WIDTH, DAY_WIDTH / 2)}px`;
        const tripTintAlpha = riskSnapshot.level === 'critical' ? 0.42 : riskSnapshot.level === 'caution' ? 0.34 : 0.26;
        const tripTint = hexToRgba(statusColor, tripTintAlpha);
        node.style.background = `linear-gradient(135deg, ${tripTint} 0%, ${statusColor} 100%)`;

        node.classList.remove('calendar-trip--safe', 'calendar-trip--warning', 'calendar-trip--critical');
        node.classList.remove('trip-bar--safe', 'trip-bar--warning', 'trip-bar--critical');
        node.classList.add(`calendar-trip--${statusKey}`);
        node.classList.add(`trip-bar--${statusKey}`);

        node.dataset.start = serialiseDate(trip.start);
        node.dataset.end = serialiseDate(trip.end);
        node.dataset.daysUsed = status && Number.isFinite(status.daysUsed) ? String(status.daysUsed) : '';
        node.dataset.compliance = statusKey;
        node.dataset.statusLabel = statusLabel;
        node.dataset.employee = trip.employeeName || node.dataset.employee || '';
        node.dataset.country = trip.country || node.dataset.country || '';
        node.dataset.jobRef = trip.jobRef || '';
        node.dataset.employeeId = Number.isFinite(trip.employeeId) ? String(trip.employeeId) : node.dataset.employeeId || '';
        node.dataset.riskDaysUsed = String(riskSnapshot.daysUsed);
        node.dataset.riskLevel = riskSnapshot.level;
        node.dataset.riskColor = statusColor;
        node.style.setProperty('--calendar-trip-color', statusColor);
        this.decorateTripNode(node, trip);

        node.classList.remove('calendar-trip--overflow-start', 'trip-bar--overflow-start');
        node.classList.remove('calendar-trip--overflow-end', 'trip-bar--overflow-end');
        if (trip.start < this.range.start) {
            node.classList.add('calendar-trip--overflow-start', 'trip-bar--overflow-start');
        }
        if (trip.end > this.range.end) {
            node.classList.add('calendar-trip--overflow-end', 'trip-bar--overflow-end');
        }

        if (trip.ghosted) {
            node.classList.add('calendar-trip--ghosted', 'trip-bar--ghosted');
        } else {
            node.classList.remove('calendar-trip--ghosted', 'trip-bar--ghosted');
        }

        const ariaParts = [
            trip.country ? `${trip.country} trip` : 'Trip',
            trip.employeeName ? `for ${trip.employeeName}` : null,
            formatDateRangeDisplay(trip.start, trip.end),
            statusLabel,
            `Usage ${riskSnapshot.daysUsed} of ${RISK_THRESHOLDS.limit} days`
        ].filter(Boolean);
        node.setAttribute('aria-label', ariaParts.join('. '));
        node.setAttribute('aria-grabbed', 'false');

        this.prepareTripForDrag(node, trip);
    };

    CalendarController.prototype.handleRenderOverflow = function handleRenderOverflow(hasVisibleTrips) {
        this.setEmptyState(true, {
            message: 'Too many trips to render at once. Refine filters or adjust the date range.'
        });
        if (!hasVisibleTrips) {
            this.elements.employeeList.innerHTML = '';
            this.elements.grid.innerHTML = '';
        }
    };

    CalendarController.prototype.setEmptyState = function setEmptyState(isEmpty, options = {}) {
        if (!this.elements.empty) {
            return;
        }
        if (this.emptyStateMessageNode) {
            if (isEmpty) {
                const messageText = options.message || this.emptyStateDefaultMessage;
                this.emptyStateMessageNode.textContent = messageText;
            } else {
                this.emptyStateMessageNode.textContent = this.emptyStateDefaultMessage;
            }
        }
        this.elements.empty.hidden = !isEmpty;
        if (isEmpty) {
            this.elements.empty.setAttribute('role', 'status');
            this.elements.empty.setAttribute('aria-live', 'polite');
        } else {
            this.elements.empty.removeAttribute('role');
            this.elements.empty.removeAttribute('aria-live');
        }
    };

    CalendarController.prototype.centerOnDate = function centerOnDate(date) {
        if (!this.elements.timelineContainer) {
            return;
        }
        if (!isWithinRange(date, this.range)) {
            return;
        }
        const offset = diffInDaysInclusive(this.range.start, date) * DAY_WIDTH;
        const targetScroll = Math.max(0, offset - (this.elements.timelineContainer.clientWidth / 2));
        this.elements.timelineContainer.scrollTo({ left: targetScroll, behavior: 'smooth' });
    };

    CalendarController.prototype.highlightEmployee = function highlightEmployee(employeeId) {
        const row = this.elements.grid.querySelector(`.calendar-grid-row[data-employee-id="${employeeId}"]`);
        const employeeItem = this.elements.employeeList.querySelector(`.calendar-employee-item[data-employee-id="${employeeId}"]`);
        if (!row || !employeeItem) {
            return;
        }
        row.classList.add('calendar-grid-row--focus');
        employeeItem.classList.add('calendar-employee-item--focus');
        row.scrollIntoView({ block: 'center', behavior: 'smooth' });
        this.focusEmployeeId = null;
    };

    CalendarController.prototype.init = function init() {
        debugLog('Calendar initializing...');
        this.setupEventListeners();
        this.populateFutureWeeksSelect();
        this.updateViewToggleUI();
        if (this.elements.forecastPanel) {
            this.renderForecastLoading('Loading forecast…');
        }
        this.loadData().catch((error) => {
            console.error('Initial calendar load failed', error);
        });
    };

    CalendarController.prototype.setupEventListeners = function setupEventListeners() {
        // Future weeks selector
        if (this.elements.futureWeeksSelect) {
            this.elements.futureWeeksSelect.addEventListener('change', (e) => {
                const weeks = parseInt(e.target.value, 10);
                if (!isNaN(weeks)) {
                    this.setFutureWeeks(weeks);
                }
            });
        }
    };

    CalendarController.prototype.populateFutureWeeksSelect = function populateFutureWeeksSelect() {
        if (!this.elements.futureWeeksSelect) {
            return;
        }
        
        this.elements.futureWeeksSelect.innerHTML = '';
        for (let weeks = MIN_FUTURE_WEEKS; weeks <= MAX_FUTURE_WEEKS; weeks++) {
            const option = document.createElement('option');
            option.value = weeks;
            option.textContent = `${weeks} weeks`;
            if (weeks === this.futureWeeks) {
                option.selected = true;
            }
            this.elements.futureWeeksSelect.appendChild(option);
        }
    };

    const CalendarApp = {
        init(root) {
            if (!root) {
                return null;
            }
            const controller = new CalendarController(root);
            controller.init();
            return controller;
        }
    };

    const CalendarUtils = {
        parseDate,
        addDays,
        addMonths,
        startOfMonth,
        endOfMonth,
        diffInDaysInclusive,
        calculateRangeDays,
        buildTripStatusIndex,
        normaliseTrip,
        calculateTripPlacement,
        formatRangeLabel,
        formatDateRangeDisplay,
        formatDateTimeDisplay,
        formatDuration,
        normaliseStatusLabel,
        DEFAULT_WARNING_THRESHOLD,
        CRITICAL_THRESHOLD,
        LOOKBACK_DAYS,
        DEFAULT_FUTURE_WEEKS,
        MIN_FUTURE_WEEKS,
        MAX_FUTURE_WEEKS
    };

    function initCalendar() {
        if (typeof document === 'undefined') {
            return;
        }
        const calendarRoot = document.getElementById('calendar');
        if (calendarRoot) {
            CalendarApp.init(calendarRoot);
        }
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { CalendarApp, CalendarUtils };
    } else {
        global.CalendarApp = CalendarApp;
        global.CalendarUtils = CalendarUtils;
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initCalendar);
        } else {
            initCalendar();
        }
    }
})(typeof window !== 'undefined' ? window : globalThis);
    CalendarController.prototype.handleTripPointerDown = function handleTripPointerDown(event) {
        const handle = event.target.closest('.calendar-trip-handle');
        if (!handle || (typeof event.button === 'number' && event.button !== 0)) {
            return;
        }
        const tripNode = handle.closest('.calendar-trip');
        if (!tripNode) {
            return;
        }
        const tripId = Number.parseInt(tripNode.dataset.tripId || '', 10);
        if (!Number.isFinite(tripId)) {
            return;
        }
        const trip = this.state.tripIndex.get(tripId);
        if (!trip) {
            return;
        }
        if (tripNode.dataset.dragInteraction === 'disabled' || trip.locked) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        const edge = handle.dataset.resize === 'end' ? 'end' : 'start';
        this.beginTripResize({
            trip,
            edge,
            element: tripNode,
            pointerId: event.pointerId,
            clientX: event.clientX,
            captureTarget: handle
        });
    };

    CalendarController.prototype.beginTripResize = function beginTripResize(options = {}) {
        if (!options.trip || !options.element) {
            return;
        }
        this.teardownResizeListeners();
        const rangeStart = this.range && this.range.start instanceof Date ? startOfDay(this.range.start) : null;
        const rangeEnd = this.range && this.range.end instanceof Date ? startOfDay(this.range.end) : null;
        const baseStart = startOfDay(options.trip.start);
        const baseEnd = startOfDay(options.trip.end || options.trip.start);
        const computedStyle = typeof window !== 'undefined' ? window.getComputedStyle(options.element) : null;
        const originalLeft = Number.parseFloat(options.element.style.left || (computedStyle && computedStyle.left) || '0') || 0;
        const computedWidth = Number.parseFloat(options.element.style.width || (computedStyle && computedStyle.width) || '0');
        const originalWidth = Number.isFinite(computedWidth) && computedWidth > 0
            ? computedWidth
            : Math.max((diffInDaysInclusive(baseStart, baseEnd) + 1) * DAY_WIDTH, DAY_WIDTH);
        this.resizeSession = {
            tripId: options.trip.id,
            employeeId: options.trip.employeeId,
            edge: options.edge === 'end' ? 'end' : 'start',
            pointerId: options.pointerId,
            startClientX: options.clientX,
            baseStart,
            baseEnd,
            rangeStart,
            rangeEnd,
            originalLeft,
            originalWidth,
            element: options.element,
            previewStart: null,
            previewEnd: null,
            captureTarget: options.captureTarget || null,
            lastDelta: null
        };
        if (typeof window !== 'undefined') {
            window.addEventListener('pointermove', this.handleTripResizeMove, { passive: false });
            window.addEventListener('pointerup', this.handleTripResizeEnd, { passive: false });
            window.addEventListener('pointercancel', this.handleTripResizeEnd, { passive: false });
        }
        if (this.resizeSession.captureTarget && typeof this.resizeSession.captureTarget.setPointerCapture === 'function') {
            try {
                this.resizeSession.captureTarget.setPointerCapture(this.resizeSession.pointerId);
            } catch {
                // ignore
            }
        }
        options.element.classList.add('calendar-trip--resizing');
    };

    CalendarController.prototype.calculateResizeTarget = function calculateResizeTarget(session, deltaDays) {
        if (!session) {
            return null;
        }
        if (session.edge === 'start') {
            let proposedStart = addDays(session.baseStart, deltaDays);
            if (!proposedStart) {
                return null;
            }
            if (session.rangeStart && proposedStart < session.rangeStart) {
                proposedStart = session.rangeStart;
            }
            if (proposedStart > session.baseEnd) {
                proposedStart = session.baseEnd;
            }
            return { start: proposedStart, end: session.baseEnd };
        }
        let proposedEnd = addDays(session.baseEnd, deltaDays);
        if (!proposedEnd) {
            return null;
        }
        if (session.rangeEnd && proposedEnd > session.rangeEnd) {
            proposedEnd = session.rangeEnd;
        }
        if (proposedEnd < session.baseStart) {
            proposedEnd = session.baseStart;
        }
        return { start: session.baseStart, end: proposedEnd };
    };

    CalendarController.prototype.applyResizePreview = function applyResizePreview(session) {
        if (!session || !session.element) {
            return;
        }
        const targetStart = session.previewStart || session.baseStart;
        const targetEnd = session.previewEnd || session.baseEnd;
        const durationDays = Math.max(1, diffInDaysInclusive(targetStart, targetEnd) + 1);
        const widthPx = durationDays * DAY_WIDTH;
        session.element.style.width = `${widthPx}px`;
        if (session.edge === 'start') {
            const offsetDays = diffInDaysInclusive(session.baseStart, targetStart);
            const nextLeft = session.originalLeft + (offsetDays * DAY_WIDTH);
            session.element.style.left = `${Math.max(0, nextLeft)}px`;
        } else {
            session.element.style.left = `${Math.max(0, session.originalLeft)}px`;
        }
        session.element.classList.add('calendar-trip--resizing');
    };

    CalendarController.prototype.handleTripResizeMove = function handleTripResizeMove(event) {
        const session = this.resizeSession;
        if (!session || event.pointerId !== session.pointerId) {
            return;
        }
        event.preventDefault();
        const deltaPx = event.clientX - session.startClientX;
        const deltaDays = Math.round(deltaPx / DAY_WIDTH);
        if (deltaDays === session.lastDelta) {
            return;
        }
        const nextDates = this.calculateResizeTarget(session, deltaDays);
        if (!nextDates) {
            return;
        }
        session.lastDelta = deltaDays;
        session.previewStart = nextDates.start;
        session.previewEnd = nextDates.end;
        this.applyResizePreview(session);
    };

    CalendarController.prototype.handleTripResizeEnd = function handleTripResizeEnd(event) {
        const session = this.resizeSession;
        if (!session) {
            return;
        }
        if (event.type !== 'pointercancel' && event.pointerId !== session.pointerId) {
            return;
        }
        event.preventDefault();
        this.teardownResizeListeners();
        if (session.captureTarget && typeof session.captureTarget.releasePointerCapture === 'function') {
            try {
                session.captureTarget.releasePointerCapture(session.pointerId);
            } catch {
                // ignore
            }
        }
        const nextStart = session.previewStart || session.baseStart;
        const nextEnd = session.previewEnd || session.baseEnd;
        session.element.classList.remove('calendar-trip--resizing');
        if (nextStart.getTime() === session.baseStart.getTime() && nextEnd.getTime() === session.baseEnd.getTime()) {
            this.resetResizePreview(session);
            this.resizeSession = null;
            return;
        }
        this.commitTripResize(session, nextStart, nextEnd);
    };

    CalendarController.prototype.resetResizePreview = function resetResizePreview(session) {
        if (!session || !session.element) {
            return;
        }
        session.element.style.left = `${Math.max(0, session.originalLeft)}px`;
        session.element.style.width = `${session.originalWidth}px`;
    };

    CalendarController.prototype.teardownResizeListeners = function teardownResizeListeners() {
        if (typeof window === 'undefined') {
            return;
        }
        window.removeEventListener('pointermove', this.handleTripResizeMove);
        window.removeEventListener('pointerup', this.handleTripResizeEnd);
        window.removeEventListener('pointercancel', this.handleTripResizeEnd);
    };

    CalendarController.prototype.commitTripResize = async function commitTripResize(session, nextStart, nextEnd) {
        const element = session.element;
        if (element) {
            element.classList.add('calendar-trip--updating');
        }
        try {
            const updatedTrip = await this.updateTripDates(session.tripId, nextStart, nextEnd);
            this.integrateTripUpdate(updatedTrip);
            const statusIndex = this.recalculateEmployeeStatuses(updatedTrip.employeeId);
            this.applyStatusUpdatesToEmployee(updatedTrip.employeeId, statusIndex);
            if (this.isDetailOpen && this.activeTripId === updatedTrip.id) {
                this.openTripDetail(updatedTrip.id);
            }
            this.showToast('Trip updated successfully ✅');
        } catch (error) {
            console.error('Trip resize failed', error);
            this.showToast('Unable to update trip. Changes reverted ❌');
            this.resetResizePreview(session);
        } finally {
            if (element) {
                element.classList.remove('calendar-trip--updating');
            }
            this.resizeSession = null;
        }
    };
