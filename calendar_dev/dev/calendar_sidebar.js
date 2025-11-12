export class CalendarSidebar {
  constructor(container) {
    this.container = container;
  }

  updateSidebar({ totalDays, nextTrip, riskPercent, upcomingTrips }) {
    if (!this.container) return;
    const riskMeta = this.getRiskMeta(totalDays);
    const nextTripMarkup = nextTrip
      ? `<strong>${nextTrip.employee}</strong> · ${nextTrip.country}<br>${this.formatDateRange(nextTrip)}`
      : 'No upcoming trips on the books.';

    const upcomingList = (upcomingTrips || [])
      .map(
        (trip) => `
          <li>
            <div class="trip-row">
              <strong>${trip.employee}</strong>
              <span>${trip.country}</span>
            </div>
            <small>${this.formatDateRange(trip)}</small>
          </li>`
      )
      .join('');

    this.container.innerHTML = `
      <div class="sidebar-card">
        <h3>Rolling 180 Days</h3>
        <div class="sidebar-value">${totalDays} days</div>
      </div>
      <div class="sidebar-card">
        <h3>Risk Indicator</h3>
        <p>${riskMeta.label}</p>
        <div class="risk-bar">
          <span style="width:${riskMeta.width}%;background:${riskMeta.color}"></span>
        </div>
      </div>
      <div class="sidebar-card">
        <h3>Next Trip</h3>
        <p>${nextTripMarkup}</p>
      </div>
      <div class="sidebar-card">
        <h3>Upcoming</h3>
        ${upcomingList ? `<ul class="trip-list">${upcomingList}</ul>` : '<p>Nothing else scheduled.</p>'}
      </div>
    `;
  }

  getRiskMeta(totalDays) {
    if (Number.isNaN(totalDays)) {
      return { label: 'No data', width: 0, color: '#d4d9e9' };
    }

    const ratio = Math.min(totalDays / 90, 1);
    let label = 'Clear';
    let color = '#3cb37a';

    if (totalDays >= 90) {
      label = 'Exceeded';
      color = '#ff5a5f';
    } else if (totalDays >= 60) {
      label = 'Watch';
      color = '#ff9f43';
    }

    return {
      label,
      width: ratio * 100,
      color,
    };
  }

  formatDateRange(trip) {
    const start = this.formatDate(trip.startDate || trip.start_date);
    const end = this.formatDate(trip.endDate || trip.end_date);
    return `${start} → ${end}`;
  }

  formatDate(value) {
    const d = typeof value === 'string' ? new Date(value) : value;
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  }
}
