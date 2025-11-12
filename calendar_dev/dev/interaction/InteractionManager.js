const STATES = {
  idle: 'idle',
  dragging: 'dragging',
  resizing_left: 'resizing_left',
  resizing_right: 'resizing_right',
  committing: 'committing',
};

const DEFAULT_DATA = {
  activeTripId: null,
  startClientX: null,
  startClientY: null,
  currentClientX: null,
  currentClientY: null,
  baseRect: null,
  startCellIndex: null,
  currentCellIndex: null,
  startTrip: null,
  snapWidthPx: 0,
  resizeEdge: null,
};

const noop = () => {};

export class InteractionManager {
  constructor({
    getCalendarRect,
    clientXToCellIndex,
    commitTripUpdate,
    onPreview = noop,
    addDays,
    onStateChange = noop,
  }) {
    this.getCalendarRect = getCalendarRect;
    this.clientXToCellIndex = clientXToCellIndex;
    this.commitTripUpdate = commitTripUpdate;
    this.onPreview = onPreview;
    this.addDays = addDays;
    this.onStateChange = onStateChange;

    this.state = STATES.idle;
    this.data = { ...DEFAULT_DATA };
    this.pendingFrame = null;
    this.pendingPoint = null;
  }

  beginDrag(tripId, clientX, meta = {}) {
    this.startInteraction({
      tripId,
      clientX,
      clientY: meta.startClientY ?? null,
      meta,
      nextState: STATES.dragging,
      resizeEdge: null,
      anchorIndex: meta?.startTrip?.startCellIndex ?? null,
    });
  }

  beginResize(tripId, edge, clientX, meta = {}) {
    const nextState = edge === 'left' ? STATES.resizing_left : STATES.resizing_right;
    const anchorIndex =
      edge === 'left' ? meta?.startTrip?.startCellIndex : meta?.startTrip?.endCellIndex;
    this.startInteraction({
      tripId,
      clientX,
      clientY: meta.startClientY ?? null,
      meta,
      nextState,
      resizeEdge: edge,
      anchorIndex,
    });
  }

  startInteraction({ tripId, clientX, clientY, meta, nextState, resizeEdge, anchorIndex }) {
    if (!tripId || typeof clientX !== 'number' || !meta?.startTrip || !this.addDays) {
      return;
    }
    this.cancel(true);

    this.data = {
      activeTripId: tripId,
      startClientX: clientX,
      startClientY: clientY ?? null,
      currentClientX: clientX,
      currentClientY: clientY ?? null,
      baseRect: meta.baseRect || this.getCalendarRect(),
      startCellIndex: anchorIndex,
      currentCellIndex: anchorIndex,
      startTrip: meta.startTrip,
      snapWidthPx: meta.snapWidthPx || 0,
      resizeEdge,
    };

    this.pendingPoint = null;
    this.setState(nextState);
    this.emitPreview();
  }

  updatePointer(clientX, clientY) {
    if (this.state === STATES.idle || this.state === STATES.committing) {
      return;
    }
    if (typeof clientX !== 'number') return;
    this.pendingPoint = { clientX, clientY };
    if (this.pendingFrame) return;
    this.pendingFrame = requestAnimationFrame(() => this.flushPointer());
  }

  flushPointer() {
    this.pendingFrame = null;
    if (!this.pendingPoint) return;
    const { clientX, clientY } = this.pendingPoint;
    this.pendingPoint = null;
    const nextIndex = this.clientXToCellIndex(clientX, clientY);
    if (nextIndex == null) return;
    this.data.currentClientX = clientX;
    this.data.currentClientY = clientY ?? null;
    this.data.currentCellIndex = nextIndex;
    this.emitPreview();
  }

  emitPreview() {
    if (!this.data.startTrip) return;
    const preview = this.buildPreview();
    this.onPreview(preview);
  }

  buildPreview() {
    const { startTrip, currentCellIndex, startCellIndex } = this.data;
    if (
      !startTrip ||
      startCellIndex == null ||
      currentCellIndex == null ||
      !Number.isFinite(currentCellIndex)
    ) {
      return null;
    }

    let nextStartIndex = startTrip.startCellIndex;
    let nextEndIndex = startTrip.endCellIndex;

    const payload = {
      state: this.state,
      tripId: this.data.activeTripId,
      startCellIndex,
      currentCellIndex,
      startClientX: this.data.startClientX,
      currentClientX: this.data.currentClientX,
      startClientY: this.data.startClientY,
      currentClientY: this.data.currentClientY,
      snapWidthPx: this.data.snapWidthPx,
      resizeEdge: this.data.resizeEdge,
      startDate: startTrip.startDate,
      endDate: startTrip.endDate,
      deltaDays: 0,
      nextStartDate: startTrip.startDate,
      nextEndDate: startTrip.endDate,
    };

    if (!this.addDays) {
      return payload;
    }

    if (this.state === STATES.dragging) {
      const delta = currentCellIndex - startCellIndex;
      payload.deltaDays = delta;
      payload.nextStartDate = this.addDays(startTrip.startDate, delta);
      payload.nextEndDate = this.addDays(startTrip.endDate, delta);
      nextStartIndex = startTrip.startCellIndex + delta;
      nextEndIndex = startTrip.endCellIndex + delta;
    } else if (this.state === STATES.resizing_left) {
      const constrainedIndex = Math.min(currentCellIndex, startTrip.endCellIndex);
      const delta = constrainedIndex - startTrip.startCellIndex;
      payload.deltaDays = delta;
      payload.nextStartDate = this.addDays(startTrip.startDate, delta);
      payload.nextEndDate = startTrip.endDate;
      nextStartIndex = startTrip.startCellIndex + delta;
    } else if (this.state === STATES.resizing_right) {
      const targetIndex = Math.max(currentCellIndex, startTrip.startCellIndex);
      const delta = targetIndex - startTrip.endCellIndex;
      payload.deltaDays = delta;
      payload.nextStartDate = startTrip.startDate;
      payload.nextEndDate = this.addDays(startTrip.endDate, delta);
      nextEndIndex = startTrip.endCellIndex + delta;
    }

    payload.hasDelta =
      payload.nextStartDate.getTime() !== startTrip.startDate.getTime() ||
      payload.nextEndDate.getTime() !== startTrip.endDate.getTime();

    payload.range = {
      startCellIndex: Math.min(nextStartIndex, nextEndIndex),
      endCellIndex: Math.max(nextStartIndex, nextEndIndex),
    };

    return payload;
  }

  commit() {
    if (this.state === STATES.idle) return null;
    const preview = this.buildPreview();
    this.setState(STATES.committing);
    if (preview?.hasDelta && this.commitTripUpdate) {
      this.commitTripUpdate(this.data.activeTripId, preview.nextStartDate, preview.nextEndDate);
    }
    this.onPreview(null);
    this.resetInternal();
    return preview;
  }

  cancel(silent = false) {
    if (!silent) {
      this.onPreview(null);
    }
    this.resetInternal();
  }

  resetInternal() {
    if (this.pendingFrame) {
      cancelAnimationFrame(this.pendingFrame);
      this.pendingFrame = null;
    }
    this.pendingPoint = null;
    this.data = { ...DEFAULT_DATA };
    this.setState(STATES.idle);
  }

  setState(nextState) {
    if (this.state === nextState) return;
    const prev = this.state;
    this.state = nextState;
    this.onStateChange(nextState, prev, {
      tripId: this.data.activeTripId,
      startCellIndex: this.data.startCellIndex,
      currentCellIndex: this.data.currentCellIndex,
    });
  }
}

export const INTERACTION_STATES = STATES;
