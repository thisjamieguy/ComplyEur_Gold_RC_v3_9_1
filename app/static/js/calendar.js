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
        safe: '#4CAF50',
        warning: '#FFC107',
        critical: '#F44336'
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
            document.body.appendChild(tooltipEl);
            return tooltipEl;
        }

        return {
            show(content, x, y, options = {}) {
                const el = ensureElement();
                el.innerHTML = content;
                if (options && options.accent) {
                    el.style.setProperty('--calendar-tooltip-accent', options.accent);
                }
                el.style.left = `${x + 16}px`;
                el.style.top = `${y + 16}px`;
                requestAnimationFrame(() => {
                    el.classList.add('calendar-tooltip--visible');
                    visible = true;
                });
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
            isSubmittingForm: false
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
            toast: root.querySelector('#calendar-toast')
        };
        this.tooltip = createTooltip();
        this.editTripButtons = Array.from(root.querySelectorAll('[data-action="edit-trip"]'));
        if (this.elements.editTripGlobal) {
            this.editTripButtons.push(this.elements.editTripGlobal);
        }
        this.formCloseButtons = Array.from(root.querySelectorAll('[data-action="close-form"]'));
        this.timelineWidth = 0;
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
        this.handleTimelineScroll = this.handleTimelineScroll.bind(this);
        this.handleTimelineVerticalScroll = this.handleTimelineVerticalScroll.bind(this);
        this.handleTripClick = this.handleTripClick.bind(this);
        this.handleTripKeydown = this.handleTripKeydown.bind(this);
        this.handleOverlayInteraction = this.handleOverlayInteraction.bind(this);
        this.handleGlobalKeydown = this.handleGlobalKeydown.bind(this);
        this.handleWindowResize = this.handleWindowResize.bind(this);
        this.handleGridMouseover = this.handleGridMouseover.bind(this);
        this.handleGridMousemove = this.handleGridMousemove.bind(this);
        this.handleGridMouseout = this.handleGridMouseout.bind(this);
        this.emptyStateMessageNode = this.elements.empty ? this.elements.empty.querySelector('p') : null;
        this.emptyStateDefaultMessage = this.emptyStateMessageNode ? this.emptyStateMessageNode.textContent : '';
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
                onDrop: (details) => this.handleTripDrop(details)
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
        if (this.elements.timelineContainer) {
            this.elements.timelineContainer.addEventListener('scroll', this.handleTimelineScroll, { passive: true });
            this.elements.timelineContainer.addEventListener('scroll', this.handleTimelineVerticalScroll, { passive: true });
        }
        if (this.elements.employeeList) {
            this.elements.employeeList.addEventListener('scroll', this.handleTimelineVerticalScroll, { passive: true });
        }
        if (this.elements.grid) {
            this.elements.grid.addEventListener('mouseover', (event) => this.handleGridMouseover(event));
            this.elements.grid.addEventListener('mousemove', this.handleGridMousemove);
            this.elements.grid.addEventListener('mouseout', (event) => this.handleGridMouseout(event));
            this.elements.grid.addEventListener('click', this.handleTripClick);
            this.elements.grid.addEventListener('keydown', this.handleTripKeydown);
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
        this.updateGlobalEditButtonState();
        window.addEventListener('resize', this.handleWindowResize, { passive: true });
        document.addEventListener('keydown', this.handleGlobalKeydown);
    };

    CalendarController.prototype.handleTimelineScroll = function handleTimelineScroll(event) {
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

    CalendarController.prototype.handleGridMouseover = function handleGridMouseover(event) {
        if (this.isDetailOpen || !this.tooltip) {
            return;
        }
        const tripTarget = event.target.closest('.calendar-trip');
        if (tripTarget) {
            const employee = tripTarget.getAttribute('data-employee');
            const country = tripTarget.getAttribute('data-country');
            const start = tripTarget.getAttribute('data-start');
            const end = tripTarget.getAttribute('data-end');
            const jobRef = tripTarget.getAttribute('data-job-ref');
            const statusLabel = tripTarget.getAttribute('data-status-label');
            const riskDays = tripTarget.getAttribute('data-risk-days-used') || tripTarget.getAttribute('data-days-used') || '0';
            const riskColor = tripTarget.getAttribute('data-risk-color') || RISK_COLORS.safe;

            const lines = [
                `<strong>${employee || 'Unknown employee'}</strong>`,
                `<span>${country || 'Unknown country'}</span>`,
                `<span>${start} → ${end}</span>`,
                `<span class="calendar-tooltip-metric">Days used: ${riskDays} / ${RISK_THRESHOLDS.limit}</span>`
            ];

            if (jobRef) {
                lines.push(`<span>Job ref: ${jobRef}</span>`);
            }
            if (statusLabel) {
                lines.push(`<span>${statusLabel}</span>`);
            }

            this.tooltip.show(lines.map((line) => `<div>${line}</div>`).join(''), event.pageX, event.pageY, { accent: riskColor });
            return;
        }

        const cellTarget = event.target.closest('.calendar-cell');
        if (cellTarget) {
            const riskDays = cellTarget.dataset.riskDaysUsed || '0';
            const riskLevel = cellTarget.dataset.riskLevel || 'safe';
            const riskColor = cellTarget.dataset.riskColor || RISK_COLORS.safe;
            const dateLabel = cellTarget.dataset.calendarDate ? `<span>${cellTarget.dataset.calendarDate}</span>` : '';
            const label = riskLevel === 'safe' ? 'Compliant window' : riskLevel === 'caution' ? 'Approaching limit' : 'Non-compliant';
            const employeeName = cellTarget.dataset.employeeName || '';

            const content = [
                employeeName ? `<strong>${sanitizeText(employeeName)}</strong>` : '',
                dateLabel,
                `<span class="calendar-tooltip-metric">Days used: ${riskDays} / ${RISK_THRESHOLDS.limit}</span>`,
                `<span>${label}</span>`
            ].filter(Boolean).map((line) => `<div>${line}</div>`).join('');

            this.tooltip.show(content, event.pageX, event.pageY, { accent: riskColor });
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
        this.lastFocusedTrip = target;
        this.openTripDetail(tripId, target);
    };

    CalendarController.prototype.handleTripKeydown = function handleTripKeydown(event) {
        const target = event.target.closest('.calendar-trip');
        if (!target) {
            return;
        }
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            const tripId = Number.parseInt(target.getAttribute('data-trip-id'), 10);
            if (!Number.isFinite(tripId)) {
                return;
            }
            this.lastFocusedTrip = target;
            this.openTripDetail(tripId, target);
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
        const targetElement = originElement || (this.elements.grid ? this.elements.grid.querySelector(`.calendar-trip[data-trip-id="${tripId}"]`) : null);
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
            let response;
            if (this.state.formMode === 'edit' && Number.isFinite(this.state.editingTripId)) {
                response = await fetch(`/api/trips/${this.state.editingTripId}`, {
                    method: 'PATCH',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
            } else {
                response = await fetch('/api/trips', {
                    method: 'POST',
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

            const result = await response.json();
            const normalised = normaliseTrip(result);
            if (!normalised) {
                throw new Error('Unexpected response payload from server.');
            }

            this.focusEmployeeId = normalised.employeeId;
            this.pendingCenterDate = normalised.start instanceof Date ? normalised.start : parseDate(normalised.start);
            this.pendingFocusTripId = normalised.id;
            const successMessage = this.state.formMode === 'edit' ? 'Trip updated successfully ✅' : 'Trip added successfully ✅';

            await this.loadData({
                force: true,
                centerOnToday: false,
                centerOnDate: this.pendingCenterDate instanceof Date ? this.pendingCenterDate : null
            });

            this.closeForm();
            this.showToast(successMessage);

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
            console.error('Trip save failed', error);
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
            tripBlock.textContent = trip.country || 'Trip';

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

    CalendarController.prototype.handleTripDrop = async function handleTripDrop(details) {
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
            const updatedTrip = await this.patchTripDates(tripId, nextStart, nextEnd);
            this.integrateTripUpdate(updatedTrip);
            const statusIndex = this.recalculateEmployeeStatuses(updatedTrip.employeeId);
            this.applyStatusUpdatesToEmployee(updatedTrip.employeeId, statusIndex);

            if (this.isDetailOpen && this.activeTripId === updatedTrip.id) {
                this.openTripDetail(updatedTrip.id);
            }

            this.showToast('Trip updated successfully ✅');
        } catch (error) {
            console.error('Drag-and-drop update failed', error);
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

    CalendarController.prototype.patchTripDates = async function patchTripDates(tripId, startDate, endDate) {
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
            start_date: serialiseDate(startDate),
            end_date: serialiseDate(endDate)
        };

        const response = await fetch(`/api/trips/${tripId}`, {
            method: 'PATCH',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

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

        const result = await response.json();
        const normalised = normaliseTrip(result);
        if (!normalised) {
            throw new Error('Unexpected payload received from server.');
        }

        return normalised;
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
        node.textContent = trip.country || 'Trip';
        node.style.setProperty('--calendar-trip-color', statusColor);

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
