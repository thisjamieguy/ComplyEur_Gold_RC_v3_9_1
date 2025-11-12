const clampHistory = (history) => history.slice(-6);

export class DebugOverlay {
  constructor({ hudEl, overlayEl }) {
    this.hudEl = hudEl;
    this.overlayEl = overlayEl;
    this.enabled = false;
    this.history = [];

    if (this.overlayEl) {
      this.calendarRectEl = this.createOutline('calendar-outline');
      this.proxyRectEl = this.createOutline('proxy-outline');
      this.snapRectEl = this.createOutline('snap-outline');
    }
  }

  createOutline(className) {
    const el = document.createElement('div');
    el.className = `debug-outline ${className}`;
    el.hidden = true;
    this.overlayEl.appendChild(el);
    return el;
  }

  setEnabled(flag) {
    this.enabled = Boolean(flag);
    if (this.hudEl) {
      this.hudEl.classList.toggle('hidden', !this.enabled);
      if (!this.enabled) {
        this.hudEl.textContent = '';
      }
    }
    if (!this.enabled) {
      this.hideOutline(this.calendarRectEl);
      this.hideOutline(this.proxyRectEl);
      this.hideOutline(this.snapRectEl);
    }
  }

  toggle() {
    this.setEnabled(!this.enabled);
  }

  updateInfo(payload) {
    if (!this.enabled || !this.hudEl) return;
    if (!payload) {
      this.hudEl.innerHTML = '<strong>HUD</strong>: idle';
      return;
    }
    const { clientX, startCellIndex, currentCellIndex, deltaDays, nextStartDate, nextEndDate, state } = payload;
    const startISO = nextStartDate?.toISOString?.().slice(0, 10) ?? 'n/a';
    const endISO = nextEndDate?.toISOString?.().slice(0, 10) ?? 'n/a';
    const historyMarkup = this.history
      .map((entry) => `<li>${entry.ts} · ${entry.prev} → ${entry.next}</li>`)
      .join('');
    this.hudEl.innerHTML = `
      <div><strong>State</strong>: ${state}</div>
      <div>clientX: ${clientX?.toFixed ? clientX.toFixed(2) : 'n/a'}</div>
      <div>start idx: ${startCellIndex ?? '–'} → current idx: ${currentCellIndex ?? '–'}</div>
      <div>delta days: ${deltaDays ?? 0}</div>
      <div>range: ${startISO} → ${endISO}</div>
      ${historyMarkup ? `<ol class="hud-history">${historyMarkup}</ol>` : ''}
    `;
  }

  updateRects({ calendarRect, proxyRect, snapRect }) {
    if (!this.enabled || !this.overlayEl) return;
    this.positionOutline(this.calendarRectEl, calendarRect);
    this.positionOutline(this.proxyRectEl, proxyRect);
    this.positionOutline(this.snapRectEl, snapRect);
  }

  positionOutline(target, rect) {
    if (!target) return;
    if (!rect) {
      this.hideOutline(target);
      return;
    }
    const overlayRect = this.overlayEl.getBoundingClientRect();
    target.hidden = false;
    target.style.transform = `translate(${rect.left - overlayRect.left}px, ${
      rect.top - overlayRect.top
    }px)`;
    target.style.width = `${rect.width}px`;
    target.style.height = `${rect.height}px`;
  }

  hideOutline(target) {
    if (target) {
      target.hidden = true;
    }
  }

  logTransition(prev, next, meta = {}) {
    const ts = new Date().toISOString().split('T')[1].slice(0, 12);
    this.history = clampHistory([...this.history, { prev, next, ts }]);
    // eslint-disable-next-line no-console
    console.debug('[InteractionManager]', `${prev} → ${next}`, meta);
    if (this.enabled) {
      this.updateInfo(
        meta.previewPayload || {
          state: next,
          clientX: meta.currentClientX ?? null,
          startCellIndex: meta.startCellIndex ?? null,
          currentCellIndex: meta.currentCellIndex ?? null,
          deltaDays: 0,
          nextStartDate: null,
          nextEndDate: null,
        }
      );
    }
  }
}
