"use strict";

const assert = require("assert");
const path = require("path");

const { CalendarUtils } = require(path.join(__dirname, "../../app/static/js/calendar.js"));

function testParseDate() {
    const date = CalendarUtils.parseDate("2024-02-15");
    assert(date instanceof Date, "parseDate should return a Date instance");
    assert.strictEqual(date.getUTCFullYear(), 2024, "Year should be 2024");
    assert.strictEqual(date.getUTCMonth(), 1, "Month should be February (index 1)");
    assert.strictEqual(date.getUTCDate(), 15, "Day should be 15");
}

function testRangeDays() {
    const start = new Date(Date.UTC(2024, 0, 1));
    const end = new Date(Date.UTC(2024, 0, 31));
    const days = CalendarUtils.calculateRangeDays({ start, end });
    assert.strictEqual(days.length, 31, "January 2024 should yield 31 days");
    assert(days[0].isMonthStart, "First day should be a month start");
    const weekStarts = days.filter((day) => day.isWeekStart);
    assert(weekStarts.length >= 4, "Should identify each Monday as the start of a week");
}

function testCalendarConstants() {
    assert.strictEqual(CalendarUtils.LOOKBACK_DAYS, 180, "Lookback should be 180 days");
    assert.strictEqual(CalendarUtils.DEFAULT_FUTURE_WEEKS, 6, "Default future weeks should be 6");
    assert.strictEqual(CalendarUtils.MIN_FUTURE_WEEKS, 4, "Min future weeks should be 4");
    assert.strictEqual(CalendarUtils.MAX_FUTURE_WEEKS, 10, "Max future weeks should be 10");
}

function testTripStatusClassification() {
    const trips = [
        {
            id: 1,
            start: new Date(Date.UTC(2024, 0, 1)),
            end: new Date(Date.UTC(2024, 0, 20)) // 20 days => safe
        },
        {
            id: 2,
            start: new Date(Date.UTC(2024, 7, 1)),
            end: new Date(Date.UTC(2024, 9, 15)) // ~76 days => warning
        },
        {
            id: 3,
            start: new Date(Date.UTC(2025, 0, 1)),
            end: new Date(Date.UTC(2025, 3, 10)) // ~100 days => critical
        }
    ];

    const statuses = CalendarUtils.buildTripStatusIndex(
        trips,
        CalendarUtils.DEFAULT_WARNING_THRESHOLD,
        CalendarUtils.CRITICAL_THRESHOLD
    );
    assert.strictEqual(statuses.get(1).status, "safe", "Trip 1 should be safe");
    assert.strictEqual(statuses.get(2).status, "warning", "Trip 2 should be warning");
    assert.strictEqual(statuses.get(3).status, "critical", "Trip 3 should be critical");
    assert(statuses.get(2).daysUsed > CalendarUtils.DEFAULT_WARNING_THRESHOLD, "Warning trip should exceed safe threshold");
    assert(statuses.get(3).daysUsed >= CalendarUtils.CRITICAL_THRESHOLD, "Critical trip should meet or exceed 90-day threshold");
}

function testTripPlacement() {
    const range = {
        start: new Date(Date.UTC(2024, 0, 1)),
        end: new Date(Date.UTC(2024, 5, 30))
    };
    const trip = {
        start: new Date(Date.UTC(2023, 11, 20)),
        end: new Date(Date.UTC(2024, 0, 10))
    };
    const placement = CalendarUtils.calculateTripPlacement(range, trip);
    assert.strictEqual(placement.offsetDays, 0, "Trip should begin at the start of the range");
    assert.strictEqual(placement.durationDays, 10, "Trip should span 10 visible days within the range");
    assert.strictEqual(placement.clampedStart.getUTCDate(), 1, "Clamped start should match range start");
    assert.strictEqual(placement.clampedEnd.getUTCDate(), 10, "Clamped end should match visible end date");
}

function testFormattingHelpers() {
    const start = new Date(Date.UTC(2024, 0, 1));
    const end = new Date(Date.UTC(2024, 0, 10));
    const rangeLabel = CalendarUtils.formatDateRangeDisplay(start, end);
    const segments = rangeLabel.split("→").map((segment) => segment.trim());
    assert.strictEqual(segments.length, 2, "Range label should contain two date segments separated by an arrow");
    assert(segments[0].length > 0 && segments[1].length > 0, "Each segment should contain formatted date text");
    assert(rangeLabel.includes("2024"), "Range label should include the year for context");

    assert.strictEqual(CalendarUtils.formatDuration(1), "1 day", "Singular durations should be labelled correctly");
    assert.strictEqual(CalendarUtils.formatDuration(45), "45 days", "Plural durations should be labelled correctly");
    assert.strictEqual(CalendarUtils.formatDuration(3.2), "3 days", "Duration should round to nearest whole day");
    assert.strictEqual(CalendarUtils.normaliseStatusLabel("warning"), "Approaching 90-day limit", "Warning label should match spec");
}

function testPerformanceScaling() {
    const trips = [];
    for (let i = 0; i < 1000; i += 1) {
        const start = new Date(Date.UTC(2024, 0, 1 + (i * 2)));
        const end = new Date(Date.UTC(2024, 0, 2 + (i * 2)));
        trips.push({ id: i + 1, start, end });
    }
    const statuses = CalendarUtils.buildTripStatusIndex(trips, CalendarUtils.DEFAULT_WARNING_THRESHOLD, CalendarUtils.CRITICAL_THRESHOLD);
    assert.strictEqual(statuses.size, 1000, "All trips should be indexed");
}

function run() {
    testParseDate();
    testRangeDays();
    testCalendarConstants();
    testTripStatusClassification();
    testTripPlacement();
    testFormattingHelpers();
    testPerformanceScaling();
    console.log("✅ calendar.test.js passed (Calendar utilities)");
}

run();
