/* Timeline view controller — Phase 3.8 */
(function (global) {
    'use strict';

    const DAY_WIDTH = 28;
    const ROW_HEIGHT = 60;
    const SCROLL_STEP_DAYS = 14;

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function createTooltip() {
        return {
            node: null,
            isVisible: false,
            ensure(root) {
                if (this.node) {
                    return this.node;
                }
                if (!root) {
                    return null;
                }
                const tooltip = root.querySelector('#timeline-view-tooltip');
                if (!tooltip) {
                    return null;
                }
                this.node = tooltip;
                return this.node;
            },
            show(content, position, accent, root) {
                const tooltip = this.ensure(root);
                if (!tooltip) {
                    return;
                }
                tooltip.innerHTML = content;
                tooltip.style.setProperty('--timeline-tooltip-accent', accent || '#2563eb');
                tooltip.style.left = `${position.x}px`;
                tooltip.style.top = `${position.y}px`;
                tooltip.setAttribute('aria-hidden', 'false');
                tooltip.classList.add('is-visible');
                this.isVisible = true;
            },
            hide(root) {
                const tooltip = this.ensure(root);
                if (!tooltip) {
                    return;
                }
                tooltip.setAttribute('aria-hidden', 'true');
                tooltip.classList.remove('is-visible');
                this.isVisible = false;
            }
        };
    }

    function TimelineController(root) {
        this.root = root;
        if (!root) {
            return;
        }

        this.elements = {
            wrapper: root.querySelector('.timeline-board__body'),
            employees: root.querySelector('#timeline-view-employees'),
            months: root.querySelector('#timeline-view-months'),
            days: root.querySelector('#timeline-view-days'),
            todayMarker: root.querySelector('#timeline-view-today'),
            canvasWrapper: root.querySelector('.timeline-board__canvas-wrapper'),
            canvas: root.querySelector('#timeline-view-canvas'),
            empty: root.querySelector('#timeline-view-empty'),
            loading: root.querySelector('#timeline-view-loading')
        };

        this.tooltip = createTooltip();
        this.state = {
            dataset: null,
            isActive: false,
            scrollSyncing: false
        };

        if (this.elements.canvas) {
            this.elements.canvasRows = document.createElement('div');
            this.elements.canvasRows.className = 'timeline-board__rows';
            this.elements.canvasRows.setAttribute('role', 'presentation');
            this.elements.canvas.innerHTML = '';
            this.elements.canvas.appendChild(this.elements.canvasRows);
            this.elements.canvas.addEventListener('scroll', this.handleCanvasScroll.bind(this), { passive: true });
            this.elements.canvas.addEventListener('click', this.handleCanvasClick.bind(this));
            this.elements.canvas.addEventListener('mouseover', this.handleCanvasMouseOver.bind(this));
            this.elements.canvas.addEventListener('mouseout', this.handleCanvasMouseOut.bind(this));
        }

        if (this.elements.employees) {
            this.elements.employees.addEventListener('scroll', this.handleEmployeeScroll.bind(this), { passive: true });
            this.elements.employees.addEventListener('click', this.handleEmployeeClick.bind(this));
        }

        const actionButtons = root.querySelectorAll('[data-timeline-action]');
        actionButtons.forEach((button) => {
            button.addEventListener('click', this.handleActionClick.bind(this));
        });

        this.hideLoading();
        this.renderEmpty();
    }

    TimelineController.prototype.dispatch = function dispatch(eventName, detail = {}) {
        if (!this.root) {
            return;
        }
        const event = new CustomEvent(eventName, {
            detail,
            bubbles: true
        });
        this.root.dispatchEvent(event);
    };

    TimelineController.prototype.showLoading = function showLoading() {
        if (this.elements.loading) {
            this.elements.loading.hidden = false;
        }
    };

    TimelineController.prototype.hideLoading = function hideLoading() {
        if (this.elements.loading) {
            this.elements.loading.hidden = true;
        }
    };

    TimelineController.prototype.renderEmpty = function renderEmpty(message) {
        if (this.elements.empty) {
            this.elements.empty.hidden = false;
            const text = this.elements.empty.querySelector('p');
            if (text && message) {
                text.textContent = message;
            }
        }
        if (this.elements.employees) {
            this.elements.employees.innerHTML = '';
        }
        if (this.elements.canvasRows) {
            this.elements.canvasRows.innerHTML = '';
            this.elements.canvasRows.style.width = '100%';
        }
        if (this.elements.months) {
            this.elements.months.innerHTML = '';
        }
        if (this.elements.days) {
            this.elements.days.innerHTML = '';
        }
        if (this.elements.todayMarker) {
            this.elements.todayMarker.style.display = 'none';
        }
    };

    TimelineController.prototype.clearEmptyState = function clearEmptyState() {
        if (this.elements.empty) {
            this.elements.empty.hidden = true;
        }
    };

    TimelineController.prototype.sync = function sync(dataset) {
        this.state.dataset = dataset;
        if (!dataset || !dataset.range || !Array.isArray(dataset.employees)) {
            this.renderEmpty();
            return;
        }
        if (!dataset.employees.length) {
            this.renderEmpty('No trips scheduled in this window.');
            return;
        }
        this.hideLoading();
        this.clearEmptyState();
        this.render(dataset);
        if (this.state.isActive) {
            this.scrollToToday({ smooth: false });
        }
    };

    TimelineController.prototype.render = function render(dataset) {
        this.renderHeader(dataset);
        this.renderEmployees(dataset);
        this.renderRows(dataset);
        this.updateTodayMarker(dataset);
    };

    TimelineController.prototype.renderHeader = function renderHeader(dataset) {
        if (!this.elements.months || !this.elements.days) {
            return;
        }
        const dayWidth = dataset.dayWidth || DAY_WIDTH;
        this.elements.months.innerHTML = '';
        this.elements.days.innerHTML = '';
        if (!dataset.range || !Array.isArray(dataset.range.days) || !dataset.range.days.length) {
            return;
        }

        const monthsFragment = document.createDocumentFragment();
        const daysFragment = document.createDocumentFragment();
        let currentMonth = null;
        let currentCount = 0;

        dataset.range.days.forEach((day, index) => {
            if (!currentMonth) {
                currentMonth = day.monthLabel;
                currentCount = 0;
            }
            if (day.monthLabel !== currentMonth) {
                const monthCell = document.createElement('div');
                monthCell.className = 'timeline-month-cell';
                monthCell.style.width = `${currentCount * dayWidth}px`;
                monthCell.textContent = currentMonth;
                monthsFragment.appendChild(monthCell);
                currentMonth = day.monthLabel;
                currentCount = 0;
            }
            currentCount += 1;

            const dayCell = document.createElement('div');
            dayCell.className = 'timeline-day-cell';
            dayCell.style.width = `${dayWidth}px`;
            dayCell.textContent = String(day.day);
            if (day.isWeekend) {
                dayCell.classList.add('timeline-day-cell--weekend');
            }
            if (day.isMonthStart) {
                dayCell.classList.add('timeline-day-cell--month');
            }
            daysFragment.appendChild(dayCell);

            if (index === dataset.range.days.length - 1) {
                const monthCell = document.createElement('div');
                monthCell.className = 'timeline-month-cell';
                monthCell.style.width = `${currentCount * dayWidth}px`;
                monthCell.textContent = currentMonth;
                monthsFragment.appendChild(monthCell);
            }
        });

        this.elements.months.appendChild(monthsFragment);
        this.elements.days.appendChild(daysFragment);
        const totalWidth = dataset.range.days.length * dayWidth;
        this.elements.months.style.width = `${totalWidth}px`;
        this.elements.days.style.width = `${totalWidth}px`;
    };

    TimelineController.prototype.renderEmployees = function renderEmployees(dataset) {
        if (!this.elements.employees) {
            return;
        }
        this.elements.employees.innerHTML = '';
        const fragment = document.createDocumentFragment();
        dataset.employees.forEach((employee) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'timeline-employee';
            button.dataset.timelineEmployee = String(employee.id);
            button.setAttribute('role', 'option');
            button.innerHTML = `
                <span class="timeline-employee__name">${employee.name}</span>
                <span class="timeline-employee__status timeline-employee__status--${employee.riskLevel || 'safe'}"></span>
            `;
            fragment.appendChild(button);
        });
        this.elements.employees.appendChild(fragment);
        this.elements.employees.scrollTop = this.elements.canvas ? this.elements.canvas.scrollTop : 0;
    };

    TimelineController.prototype.renderRows = function renderRows(dataset) {
        if (!this.elements.canvasRows) {
            return;
        }
        const dayWidth = dataset.dayWidth || DAY_WIDTH;
        const totalWidth = dataset.range.days.length * dayWidth;
        this.elements.canvasRows.innerHTML = '';
        this.elements.canvasRows.style.width = `${totalWidth}px`;

        const fragment = document.createDocumentFragment();
        dataset.employees.forEach((employee) => {
            const row = document.createElement('div');
            row.className = 'timeline-row';
            row.style.height = `${ROW_HEIGHT}px`;
            row.dataset.timelineEmployee = String(employee.id);

            const lane = document.createElement('div');
            lane.className = 'timeline-row__lane';
            lane.style.width = `${totalWidth}px`;
            lane.style.height = `${ROW_HEIGHT}px`;

            if (Array.isArray(employee.trips)) {
                employee.trips.forEach((trip) => {
                    const bar = document.createElement('div');
                    bar.className = `timeline-trip timeline-trip--${trip.status || 'safe'}`;
                    bar.style.left = `${trip.offsetDays * dayWidth}px`;
                    bar.style.width = `${Math.max(dayWidth * trip.durationDays, 6)}px`;
                    bar.dataset.tripId = String(trip.id);
                    bar.dataset.employeeId = String(employee.id);
                    bar.dataset.employeeName = employee.name;
                    bar.dataset.country = trip.country || 'Trip';
                    bar.dataset.range = trip.tooltip || '';
                    bar.dataset.status = trip.status || 'safe';
                    bar.dataset.days = String(trip.daysUsed || trip.durationDays || 0);
                    bar.style.setProperty('--timeline-trip-color', trip.color || '#2563eb');
                    bar.textContent = trip.country || 'Trip';
                    lane.appendChild(bar);
                });
            }

            row.appendChild(lane);
            fragment.appendChild(row);
        });

        this.elements.canvasRows.appendChild(fragment);
        this.tooltip.hide(this.root);
    };

    TimelineController.prototype.updateTodayMarker = function updateTodayMarker(dataset) {
        if (!this.elements.todayMarker || !dataset || !dataset.range || !Array.isArray(dataset.range.days)) {
            return;
        }
        const dayWidth = dataset.dayWidth || DAY_WIDTH;
        const index = dataset.range.days.findIndex((day) => day.iso === dataset.today);
        if (index === -1) {
            this.elements.todayMarker.style.display = 'none';
            return;
        }
        const height = this.elements.canvasRows ? this.elements.canvasRows.offsetHeight : 0;
        this.elements.todayMarker.style.display = 'block';
        this.elements.todayMarker.style.height = `${height}px`;
        const offset = (index + 0.5) * dayWidth;
        this.elements.todayMarker.style.transform = `translateX(${offset}px)`;
    };

    TimelineController.prototype.handleCanvasScroll = function handleCanvasScroll() {
        if (this.state.scrollSyncing) {
            return;
        }
        this.state.scrollSyncing = true;
        if (this.elements.employees) {
            this.elements.employees.scrollTop = this.elements.canvas.scrollTop;
        }
        const offset = this.elements.canvas.scrollLeft;
        if (this.elements.months) {
            this.elements.months.style.transform = `translateX(${-offset}px)`;
        }
        if (this.elements.days) {
            this.elements.days.style.transform = `translateX(${-offset}px)`;
        }
        this.state.scrollSyncing = false;
    };

    TimelineController.prototype.handleEmployeeScroll = function handleEmployeeScroll() {
        if (this.state.scrollSyncing) {
            return;
        }
        this.state.scrollSyncing = true;
        if (this.elements.canvas) {
            this.elements.canvas.scrollTop = this.elements.employees.scrollTop;
        }
        this.state.scrollSyncing = false;
    };

    TimelineController.prototype.handleCanvasClick = function handleCanvasClick(event) {
        const bar = event.target.closest('.timeline-trip');
        if (!bar) {
            return;
        }
        const tripId = Number.parseInt(bar.dataset.tripId, 10);
        if (!Number.isFinite(tripId)) {
            return;
        }
        this.dispatch('timeline:select-trip', { tripId });
    };

    TimelineController.prototype.handleEmployeeClick = function handleEmployeeClick(event) {
        const item = event.target.closest('[data-timeline-employee]');
        if (!item) {
            return;
        }
        const employeeId = Number.parseInt(item.dataset.timelineEmployee, 10);
        if (!Number.isFinite(employeeId)) {
            return;
        }
        this.dispatch('timeline:focus-employee', { employeeId });
    };

    TimelineController.prototype.handleCanvasMouseOver = function handleCanvasMouseOver(event) {
        const bar = event.target.closest('.timeline-trip');
        if (!bar) {
            return;
        }
        const rect = bar.getBoundingClientRect();
        const rootRect = this.root.getBoundingClientRect();
        const employee = bar.dataset.employeeName || '';
        const country = bar.dataset.country || 'Trip';
        const range = bar.dataset.range || '';
        const days = bar.dataset.days || '';
        const status = bar.dataset.status || 'safe';
        const accent = getComputedStyle(bar).getPropertyValue('--timeline-trip-color') || '#2563eb';
        const content = `
            <div class="timeline-tooltip__title">${country}</div>
            <div class="timeline-tooltip__meta">${employee}</div>
            ${range ? `<div class="timeline-tooltip__meta">${range}</div>` : ''}
            ${days ? `<div class="timeline-tooltip__meta">Usage: ${days} days</div>` : ''}
            <div class="timeline-tooltip__status timeline-tooltip__status--${status}">${status}</div>
        `;
        const position = {
            x: rect.left - rootRect.left + rect.width / 2,
            y: rect.top - rootRect.top - 12
        };
        this.tooltip.show(content, position, accent.trim(), this.root);
    };

    TimelineController.prototype.handleCanvasMouseOut = function handleCanvasMouseOut(event) {
        const related = event.relatedTarget;
        if (related && related.closest && related.closest('.timeline-trip')) {
            return;
        }
        this.tooltip.hide(this.root);
    };

    TimelineController.prototype.handleActionClick = function handleActionClick(event) {
        const action = event.currentTarget.dataset.timelineAction;
        switch (action) {
            case 'jump-today':
                this.scrollToToday({ smooth: true });
                break;
            case 'prev':
                this.scrollByDays(-SCROLL_STEP_DAYS);
                break;
            case 'next':
                this.scrollByDays(SCROLL_STEP_DAYS);
                break;
            default:
                break;
        }
    };

    TimelineController.prototype.scrollToToday = function scrollToToday(options = {}) {
        if (!this.elements.canvas || !this.state.dataset || !this.state.dataset.range) {
            return;
        }
        const dayWidth = this.state.dataset.dayWidth || DAY_WIDTH;
        const index = this.state.dataset.range.days.findIndex((day) => day.iso === this.state.dataset.today);
        if (index === -1) {
            return;
        }
        const canvasWidth = this.elements.canvas.clientWidth;
        const targetLeft = clamp((index * dayWidth) - (canvasWidth / 2) + (dayWidth / 2), 0, this.elements.canvas.scrollWidth);
        this.elements.canvas.scrollTo({
            left: targetLeft,
            behavior: options.smooth ? 'smooth' : 'auto'
        });
    };

    TimelineController.prototype.scrollByDays = function scrollByDays(days) {
        if (!this.elements.canvas || !Number.isFinite(days)) {
            return;
        }
        const dayWidth = this.state.dataset && this.state.dataset.dayWidth ? this.state.dataset.dayWidth : DAY_WIDTH;
        const delta = days * dayWidth;
        const target = clamp(this.elements.canvas.scrollLeft + delta, 0, this.elements.canvas.scrollWidth);
        this.elements.canvas.scrollTo({ left: target, behavior: 'smooth' });
    };

    TimelineController.prototype.activate = function activate() {
        this.state.isActive = true;
        this.scrollToToday({ smooth: true });
    };

    function initTimeline() {
        const root = document.getElementById('timeline-view');
        if (!root) {
            return null;
        }
        return new TimelineController(root);
    }

    let controller = null;
    let pendingDataset = null;
    let pendingOptions = null;

    const TimelineView = {
        init(root) {
            if (!controller) {
                controller = new TimelineController(root);
                if (pendingDataset !== null) {
                    controller.sync(pendingDataset, pendingOptions || {});
                    pendingDataset = null;
                    pendingOptions = null;
                }
            }
            return controller;
        },
        sync(dataset, options = {}) {
            if (!controller) {
                pendingDataset = dataset;
                pendingOptions = options;
                controller = initTimeline();
                if (!controller) {
                    return;
                }
            }
            controller.sync(dataset, options);
        },
        activate() {
            if (!controller) {
                controller = initTimeline();
            }
            if (controller) {
                controller.activate();
            }
        }
    };

    global.TimelineView = TimelineView;

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                if (!controller) {
                    controller = initTimeline();
                    if (controller && pendingDataset !== null) {
                        controller.sync(pendingDataset, pendingOptions || {});
                        pendingDataset = null;
                        pendingOptions = null;
                    }
                }
            });
        } else {
            controller = initTimeline();
            if (controller && pendingDataset !== null) {
                controller.sync(pendingDataset, pendingOptions || {});
                pendingDataset = null;
                pendingOptions = null;
            }
        }
    }
})(typeof window !== 'undefined' ? window : globalThis);
