import { CalendarSidebar } from './calendar_sidebar.js';
import { InteractionManager } from './interaction/InteractionManager.js';
import { DebugOverlay } from './overlays/debug_overlay.js';

const ENABLE_TRIP_DND = window.ENABLE_TRIP_DND ?? false;
const EDGE_RESIZE_HITBOX = 6;

class CalendarApp {
  constructor(options = {}) {
    this.options = options;
    this.gridEl = document.getElementById('calendarGrid');
    this.calendarMainEl = document.querySelector('.calendar-main');
    this.monthLabel = document.getElementById('monthLabel');
    this.modal = document.getElementById('tripModal');
    this.form = document.getElementById('tripForm');
    this.deleteBtn = document.getElementById('deleteTripBtn');
    this.cancelBtn = document.getElementById('cancelModal');
    this.tooltip = document.getElementById('tripTooltip');
    this.contextMenu = document.getElementById('tripContextMenu');
    this.laneBoard = document.getElementById('employeeLaneBoard');
    this.dragOverlay = document.getElementById('dragOverlay');
    this.dragHud = document.getElementById('dragDebugHud');
    this.hudToggle = document.getElementById('toggleDragHud');

    const sidebarContainer = document.getElementById('calendarSidebar');
    this.sidebar = sidebarContainer ? new CalendarSidebar(sidebarContainer) : null;

    const defaultDate = options.defaultDate || window.__CALENDAR_DEFAULT_DATE;
    this.currentDate = defaultDate ? this.toLocalDate(defaultDate) : new Date();
    this.trips = [];
    this.nextId = 1;
    this.mode = 'create';
    this.activeTripId = null;
    this.contextTrip = null;

    this.dragState = { active: false, startDate: null };
    this.justDraggedTripId = null;
    this.visibleDays = [];
    this.dayIndexByISO = new Map();
    this.employeeLaneByName = new Map();
    this.employeeNameByLane = new Map();
    this.previewLaneId = null;
    this.cachedCalendarRect = null;
    this.cellMetrics = null;
    this.gridOffset = { left: 0, top: 0 };
    this.pointerMode = null;
    this.activePointerId = null;
    this.activeTripEl = null;
    this.pendingProxyPreview = null;
    this.proxyRaf = null;
    this.dragProxyEl = null;
    this.lastPreview = null;
    this.pointerOverlay = this.dragOverlay;
    this.gridIsRTL = false;
    this.zoomFactor = 1;
    this.lastPointerCellIndex = null;

    this.boundPointerDown = this.handlePointerDown.bind(this);
    this.boundPointerMove = this.handlePointerMove.bind(this);
    this.boundPointerUp = this.handlePointerUp.bind(this);
    this.boundNativeDrag = this.preventNativeDrag.bind(this);
    this.boundActivePointerMove = (event) => this.handleActivePointerMove(event);
    this.boundActivePointerUp = (event) => this.handleActivePointerEnd(event, false);
    this.boundActivePointerCancel = (event) => this.handleActivePointerEnd(event, true);
    this.boundViewportMetrics = () => this.refreshGeometryCache();

    this.storageKey = 'calendarDevTrips';
    this.isSandbox = Array.isArray(options.sandboxTrips || window.__CALENDAR_SANDBOX_TRIPS);
    this.sandboxTrips = options.sandboxTrips || window.__CALENDAR_SANDBOX_TRIPS;

    this.debugOverlay =
      this.dragOverlay && this.dragHud ? new DebugOverlay({ hudEl: this.dragHud, overlayEl: this.dragOverlay }) : null;
    this.debugEnabled =
      options.debug ??
      new URLSearchParams(window.location.search).get('debug') === '1';
    if (this.debugOverlay && this.debugEnabled) {
      this.debugOverlay.setEnabled(true);
    }
    this.hudToggle?.addEventListener('click', () => this.debugOverlay?.toggle());
    document.addEventListener('keydown', (event) => {
      if ((event.key === 'd' || event.key === 'D') && !event.metaKey && !event.ctrlKey && !event.altKey) {
        this.debugOverlay?.toggle();
      }
    });
    window.visualViewport?.addEventListener('resize', this.boundViewportMetrics);
    window.visualViewport?.addEventListener('scroll', this.boundViewportMetrics);

    this.interactionManager = ENABLE_TRIP_DND
      ? new InteractionManager({
          getCalendarRect: () => this.getCalendarRect(),
          clientXToCellIndex: (clientX, clientY) => this.pointToCellIndex(clientX, clientY),
          commitTripUpdate: (tripId, start, end) => this.commitTripUpdate(tripId, start, end),
          onPreview: (preview) => this.handleInteractionPreview(preview),
          addDays: (date, amount) => this.addDays(date, amount),
          onStateChange: (next, prev, meta) => this.handleStateTransition(next, prev, meta),
        })
      : null;

    this.init();
  }

  async init() {
    await this.loadTrips();
    this.bindEvents();
    this.render();
  }

  async loadTrips() {
    try {
      if (this.isSandbox) {
        const sandboxSource = Array.isArray(this.sandboxTrips) ? this.sandboxTrips : [];
        this.trips = sandboxSource.map((trip) => this.normalizeTrip(trip));
        this.nextId = (Math.max(0, ...this.trips.map((t) => Number(t.id) || 0)) || 0) + 1;
        return;
      }
      const storedTrips = this.loadPersistedTrips();
      if (storedTrips && storedTrips.length) {
        this.trips = storedTrips;
        this.nextId = (Math.max(0, ...this.trips.map((t) => Number(t.id) || 0)) || 0) + 1;
        return;
      }
      const response = await fetch('calendar_mock_data.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('Failed to load mock data');
      const payload = await response.json();
      this.trips = payload.map((trip) => this.normalizeTrip(trip));
      this.nextId = (Math.max(0, ...this.trips.map((t) => Number(t.id) || 0)) || 0) + 1;
      this.persistTrips();
    } catch (error) {
      console.error('Calendar data error:', error);
      this.trips = [];
    }
  }

  normalizeTrip(trip) {
    return {
      id: trip.id ?? crypto.randomUUID?.() ?? Date.now(),
      employee: trip.employee,
      country: trip.country,
      purpose: trip.purpose || '',
      startDate: this.toLocalDate(trip.start_date || trip.startDate),
      endDate: this.toLocalDate(trip.end_date || trip.endDate),
    };
  }

  bindEvents() {
    document.querySelectorAll('.nav-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const delta = btn.dataset.nav === 'next' ? 1 : -1;
        this.currentDate.setMonth(this.currentDate.getMonth() + delta);
        this.render();
      });
    });

    this.gridEl?.addEventListener('pointerdown', this.boundPointerDown, { passive: false });
    document.addEventListener('pointermove', this.boundPointerMove, { passive: false });
    document.addEventListener('pointerup', this.boundPointerUp, { passive: false });
    document.addEventListener('click', (event) => {
      if (this.contextMenu && !event.target.closest('#tripContextMenu')) {
        this.hideContextMenu();
      }
    });
    document.addEventListener('contextmenu', (event) => {
      if (!event.target.closest('.trip-pill')) {
        this.hideContextMenu();
      }
    });
    window.addEventListener('resize', () => {
      this.hideContextMenu();
      this.refreshGeometryCache();
    });
    if (ENABLE_TRIP_DND) {
      window.addEventListener('dragstart', this.boundNativeDrag, true);
    }

    this.form?.addEventListener('submit', (event) => this.handleFormSubmit(event));
    this.cancelBtn?.addEventListener('click', () => this.closeModal());
    this.deleteBtn?.addEventListener('click', () => this.handleDelete());
    this.contextMenu?.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-action]');
      if (!button || !this.contextTrip) return;
      const action = button.dataset.action;
      if (action === 'edit') {
        this.hideContextMenu();
        this.openModal('edit', this.contextTrip);
      } else if (action === 'delete') {
        this.hideContextMenu();
        if (confirm('Delete this trip?')) {
          this.deleteTripById(this.contextTrip.id);
        }
      }
    });
  }

  render() {
    const state = this.createRenderState();
    this.renderCalendar(state);
    this.updateSidebar(state);
  }

  createRenderState() {
    return Object.freeze({
      currentDate: new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), this.currentDate.getDate()),
      trips: this.trips.map((trip) => ({
        ...trip,
        startDate: this.toLocalDate(trip.startDate),
        endDate: this.toLocalDate(trip.endDate),
      })),
    });
  }

  renderCalendar(state = this.createRenderState()) {
    const monthLabel = state.currentDate.toLocaleString('en-US', { month: 'long', year: 'numeric' });
    this.monthLabel.textContent = monthLabel;

    const days = this.generateCalendarDays(state.currentDate);
    this.visibleDays = days;
    this.dayIndexByISO = new Map(days.map(({ date }, index) => [this.formatISO(date), index]));
    this.gridEl.innerHTML = days
      .map(({ date, inMonth }, index) => {
        const dateLabel = date.getDate();
        const iso = this.formatISO(date);
        const trips = this.getTripsForDateFromState(state, date);
        const pills = trips
          .map((trip) => {
            const color = this.getTripColorClass(trip);
            const tripStartIso = this.formatISO(trip.startDate);
            const tripEndIso = this.formatISO(trip.endDate);
            const isStart = tripStartIso === iso;
            const isEnd = tripEndIso === iso;
            const handles = [
              isStart
                ? '<span class="resize-handle resize-handle-left" data-resize="start" aria-label="Extend trip earlier"></span>'
                : '',
              isEnd
                ? '<span class="resize-handle resize-handle-right" data-resize="end" aria-label="Extend trip later"></span>'
                : '',
            ].join('');
            return `<div class="trip-pill ${color} ${isStart ? 'trip-pill-start' : ''} ${isEnd ? 'trip-pill-end' : ''}" data-trip-id="${trip.id}" data-date="${iso}">
              ${handles}
              <span class="trip-pill-label">${trip.employee.split(' ')[0]} · ${trip.country}</span>
            </div>`;
          })
          .join('');

        return `<div class="day-cell ${inMonth ? '' : 'other-month'}" data-date="${iso}" data-index="${index}">
          <div class="day-label">${dateLabel}</div>
          ${pills}
        </div>`;
      })
      .join('');

    this.renderLaneBoard(state);
    this.attachTripInteractions();
    this.cachedCalendarRect = null;
    this.primeCellMetrics();
  }

  generateCalendarDays(referenceDate) {
    const year = referenceDate.getFullYear();
    const month = referenceDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const leadingEmpty = (firstDay.getDay() + 6) % 7; // convert Sunday start to Monday
    const totalCells = Math.ceil((leadingEmpty + lastDay.getDate()) / 7) * 7;

    const days = [];
    for (let i = 0; i < totalCells; i++) {
      const date = new Date(year, month, 1 - leadingEmpty + i);
      days.push({ date, inMonth: date.getMonth() === month });
    }
    return days;
  }

  getTripsForDate(date) {
    return this.trips.filter((trip) => this.isWithinRange(date, trip.startDate, trip.endDate));
  }

  getTripsForDateFromState(state, date) {
    return state.trips.filter((trip) => this.isWithinRange(date, trip.startDate, trip.endDate));
  }

  getTripColorClass(trip) {
    const duration = this.countTripDays(trip.startDate, trip.endDate);
    if (duration >= 90) return 'trip-red';
    if (duration >= 60) return 'trip-orange';
    return 'trip-green';
  }

  findTripById(id) {
    return this.trips.find((trip) => String(trip.id) === String(id)) || null;
  }

  applyDragResult({ tripId, startDate, endDate, employee }) {
    if (!tripId) return;
    const normalizedStart = this.toLocalDate(startDate);
    const normalizedEnd = this.toLocalDate(endDate);
    const updatedEmployee = employee || this.findTripById(tripId)?.employee;
    this.trips = this.trips.map((trip) =>
      trip.id === tripId
        ? {
            ...trip,
            startDate: normalizedStart,
            endDate: normalizedEnd,
            employee: updatedEmployee,
          }
        : trip
    );
    this.justDraggedTripId = tripId;
    this.render();
    this.persistTrips();
    setTimeout(() => {
      if (this.justDraggedTripId === tripId) {
        this.justDraggedTripId = null;
      }
    }, 0);
  }

  getEmployeeList(trips = this.trips) {
    return [...new Set(trips.map((trip) => trip.employee).filter(Boolean))].sort((a, b) =>
      a.localeCompare(b)
    );
  }

  resetEmployeeDirectories() {
    this.employeeLaneByName.clear();
    this.employeeNameByLane.clear();
  }

  getEmployeeLaneId(name) {
    if (!name) return '';
    if (this.employeeLaneByName.has(name)) {
      return this.employeeLaneByName.get(name);
    }
    const base =
      name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'lane';
    let candidate = base;
    let attempts = 1;
    while (this.employeeNameByLane.has(candidate) && this.employeeNameByLane.get(candidate) !== name) {
      candidate = `${base}-${attempts++}`;
    }
    this.employeeLaneByName.set(name, candidate);
    this.employeeNameByLane.set(candidate, name);
    return candidate;
  }

  getLaneName(laneId) {
    return this.employeeNameByLane.get(laneId) || null;
  }

  getAdjacentEmployee(currentName, direction) {
    const employees = this.getEmployeeList();
    if (!employees.length) return null;
    const index = employees.indexOf(currentName);
    if (index === -1) return null;
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= employees.length) return null;
    return employees[nextIndex];
  }

  countTripsForEmployee(name, trips = this.trips) {
    return trips.filter((trip) => trip.employee === name).length;
  }

  renderLaneBoard(state = this.createRenderState()) {
    if (!this.laneBoard) return;
    if (!ENABLE_TRIP_DND) {
      this.laneBoard.classList.add('hidden');
      this.laneBoard.innerHTML = '';
      return;
    }
    const trips = state?.trips || this.trips;
    this.resetEmployeeDirectories();
    const employees = this.getEmployeeList(trips);
    if (!employees.length) {
      this.laneBoard.classList.remove('hidden');
      this.laneBoard.innerHTML = '<div class="employee-lane lane-empty"><span class="lane-label">No employees</span></div>';
      return;
    }
    this.laneBoard.classList.remove('hidden');
    this.laneBoard.innerHTML = employees
      .map((name) => {
        const laneId = this.getEmployeeLaneId(name);
        const tripCount = this.countTripsForEmployee(name, trips);
        return `<div class="employee-lane" data-employee-id="${laneId}" data-employee-name="${name}">
          <span class="lane-label">${name}</span>
          <span class="lane-meta">${tripCount} trip${tripCount === 1 ? '' : 's'}</span>
        </div>`;
      })
      .join('');
  }

  attachTripInteractions() {
    this.gridEl.querySelectorAll('.trip-pill').forEach((pill) => {
      const trip = this.findTripById(pill.dataset.tripId);
      if (!trip) return;

      pill.addEventListener('mouseenter', (event) => this.showTooltip(event, trip));
      pill.addEventListener('mouseleave', () => this.hideTooltip());
      if (ENABLE_TRIP_DND && this.interactionManager) {
        pill.setAttribute('tabindex', '0');
        pill.addEventListener('pointerdown', (event) => this.handleTripPointerDown(event, trip), { passive: false });
        pill.addEventListener('dragstart', (event) => event.preventDefault());
      }
      pill.addEventListener('click', (event) => {
        const targetEl = event.target instanceof Element ? event.target : null;
        if (targetEl?.closest('.resize-handle')) return;
        event.stopPropagation();
        if (this.justDraggedTripId === trip.id) {
          this.justDraggedTripId = null;
          return;
        }
        this.openModal('edit', trip);
      });
      pill.addEventListener('contextmenu', (event) => {
        event.preventDefault();
        this.showContextMenu(event, trip);
      });
    });
  }

  handleTripPointerDown(event, trip) {
    if (!ENABLE_TRIP_DND || !this.interactionManager) return;
    if (event.button !== 0) return;
    const pill = event.currentTarget;
    this.primeCellMetrics();
    this.cachedCalendarRect = this.getCalendarRect(true);
    this.gridOffset = this.computeGridOffset();
    const context = this.buildTripInteractionContext(trip);
    if (!context) return;
    context.startClientY = event.clientY ?? null;
    const mode = this.resolveInteractionMode(event, pill);
    event.preventDefault();
    event.stopPropagation();
    this.beginPointerSession({ event, trip, pill, mode, context });
  }

  buildTripInteractionContext(trip) {
    const startIso = this.formatISO(trip.startDate);
    const endIso = this.formatISO(trip.endDate);
    const startCellIndex = this.dayIndexByISO.get(startIso);
    const endCellIndex =
      this.dayIndexByISO.get(endIso) ?? Math.max(this.visibleDays.length - 1, startCellIndex ?? 0);
    if (startCellIndex == null) {
      return null;
    }
    return {
      startTrip: {
        startDate: this.toLocalDate(trip.startDate),
        endDate: this.toLocalDate(trip.endDate),
        startCellIndex,
        endCellIndex,
      },
      snapWidthPx: this.cellMetrics?.snapWidth || 1,
      baseRect: this.cachedCalendarRect,
    };
  }

  resolveInteractionMode(event, pill) {
    const rect = pill.getBoundingClientRect();
    const nearLeft = Math.abs(event.clientX - rect.left) <= EDGE_RESIZE_HITBOX;
    const nearRight = Math.abs(rect.right - event.clientX) <= EDGE_RESIZE_HITBOX;
    const isStart = pill.classList.contains('trip-pill-start');
    const isEnd = pill.classList.contains('trip-pill-end');
    if (nearLeft && isStart) return 'resize-left';
    if (nearRight && isEnd) return 'resize-right';
    return 'drag';
  }

  beginPointerSession({ event, trip, pill, mode, context }) {
    this.pointerMode = mode;
    this.activePointerId = event.pointerId;
    this.activeTripEl = pill;
    this.activateOverlay(mode);
    this.createProxy(pill);
    pill.classList.add('dragging');
    try {
      pill.setPointerCapture(event.pointerId);
    } catch {
      // ignore capture errors
    }
    window.addEventListener('pointermove', this.boundActivePointerMove, { passive: false });
    window.addEventListener('pointerup', this.boundActivePointerUp, { passive: false });
    window.addEventListener('pointercancel', this.boundActivePointerCancel, { passive: false });
    if (mode === 'drag') {
      this.interactionManager.beginDrag(trip.id, event.clientX, context);
    } else {
      const edge = mode === 'resize-left' ? 'left' : 'right';
      this.interactionManager.beginResize(trip.id, edge, event.clientX, context);
    }
  }

  handleActivePointerMove(event) {
    if (this.activePointerId == null || event.pointerId !== this.activePointerId) return;
    event.preventDefault();
    this.interactionManager?.updatePointer(event.clientX, event.clientY);
  }

  handleActivePointerEnd(event, forceCancel = false) {
    if (this.activePointerId == null || event.pointerId !== this.activePointerId) return;
    event.preventDefault();
    if (forceCancel) {
      this.interactionManager?.cancel();
    } else {
      this.interactionManager?.commit();
    }
    this.teardownPointerSession();
  }

  teardownPointerSession() {
    if (this.activeTripEl && this.activePointerId != null) {
      try {
        this.activeTripEl.releasePointerCapture(this.activePointerId);
      } catch {
        // ignore release errors
      }
      this.activeTripEl.classList.remove('dragging');
    }
    window.removeEventListener('pointermove', this.boundActivePointerMove, { passive: false });
    window.removeEventListener('pointerup', this.boundActivePointerUp, { passive: false });
    window.removeEventListener('pointercancel', this.boundActivePointerCancel, { passive: false });
    this.deactivateOverlay();
    this.destroyProxy();
    this.activePointerId = null;
    this.activeTripEl = null;
    this.pointerMode = null;
  }

  activateOverlay(mode) {
    if (!this.pointerOverlay) return;
    this.pointerOverlay.classList.add('is-active');
    this.pointerOverlay.dataset.mode = mode;
  }

  deactivateOverlay() {
    if (!this.pointerOverlay) return;
    this.pointerOverlay.classList.remove('is-active');
    delete this.pointerOverlay.dataset.mode;
  }

  createProxy(pill) {
    if (!this.dragOverlay || !pill) return;
    this.destroyProxy();
    const proxy = pill.cloneNode(true);
    proxy.classList.add('trip-pill-proxy');
    proxy.style.transform = 'translate(0, 0)';
    proxy.style.width = `${pill.getBoundingClientRect().width}px`;
    proxy.style.height = `${pill.getBoundingClientRect().height}px`;
    this.dragOverlay.appendChild(proxy);
    this.dragProxyEl = proxy;
  }

  destroyProxy() {
    if (this.dragProxyEl?.parentNode) {
      this.dragProxyEl.parentNode.removeChild(this.dragProxyEl);
    }
    this.dragProxyEl = null;
    if (this.proxyRaf) {
      cancelAnimationFrame(this.proxyRaf);
      this.proxyRaf = null;
    }
    this.pendingProxyPreview = null;
  }

  scheduleProxyRender(preview) {
    this.pendingProxyPreview = preview;
    if (this.proxyRaf) return;
    this.proxyRaf = requestAnimationFrame(() => this.flushProxyRender());
  }

  flushProxyRender() {
    this.proxyRaf = null;
    const preview = this.pendingProxyPreview;
    if (!preview || !this.dragProxyEl || !this.cellMetrics) {
      if (!preview) {
        this.destroyProxy();
      }
      return;
    }
    const daySpan = Math.max(1, preview.range.endCellIndex - preview.range.startCellIndex + 1);
    const column = preview.range.startCellIndex % 7;
    const row = Math.floor(preview.range.startCellIndex / 7);
    const segmentWidth =
      daySpan * this.cellMetrics.width + Math.max(0, daySpan - 1) * this.cellMetrics.columnGap;
    const left =
      this.gridOffset.left + column * (this.cellMetrics.width + this.cellMetrics.columnGap);
    const top = this.gridOffset.top + row * (this.cellMetrics.height + this.cellMetrics.rowGap);
    this.dragProxyEl.style.transform = `translate(${left}px, ${top}px)`;
    this.dragProxyEl.style.width = `${segmentWidth}px`;
    this.dragProxyEl.style.height = `${this.cellMetrics.height}px`;
    if (this.debugOverlay && this.lastPreview) {
      this.debugOverlay.updateRects({
        calendarRect: this.cachedCalendarRect,
        proxyRect: this.dragProxyEl.getBoundingClientRect(),
        snapRect: this.getCellRect(this.lastPreview.currentCellIndex),
      });
    }
  }

  handleInteractionPreview(preview) {
    this.lastPreview = preview;
    if (!preview) {
      this.renderTripPreview(null, null);
      this.scheduleProxyRender(null);
      this.debugOverlay?.updateInfo(null);
      this.debugOverlay?.updateRects({ calendarRect: null, proxyRect: null, snapRect: null });
      if (typeof window !== 'undefined' && typeof window.__virtualizationProbe === 'function') {
        try {
          window.__virtualizationProbe({
            visibleLength: this.visibleDays.length,
            cellCount: this.gridEl?.querySelectorAll('.day-cell').length || 0,
            active: false,
          });
        } catch {
          // ignore probe errors
        }
      }
      return;
    }
    this.renderTripPreview(preview.nextStartDate, preview.nextEndDate);
    this.scheduleProxyRender(preview);
    this.debugOverlay?.updateInfo(preview);
    if (this.debugOverlay) {
      const snapRect = this.getCellRect(preview.currentCellIndex);
      this.debugOverlay.updateRects({
        calendarRect: this.cachedCalendarRect,
        proxyRect: null,
        snapRect,
      });
    }
    if (typeof window !== 'undefined' && typeof window.__virtualizationProbe === 'function') {
      try {
        window.__virtualizationProbe({
          visibleLength: this.visibleDays.length,
          cellCount: this.gridEl?.querySelectorAll('.day-cell').length || 0,
          active: true,
        });
      } catch {
        // ignore probe errors
      }
    }
  }

  handleStateTransition(next, prev, meta) {
    this.debugOverlay?.logTransition(prev, next, { ...meta, previewPayload: this.lastPreview });
  }

  commitTripUpdate(tripId, newStartDate, newEndDate) {
    this.applyDragResult({ tripId, startDate: newStartDate, endDate: newEndDate });
    this.lastCommit = {
      tripId,
      startDate: this.formatISO(newStartDate),
      endDate: this.formatISO(newEndDate),
    };
  }

  primeCellMetrics() {
    if (!this.gridEl) return;
    const firstCell = this.gridEl.querySelector('.day-cell');
    if (!firstCell) {
      this.cellMetrics = null;
      return;
    }
    const cellRect = firstCell.getBoundingClientRect();
    const styles = window.getComputedStyle(this.gridEl);
    const columnGap = parseFloat(styles.columnGap) || 0;
    const rowGap = parseFloat(styles.rowGap) || 0;
    this.cellMetrics = {
      width: cellRect.width,
      height: cellRect.height,
      columnGap,
      rowGap,
      snapWidth: cellRect.width + columnGap,
    };
    this.gridIsRTL = window.getComputedStyle(this.gridEl).direction === 'rtl';
    this.zoomFactor = this.getCurrentZoomLevel();
  }

  refreshGeometryCache() {
    this.cachedCalendarRect = null;
    this.primeCellMetrics();
  }

  getCurrentZoomLevel() {
    try {
      if (window.visualViewport) {
        const viewportScale = Number(window.visualViewport.scale);
        if (Number.isFinite(viewportScale) && viewportScale > 0) {
          return viewportScale;
        }
      }
      const computedZoom = Number(window.getComputedStyle(document.body).zoom);
      if (Number.isFinite(computedZoom) && computedZoom > 0) {
        return computedZoom;
      }
    } catch {
      // ignore zoom probes
    }
    return 1;
  }

  computeGridOffset() {
    if (!this.calendarMainEl || !this.gridEl) return { left: 0, top: 0 };
    const mainRect = this.calendarMainEl.getBoundingClientRect();
    const gridRect = this.gridEl.getBoundingClientRect();
    return {
      left: gridRect.left - mainRect.left + (this.calendarMainEl.scrollLeft || 0),
      top: gridRect.top - mainRect.top + (this.calendarMainEl.scrollTop || 0),
    };
  }

  getCalendarRect(force = false) {
    if (!this.gridEl) return null;
    if (!force && this.cachedCalendarRect) return this.cachedCalendarRect;
    const scroller = this.calendarMainEl || this.gridEl;
    const rect = scroller.getBoundingClientRect();
    const gridRect = this.gridEl?.getBoundingClientRect();
    this.cachedCalendarRect = {
      left: rect.left,
      right: rect.right,
      top: rect.top,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height,
      scrollLeft: scroller.scrollLeft || 0,
      scrollTop: scroller.scrollTop || 0,
      dpr: window.devicePixelRatio || 1,
      gridLeft: gridRect?.left ?? rect.left,
      gridTop: gridRect?.top ?? rect.top,
    };
    return this.cachedCalendarRect;
  }

  pointToCellIndex(clientX, clientY) {
    const currentZoom = this.getCurrentZoomLevel();
    const zoomBaseline = this.zoomFactor ?? currentZoom;
    if (!this.cellMetrics || Math.abs(currentZoom - zoomBaseline) > 0.005) {
      this.refreshGeometryCache();
    }
    const rect = this.cachedCalendarRect || this.getCalendarRect();
    if (!rect || !this.cellMetrics || !this.visibleDays.length) return null;
    const columns = 7;
    const totalRows = Math.ceil(this.visibleDays.length / columns);
    if (typeof clientX === 'number' && typeof clientY === 'number') {
      let hitCell = null;
      const topHit = document.elementFromPoint(clientX, clientY);
      if (topHit instanceof Element) {
        hitCell = topHit.closest('.day-cell');
      }
      if (!hitCell && document.elementsFromPoint) {
        const stack = document.elementsFromPoint(clientX, clientY);
        hitCell = stack.find((el) => el instanceof Element && el.classList?.contains('day-cell')) || null;
      }
      if (hitCell?.dataset.index) {
        const idx = Number(hitCell.dataset.index);
        if (!Number.isNaN(idx)) {
          this.lastPointerCellIndex = idx;
          return idx;
        }
      }
    }
    const relX = clientX != null ? clientX : rect.left;
    const relY = clientY != null ? clientY : rect.top;
    const baseLeft = rect.gridLeft ?? rect.left;
    const baseTop = rect.gridTop ?? rect.top;
    const offsetX = relX - baseLeft + (rect.scrollLeft || 0);
    const offsetY = relY - baseTop + (rect.scrollTop || 0);
    const snapX = Math.max(1, this.cellMetrics.snapWidth || this.cellMetrics.width);
    const snapY = Math.max(1, this.cellMetrics.height + this.cellMetrics.rowGap);
    const rawColumn = Math.floor(offsetX / snapX);
    const column = this.gridIsRTL ? columns - 1 - rawColumn : rawColumn;
    const row = Math.floor(offsetY / snapY);
    const clampedColumn = Math.min(Math.max(column, 0), columns - 1);
    const clampedRow = Math.min(Math.max(row, 0), totalRows - 1);
    const index = clampedRow * columns + clampedColumn;
    const normalized = Math.min(Math.max(index, 0), this.visibleDays.length - 1);
    this.lastPointerCellIndex = normalized;
    return normalized ?? this.lastPointerCellIndex;
  }

  getCellRect(index) {
    if (index == null) return null;
    const cell = this.gridEl?.querySelector(`.day-cell[data-index=\"${index}\"]`);
    return cell?.getBoundingClientRect() ?? null;
  }

  renderTripPreview(start, end, laneId = null) {
    this.clearTripPreview();
    if (!start || !end) return;
    const [min, max] = start <= end ? [start, end] : [end, start];
    this.gridEl.querySelectorAll('.day-cell').forEach((cell) => {
      const cellDate = this.toLocalDate(cell.dataset.date);
      if (cellDate >= min && cellDate <= max) {
        cell.classList.add('trip-preview');
      }
    });
    this.highlightLane(laneId);
  }

  clearTripPreview() {
    this.gridEl.querySelectorAll('.day-cell.trip-preview').forEach((cell) =>
      cell.classList.remove('trip-preview')
    );
    this.highlightLane(null);
  }

  highlightLane(laneId) {
    if (!this.laneBoard) return;
    if (this.previewLaneId && this.previewLaneId !== laneId) {
      const previous = this.laneBoard.querySelector(`[data-employee-id="${this.previewLaneId}"]`);
      previous?.classList.remove('lane-preview');
    }
    if (laneId) {
      const target = this.laneBoard.querySelector(`[data-employee-id="${laneId}"]`);
      target?.classList.add('lane-preview');
      this.previewLaneId = laneId;
    } else {
      this.previewLaneId = null;
    }
  }

  handlePointerDown(event) {
    if (event.button !== 0) return;
    const targetEl = event.target instanceof Element ? event.target : null;
    if (targetEl?.closest('.trip-pill')) return;
    const cell = targetEl?.closest('.day-cell');
    if (!cell) return;
    this.dragState = {
      active: true,
      startDate: cell.dataset.date,
    };
    this.highlightRange(cell.dataset.date, cell.dataset.date);
  }

  handlePointerMove(event) {
    if (!this.dragState.active) return;
    const cell = this.resolveCellForSelection(event);
    if (!cell) return;
    this.highlightRange(this.dragState.startDate, cell.dataset.date);
  }

  handlePointerUp(event) {
    if (!this.dragState.active) return;
    const cell = this.resolveCellForSelection(event);
    const startDate = this.dragState.startDate;
    const endDate = cell ? cell.dataset.date : startDate;
    this.dragState = { active: false, startDate: null };
    this.clearHighlights();
    if (startDate && endDate) {
      this.openModal('create', {
        startDate,
        endDate,
      });
    }
  }

  resolveCellForSelection(event) {
    if (typeof event.clientX === 'number' && typeof event.clientY === 'number') {
      const fromPoint = document.elementFromPoint(event.clientX, event.clientY);
      if (fromPoint instanceof Element) {
        const cell = fromPoint.closest('.day-cell');
        if (cell) return cell;
      }
    }
    const targetEl = event.target instanceof Element ? event.target : null;
    return targetEl?.closest('.day-cell') || null;
  }

  highlightRange(startISO, endISO) {
    if (!startISO || !endISO) return;
    const start = new Date(startISO);
    const end = new Date(endISO);
    const [min, max] = start <= end ? [start, end] : [end, start];
    this.clearHighlights();
    this.gridEl.querySelectorAll('.day-cell').forEach((cell) => {
      const date = new Date(cell.dataset.date);
      if (date >= min && date <= max) {
        cell.classList.add('selection-active');
      }
    });
  }

  clearHighlights() {
    this.gridEl.querySelectorAll('.day-cell.selection-active').forEach((cell) =>
      cell.classList.remove('selection-active')
    );
  }

  preventNativeDrag(event) {
    if (!ENABLE_TRIP_DND) return;
    const targetEl = event.target instanceof Element ? event.target : null;
    if (targetEl?.closest('.trip-pill')) {
      event.preventDefault();
    }
  }

  openModal(mode, data = {}) {
    if (!this.modal || !this.form) return;
    this.mode = mode;
    this.activeTripId = data.id ?? null;
    this.hideContextMenu();
    document.getElementById('modalTitle').textContent = mode === 'edit' ? 'Edit Trip' : 'Add Trip';

    const employee = data.employee || '';
    const country = data.country || '';
    const startInput = data.startDate || data.start_date || data.start;
    const endInput = data.endDate || data.end_date || data.end;
    const startDate = startInput ? this.formatISO(this.toLocalDate(startInput)) : '';
    const endDate = endInput ? this.formatISO(this.toLocalDate(endInput)) : '';

    this.form.employee.value = employee;
    this.form.country.value = country;
    this.form.startDate.value = startDate || '';
    this.form.endDate.value = endDate || '';

    if (this.deleteBtn) {
      this.deleteBtn.style.display = mode === 'edit' ? 'inline-flex' : 'none';
    }

    this.modal.classList.remove('hidden');
  }

  closeModal() {
    if (!this.modal || !this.form) return;
    this.modal.classList.add('hidden');
    this.form.reset();
    this.activeTripId = null;
    this.hideContextMenu();
  }

  handleFormSubmit(event) {
    if (!this.form) return;
    event.preventDefault();
    const formData = new FormData(this.form);
    const payload = Object.fromEntries(formData.entries());
    const start = this.toLocalDate(payload.startDate);
    const end = this.toLocalDate(payload.endDate);

    if (!payload.employee || !payload.country) {
      alert('Employee and Country are required.');
      return;
    }

    if (end < start) {
      alert('End date cannot be before start date.');
      return;
    }

    if (this.mode === 'edit' && this.activeTripId) {
      this.trips = this.trips.map((trip) =>
        trip.id === this.activeTripId
          ? {
              ...trip,
              employee: payload.employee,
              country: payload.country,
              startDate: start,
              endDate: end,
            }
          : trip
      );
    } else {
      this.trips.push({
        id: this.nextId++,
        employee: payload.employee,
        country: payload.country,
        startDate: start,
        endDate: end,
      });
    }

    this.closeModal();
    this.render();
    this.persistTrips();
  }

  handleDelete() {
    if (!this.activeTripId) return;
    this.deleteTripById(this.activeTripId);
    this.closeModal();
  }

  deleteTripById(id) {
    this.trips = this.trips.filter((trip) => trip.id !== id);
    this.render();
    this.persistTrips();
  }

  resizeTrip(tripId, newStart, newEnd) {
    this.applyDragResult({ tripId, startDate: newStart, endDate: newEnd });
  }

  updateSidebar(state = this.createRenderState()) {
    if (!this.sidebar) return;
    const activeState = state || this.createRenderState();
    const trips = activeState.trips || this.trips;
    const reference = new Date(activeState.currentDate.getFullYear(), activeState.currentDate.getMonth() + 1, 0);
    const totalDays = this.calculateRollingTotal(reference, trips);
    const nextTrip = this.getNextUpcomingTrip(trips);
    const upcomingTrips = this.getUpcomingTrips(3, trips);

    this.sidebar.updateSidebar({
      totalDays,
      nextTrip,
      riskPercent: Math.min(totalDays / 90, 1),
      upcomingTrips,
    });
  }

  calculateRollingTotal(referenceDate, trips = this.trips) {
    const windowStart = new Date(referenceDate);
    windowStart.setDate(windowStart.getDate() - 179);

    return trips.reduce((sum, trip) => {
      const overlap = this.getOverlapDays(windowStart, referenceDate, trip.startDate, trip.endDate);
      return sum + overlap;
    }, 0);
  }

  getOverlapDays(windowStart, windowEnd, rangeStart, rangeEnd) {
    const start = rangeStart < windowStart ? windowStart : rangeStart;
    const end = rangeEnd > windowEnd ? windowEnd : rangeEnd;
    if (end < start) return 0;
    return this.countTripDays(start, end);
  }

  countTripDays(start, end) {
    const ms = this.toLocalDate(end).getTime() - this.toLocalDate(start).getTime();
    return Math.floor(ms / (1000 * 60 * 60 * 24)) + 1;
  }

  addDays(date, amount) {
    const next = this.toLocalDate(date);
    next.setDate(next.getDate() + amount);
    return next;
  }

  diffInDays(a, b) {
    const first = this.toLocalDate(a);
    const second = this.toLocalDate(b);
    return Math.round((first.getTime() - second.getTime()) / (1000 * 60 * 60 * 24));
  }

  getNextUpcomingTrip(trips = this.trips) {
    const today = this.toLocalDate(new Date());
    return (
      [...trips]
        .filter((trip) => trip.startDate >= today)
        .sort((a, b) => a.startDate - b.startDate)[0] || null
    );
  }

  getUpcomingTrips(limit = 3, trips = this.trips) {
    const today = this.toLocalDate(new Date());
    return [...trips]
      .filter((trip) => trip.startDate >= today)
      .sort((a, b) => a.startDate - b.startDate)
      .slice(0, limit);
  }

  showTooltip(event, trip) {
    if (!this.tooltip) return;
    const tooltipContent = `
      <strong>${trip.employee}</strong><br>
      ${trip.country}<br>
      ${this.formatDate(trip.startDate)} → ${this.formatDate(trip.endDate)}
    `;
    this.tooltip.innerHTML = tooltipContent;
    this.tooltip.classList.remove('hidden');
    const { clientX, clientY } = event;
    this.tooltip.style.top = `${clientY + 12}px`;
    this.tooltip.style.left = `${clientX + 12}px`;
  }

  hideTooltip() {
    this.tooltip?.classList.add('hidden');
  }

  showContextMenu(event, trip, targetEl) {
    if (!this.contextMenu) return;
    this.contextTrip = trip;
    this.contextMenu.dataset.tripId = trip.id;
    this.contextMenu.style.visibility = 'hidden';
    this.contextMenu.classList.remove('hidden');

    const menuWidth = this.contextMenu.offsetWidth || 200;
    const menuHeight = this.contextMenu.offsetHeight || 96;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const anchorRect = targetEl?.getBoundingClientRect();

    let left = event.clientX;
    let top = event.clientY;

    if (anchorRect) {
      left = anchorRect.left + anchorRect.width / 2;
      top = anchorRect.top + anchorRect.height / 2;
    }

    if (left + menuWidth > viewportWidth) {
      left = viewportWidth - menuWidth - 12;
    }
    if (top + menuHeight > viewportHeight) {
      top = viewportHeight - menuHeight - 12;
    }

    this.contextMenu.style.left = `${left}px`;
    this.contextMenu.style.top = `${top}px`;
    this.contextMenu.style.visibility = 'visible';
  }

  hideContextMenu() {
    if (!this.contextMenu) return;
    this.contextMenu.classList.add('hidden');
    this.contextMenu.style.visibility = '';
    this.contextTrip = null;
  }

  isWithinRange(date, start, end) {
    const target = this.toLocalDate(date);
    const rangeStart = this.toLocalDate(start);
    const rangeEnd = this.toLocalDate(end);
    return target >= rangeStart && target <= rangeEnd;
  }

  toLocalDate(value) {
    if (!value) return null;
    if (value instanceof Date) {
      return new Date(value.getFullYear(), value.getMonth(), value.getDate());
    }
    const safeValue = String(value).includes('T') ? String(value).split('T')[0] : String(value);
    const [year, month, day] = safeValue.split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  formatISO(date) {
    if (!date) return '';
    const d = this.toLocalDate(date);
    return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'), String(d.getDate()).padStart(2, '0')].join('-');
  }

  formatDate(date) {
    return this.toLocalDate(date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  }
  addTripFromIntegration(trip) {
    this.trips.push(this.normalizeTrip(trip));
    this.render();
    this.persistTrips();
  }

  loadPersistedTrips() {
    if (!this.hasStorageSupport()) return null;
    try {
      const raw = window.localStorage.getItem(this.storageKey);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return null;
      return parsed.map((trip) => this.normalizeTrip(trip));
    } catch (error) {
      console.warn('Calendar storage load failed:', error);
      return null;
    }
  }

  persistTrips() {
    if (this.isSandbox || !this.hasStorageSupport()) return;
    try {
      const payload = this.trips.map((trip) => ({
        ...trip,
        startDate: this.formatISO(trip.startDate),
        endDate: this.formatISO(trip.endDate),
      }));
      window.localStorage.setItem(this.storageKey, JSON.stringify(payload));
    } catch (error) {
      console.warn('Calendar storage save failed:', error);
    }
  }

  hasStorageSupport() {
    try {
      return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
    } catch {
      return false;
    }
  }
}

let calendarAppInstance;

export const bootstrapCalendar = (options = {}) => {
  calendarAppInstance = new CalendarApp(options);
  window.calendarAppInstance = calendarAppInstance;
  return calendarAppInstance;
};

if (!window.CALENDAR_SKIP_AUTO_BOOTSTRAP) {
  window.addEventListener('DOMContentLoaded', () => {
    bootstrapCalendar();
  });
}

export const renderCalendar = () => calendarAppInstance?.render();
export const addTrip = (trip) => calendarAppInstance?.addTripFromIntegration(trip);
export const updateSidebar = () => calendarAppInstance?.updateSidebar();
export { CalendarApp };
