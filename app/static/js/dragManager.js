// Phase 3.6.1 — Calendar Drag Manager — Verified ✅
(function (global) {
    'use strict';

    const DAY_IN_MS = 86_400_000;

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function startOfDay(value) {
        if (!(value instanceof Date)) {
            return null;
        }
        const copy = new Date(value.getTime());
        copy.setHours(0, 0, 0, 0);
        return copy;
    }

    function toDate(value) {
        if (value instanceof Date) {
            return new Date(value.getTime());
        }
        if (typeof value === 'string') {
            const parsed = new Date(value);
            if (!Number.isNaN(parsed.getTime())) {
                return startOfDay(parsed);
            }
        }
        if (typeof value === 'number') {
            const fromNumber = new Date(value);
            if (!Number.isNaN(fromNumber.getTime())) {
                return startOfDay(fromNumber);
            }
        }
        return null;
    }

    function addDays(date, days) {
        const safeDate = startOfDay(date);
        if (!safeDate) {
            return null;
        }
        return new Date(safeDate.getTime() + (days * DAY_IN_MS));
    }

    function diffInDays(start, end) {
        const safeStart = startOfDay(start);
        const safeEnd = startOfDay(end);
        if (!safeStart || !safeEnd) {
            return 0;
        }
        return Math.round((safeEnd.getTime() - safeStart.getTime()) / DAY_IN_MS);
    }

    function ensureLabelElement(rootClass) {
        let label = document.querySelector(`.${rootClass}`);
        if (!label) {
            label = document.createElement('div');
            label.className = rootClass;
            label.setAttribute('role', 'status');
            label.setAttribute('aria-live', 'polite');
            label.style.display = 'none';
            document.body.appendChild(label);
        }
        return label;
    }

    class DragManager {
        constructor(options = {}) {
            this.options = options;
            this.dayWidth = Number.isFinite(options.dayWidth) ? options.dayWidth : 28;
            this.grid = options.grid || null;
            this.tripMeta = new WeakMap();
            this.boundTrips = new WeakSet();
            this.rows = new WeakSet();
            this.dragging = null;
            this.labelClass = 'calendar-drag-label';
            this.labelEl = null;

            this.handleDragStart = this.handleDragStart.bind(this);
            this.handleDragEnd = this.handleDragEnd.bind(this);
            this.handleDragOver = this.handleDragOver.bind(this);
            this.handleDrop = this.handleDrop.bind(this);
            this.handleDragLeave = this.handleDragLeave.bind(this);
        }

        registerTrip(element, metadata = {}) {
            if (!element) {
                return;
            }

            const meta = this.normaliseMetadata(metadata);
            this.tripMeta.set(element, meta);

            if (meta.locked) {
                element.setAttribute('draggable', 'false');
                element.setAttribute('aria-grabbed', 'false');
                return;
            }

            element.setAttribute('draggable', 'true');
            element.setAttribute('aria-grabbed', 'false');

            if (!this.boundTrips.has(element)) {
                element.addEventListener('dragstart', this.handleDragStart);
                element.addEventListener('dragend', this.handleDragEnd);
                this.boundTrips.add(element);
            }
        }

        normaliseMetadata(metadata) {
            const start = toDate(metadata.start);
            const end = toDate(metadata.end) || start;
            const durationDays = Math.max(1, Number.isFinite(metadata.durationDays) ? Math.round(metadata.durationDays) : diffInDays(start, end) + 1);
            return {
                id: metadata.id,
                employeeId: metadata.employeeId,
                start,
                end,
                durationDays,
                locked: Boolean(metadata.locked)
            };
        }

        registerRow(layer) {
            if (!layer || this.rows.has(layer)) {
                return layer;
            }
            layer.addEventListener('dragover', this.handleDragOver);
            layer.addEventListener('drop', this.handleDrop);
            layer.addEventListener('dragleave', this.handleDragLeave);
            this.rows.add(layer);
            return layer;
        }

        getRangeInfo() {
            if (typeof this.options.getRange !== 'function') {
                return { start: null, totalDays: 0 };
            }
            const range = this.options.getRange();
            if (!range || !(range.start instanceof Date) || !(range.end instanceof Date)) {
                return { start: null, totalDays: 0 };
            }
            const safeStart = startOfDay(range.start);
            const safeEnd = startOfDay(range.end);
            if (!safeStart || !safeEnd) {
                return { start: null, totalDays: 0 };
            }
            const totalDays = diffInDays(safeStart, safeEnd) + 1;
            return { start: safeStart, totalDays: Math.max(totalDays, 0) };
        }

        handleDragStart(event) {
            const element = event.currentTarget;
            const meta = this.tripMeta.get(element);
            if (!element || !meta || meta.locked) {
                if (event.dataTransfer) {
                    event.dataTransfer.dropEffect = 'none';
                }
                event.preventDefault();
                return;
            }

            const layer = this.registerRow(element.parentElement);
            const row = element.closest('.calendar-grid-row');
            if (!layer || !row) {
                event.preventDefault();
                return;
            }

            const rangeInfo = this.getRangeInfo();
            if (!rangeInfo.start) {
                event.preventDefault();
                return;
            }

            const elementRect = element.getBoundingClientRect();
            const pointerOffsetX = typeof event.offsetX === 'number'
                ? event.offsetX
                : event.clientX - elementRect.left;
            const pointerOffsetY = typeof event.offsetY === 'number'
                ? event.offsetY
                : event.clientY - elementRect.top;
            const anchorOffsetDays = pointerOffsetX / this.dayWidth;
            const originalStartIndex = Math.max(0, diffInDays(rangeInfo.start, meta.start));

            const placeholder = document.createElement('div');
            placeholder.className = 'calendar-trip-placeholder';
            placeholder.style.position = 'absolute';
            placeholder.style.left = element.style.left || '0px';
            placeholder.style.top = element.style.top || '0px';
            placeholder.style.width = element.style.width || `${meta.durationDays * this.dayWidth}px`;
            placeholder.style.height = element.style.height || `${element.offsetHeight}px`;
            placeholder.style.pointerEvents = 'none';
            layer.appendChild(placeholder);

            element.classList.add('calendar-trip--dragging');
            element.setAttribute('aria-grabbed', 'true');
            row.setAttribute('aria-dropeffect', 'move');

            this.dragging = {
                element,
                meta,
                layer,
                row,
                pointerOffsetX,
                pointerOffsetY,
                anchorOffsetDays,
                originalLeft: parseFloat(element.style.left) || 0,
                originalStart: meta.start,
                originalEnd: meta.end,
                originalIndex: originalStartIndex,
                placeholder,
                nextIndex: originalStartIndex,
                nextLeft: parseFloat(element.style.left) || 0,
                nextStart: meta.start,
                nextEnd: meta.end
            };

            if (event.dataTransfer) {
                event.dataTransfer.effectAllowed = 'move';
                event.dataTransfer.setData('text/plain', String(meta.id));
                try {
                    const dragImage = element.cloneNode(true);
                    dragImage.classList.add('calendar-trip--drag-image');
                    dragImage.style.position = 'absolute';
                    dragImage.style.top = '-9999px';
                    dragImage.style.left = '-9999px';
                    dragImage.style.pointerEvents = 'none';
                    document.body.appendChild(dragImage);
                    event.dataTransfer.setDragImage(dragImage, pointerOffsetX, pointerOffsetY);
                    window.setTimeout(() => {
                        if (dragImage && dragImage.parentNode) {
                            dragImage.parentNode.removeChild(dragImage);
                        }
                    }, 0);
                } catch (error) {
                    // Some browsers may throw if setDragImage is unsupported; ignore gracefully.
                }
            }
        }

        handleDragOver(event) {
            if (!this.dragging) {
                return;
            }
            if (event.currentTarget !== this.dragging.layer) {
                return;
            }

            const meta = this.dragging.meta;
            const rangeInfo = this.getRangeInfo();
            if (!rangeInfo.start) {
                return;
            }

            if (event.cancelable) {
                event.preventDefault();
            }
            if (event.dataTransfer) {
                event.dataTransfer.dropEffect = 'move';
            }

            const layerRect = this.dragging.layer.getBoundingClientRect();
            const relativeX = event.clientX - layerRect.left;
            const rawIndex = (relativeX / this.dayWidth) - this.dragging.anchorOffsetDays;
            const maxIndex = Math.max(0, rangeInfo.totalDays - meta.durationDays);
            const snappedIndex = clamp(Math.round(rawIndex), 0, maxIndex);
            const snappedLeft = snappedIndex * this.dayWidth;

            const startDate = addDays(rangeInfo.start, snappedIndex);
            const endDate = addDays(startDate, meta.durationDays - 1);

            this.dragging.nextIndex = snappedIndex;
            this.dragging.nextLeft = snappedLeft;
            this.dragging.nextStart = startDate || meta.start;
            this.dragging.nextEnd = endDate || meta.end;

            if (this.dragging.placeholder) {
                this.dragging.placeholder.style.left = `${snappedLeft}px`;
                this.dragging.placeholder.style.width = `${meta.durationDays * this.dayWidth}px`;
                this.dragging.placeholder.style.top = this.dragging.element.style.top || '0px';
            }

            this.updateLabel(event.clientX, event.clientY, this.dragging.nextStart, this.dragging.nextEnd);
        }

        handleDrop(event) {
            if (!this.dragging) {
                return;
            }

            if (event.cancelable) {
                event.preventDefault();
            }

            const dragState = this.dragging;
            const meta = dragState.meta;
            const rangeInfo = this.getRangeInfo();
            const dropRow = event.currentTarget ? event.currentTarget.closest('.calendar-grid-row') : null;

            const dropEmployeeId = dropRow ? dropRow.getAttribute('data-employee-id') : null;
            const metaEmployeeId = meta.employeeId != null ? String(meta.employeeId) : null;
            if (dropEmployeeId !== null && metaEmployeeId !== null && dropEmployeeId !== metaEmployeeId) {
                this.cleanupDrag();
                return;
            }

            const nextIndex = Number.isFinite(dragState.nextIndex) ? dragState.nextIndex : dragState.originalIndex;
            const nextStart = dragState.nextStart || addDays(rangeInfo.start, nextIndex);
            const nextEnd = dragState.nextEnd || addDays(nextStart, meta.durationDays - 1);
            const nextLeft = Number.isFinite(dragState.nextLeft) ? dragState.nextLeft : dragState.originalLeft;

            const payload = {
                tripId: meta.id,
                employeeId: meta.employeeId,
                element: dragState.element,
                nextStart,
                nextEnd,
                nextIndex,
                nextLeft,
                originalStart: dragState.originalStart,
                originalEnd: dragState.originalEnd,
                originalIndex: dragState.originalIndex,
                originalLeft: dragState.originalLeft,
                revert: () => {
                    if (!dragState || !dragState.element) {
                        return;
                    }
                    dragState.element.style.left = `${dragState.originalLeft}px`;
                    dragState.element.setAttribute('aria-grabbed', 'false');
                }
            };

            this.cleanupDrag();

            if (typeof this.options.onDrop === 'function') {
                Promise.resolve()
                    .then(() => this.options.onDrop(payload))
                    .catch((error) => {
                        console.error('Drag drop handler rejected', error);
                        if (typeof payload.revert === 'function') {
                            payload.revert();
                        }
                    });
            }
        }

        handleDragLeave(event) {
            if (!this.dragging || event.currentTarget !== this.dragging.layer) {
                return;
            }
            this.hideLabel();
        }

        handleDragEnd() {
            this.cleanupDrag();
        }

        updateLabel(clientX, clientY, startDate, endDate) {
            if (!startDate || !endDate) {
                this.hideLabel();
                return;
            }

            if (!this.labelEl) {
                this.labelEl = ensureLabelElement(this.labelClass);
            }

            let labelText = '';
            if (typeof this.options.formatLabel === 'function') {
                labelText = this.options.formatLabel(startDate, endDate) || '';
            }
            if (!labelText) {
                labelText = `${startDate.toISOString().split('T')[0]} → ${endDate.toISOString().split('T')[0]}`;
            }

            const offsetX = 16;
            const offsetY = 40;
            const x = Math.max(0, clientX + offsetX);
            const y = Math.max(0, clientY - offsetY);

            this.labelEl.textContent = labelText;
            this.labelEl.style.display = 'block';
            this.labelEl.style.left = `${x}px`;
            this.labelEl.style.top = `${y}px`;
        }

        hideLabel() {
            if (this.labelEl) {
                this.labelEl.style.display = 'none';
            }
        }

        cleanupDrag() {
            if (!this.dragging) {
                return;
            }

            const { element, row, placeholder } = this.dragging;
            if (element) {
                element.classList.remove('calendar-trip--dragging');
                element.setAttribute('aria-grabbed', 'false');
            }
            if (row) {
                row.removeAttribute('aria-dropeffect');
            }
            if (placeholder && placeholder.parentNode) {
                placeholder.parentNode.removeChild(placeholder);
            }
            this.hideLabel();
            this.dragging = null;
        }
    }

    global.CalendarDragManager = DragManager;
})(typeof window !== 'undefined' ? window : globalThis);



