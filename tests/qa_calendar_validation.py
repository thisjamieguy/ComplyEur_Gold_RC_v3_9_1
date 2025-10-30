"""
Comprehensive QA validation suite for the native JavaScript calendar (Phase 3.5.3).

This end-to-end test relies on the Python Playwright bindings and a running instance
of the EU Trip Tracker at http://127.0.0.1:5000 (or the URL supplied via
EUTRACKER_BASE_URL). It exercises rendering, interaction, accessibility, and basic
regression checks so regressions are caught before promoting to production.
"""

from __future__ import annotations

import os
import re
import time
import uuid
from datetime import date, timedelta
from typing import Dict, List

import pytest

# Ensure Playwright is available before loading heavy fixtures.
pytest.importorskip(
    "playwright.sync_api",
    reason="Playwright Python bindings are required for calendar QA validation.",
)

from playwright.sync_api import Browser, BrowserContext, Page, expect, sync_playwright  # type: ignore

BASE_URL = os.getenv("EUTRACKER_BASE_URL", "http://127.0.0.1:5000")
ADMIN_PASSWORD = os.getenv("EUTRACKER_ADMIN_PASSWORD", "admin123")
HEADLESS = os.getenv("EUTRACKER_HEADLESS", "1") != "0"
MAX_LOAD_MS = int(os.getenv("CALENDAR_LOAD_THRESHOLD_MS", "1000"))
VIEWPORT = {"width": 1440, "height": 900}

STATUS_COLORS = {
    "safe": "#15803d",
    "warning": "#c2410c",
    "critical": "#dc2626",
}

RGB_PATTERN = re.compile(r"rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)")


def _iso(day: date) -> str:
    return day.isoformat()


def _rgb_to_hex(value: str | None) -> str | None:
    if not value:
        return None
    match = RGB_PATTERN.search(value.strip())
    if not match:
        return value.strip()
    r, g, b = (int(channel) for channel in match.groups())
    return f"#{r:02x}{g:02x}{b:02x}"


def _relative_channel(component: float) -> float:
    component /= 255.0
    return component / 12.92 if component <= 0.03928 else ((component + 0.055) / 1.055) ** 2.4


def _contrast_ratio(hex_color: str, foreground: str = "#ffffff") -> float:
    def luminance(hex_code: str) -> float:
        hex_code = hex_code.lstrip("#")
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        r_lin = _relative_channel(r)
        g_lin = _relative_channel(g)
        b_lin = _relative_channel(b)
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    bg_l = luminance(hex_color)
    fg_l = luminance(foreground)
    brightest, darkest = max(bg_l, fg_l), min(bg_l, fg_l)
    return (brightest + 0.05) / (darkest + 0.05)


@pytest.fixture(scope="session")
def browser() -> Browser:
    with sync_playwright() as playwright:
        chromium = playwright.chromium
        browser = chromium.launch(headless=HEADLESS)
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser) -> BrowserContext:
    ctx = browser.new_context(base_url=BASE_URL, viewport=VIEWPORT, ignore_https_errors=True)
    ctx.set_default_timeout(10_000)
    try:
        response = ctx.request.get("/login")
        if response.status != 200:
            pytest.skip(
                f"Calendar QA requires the Flask app to be running at {BASE_URL} "
                f"(received HTTP {response.status})."
            )
    except Exception as exc:  # pragma: no cover - network guard
        pytest.skip(f"Calendar QA requires an accessible server at {BASE_URL}: {exc}")
    yield ctx
    ctx.close()


def _seed_calendar_data(page: Page) -> List[Dict[str, object]]:
    suffix = uuid.uuid4().hex[:6].upper()
    start_of_month = date.today().replace(day=1)
    scenarios = [
        ("Compliant QA", "DE", 10, "safe"),
        ("Warning QA", "FR", 80, "warning"),
        ("Critical QA", "IT", 95, "critical"),
    ]
    seeded: List[Dict[str, object]] = []

    for index, (label, country, duration, status) in enumerate(scenarios):
        employee_name = f"{label} {suffix}"
        create_employee = page.context.request.post("/add_employee", data={"name": employee_name})
        payload = create_employee.json()
        assert payload.get("success"), f"Failed to create employee: {payload}"
        employee_id = str(payload.get("employee_id"))

        entry = start_of_month + timedelta(days=index * 14)
        exit_date = entry + timedelta(days=duration - 1)
        create_trip = page.context.request.post(
            "/add_trip",
            data={
                "employee_id": employee_id,
                "country_code": country,
                "entry_date": _iso(entry),
                "exit_date": _iso(exit_date),
                "purpose": f"QA validation window ({status})",
            },
        )
        trip_payload = create_trip.json()
        assert trip_payload.get("success"), f"Failed to create trip: {trip_payload}"

        seeded.append(
            {
                "id": employee_id,
                "name": employee_name,
                "country": country,
                "entry": entry,
                "exit": exit_date,
                "status": status,
                "duration": duration,
            }
        )

    return seeded


@pytest.mark.e2e
def test_calendar_end_to_end_validation(context: BrowserContext) -> None:
    page = context.new_page()
    console_issues: List[str] = []
    failed_requests: List[str] = []
    js_exceptions: List[str] = []

    page.on(
        "console",
        lambda msg: console_issues.append(f"{msg.type}::{msg.text}")
        if msg.type in {"error", "warning"}
        else None,
    )
    page.on("pageerror", lambda exc: js_exceptions.append(str(exc)))
    page.on(
        "requestfailed",
        lambda req: failed_requests.append(f"{req.url} -> {req.failure.value if req.failure else 'unknown'}"),
    )

    page.goto("/login")
    expect(page.get_by_role("heading", name="🇪🇺 EU Trip Tracker")).to_be_visible()
    page.get_by_label("Admin Password").fill(ADMIN_PASSWORD)
    page.get_by_role("button", name="Login", exact=False).click()
    page.wait_for_url("**/dashboard")

    seeded = _seed_calendar_data(page)
    trips_payload = page.context.request.get("/api/trips").json()

    # Trips payload should reflect newly seeded records.
    for record in seeded:
        matches = [
            trip
            for trip in trips_payload.get("trips", [])
            if trip.get("employee_name") == record["name"]
        ]
        assert matches, f"Trip for {record['name']} missing from /api/trips payload."
        assert matches[0]["country"] == record["country"], "Country mismatch in API payload."

    # Calendar render + performance validation.
    start = time.perf_counter()
    page.goto("/calendar")
    page.wait_for_selector(".calendar-trip", state="visible")
    load_ms = (time.perf_counter() - start) * 1000
    assert load_ms <= MAX_LOAD_MS, f"Calendar load time {load_ms:.0f}ms exceeds {MAX_LOAD_MS}ms SLA."

    # Rendering verification.
    range_label = page.locator("#calendar-range-label")
    initial_range = range_label.inner_text().strip()
    expect(page.locator("#calendar-today-marker")).to_be_visible()
    expect(page.locator("#calendar-empty")).to_be_hidden()

    today_marker_transform = page.locator("#calendar-today-marker").evaluate(
        "el => el.style.transform"
    )
    start_of_month = date.today().replace(day=1)
    expected_offset_px = ((date.today() - start_of_month).days + 0.5) * 28
    if today_marker_transform:
        match = re.search(r"translateX\\(([-0-9.]+)px\\)", today_marker_transform)
        assert match, f"Unexpected today marker transform: {today_marker_transform}"
        actual_offset = float(match.group(1))
        assert abs(actual_offset - expected_offset_px) <= 30, "Today marker misaligned with current date."

    for record in seeded:
        trip = page.locator(f".calendar-trip[data-employee='{record['name']}']")
        expect(trip).to_be_visible()
        assert trip.get_attribute("data-compliance") == record["status"]
        assert trip.get_attribute("data-country") == record["country"]
        assert trip.get_attribute("data-start") == _iso(record["entry"])
        assert trip.get_attribute("data-end") == _iso(record["exit"])
        row_employee_id = trip.evaluate("el => el.closest('.calendar-grid-row').dataset.employeeId")
        assert row_employee_id == record["id"], "Trip rendered in incorrect employee row."

        computed_color = _rgb_to_hex(trip.evaluate("el => getComputedStyle(el).backgroundColor"))
        assert computed_color == STATUS_COLORS[record["status"]], "Trip color does not match status token."
        ratio = _contrast_ratio(STATUS_COLORS[record["status"]])
        assert ratio >= 4.5, f"{record['status']} trip color contrast {ratio:.2f} falls below WCAG AA."

    legend_items = page.locator(".calendar-legend-item span:last-child")
    expect(legend_items.nth(0)).to_have_text("Compliant")
    expect(legend_items.nth(1)).to_have_text("Approaching 90-day limit")
    expect(legend_items.nth(2)).to_have_text("Exceeded 90-day threshold")

    # Functional interactions.
    safe_trip = page.locator(f".calendar-trip[data-employee='{seeded[0]['name']}']")
    safe_trip.hover()
    tooltip = page.locator(".calendar-tooltip")
    expect(tooltip).to_be_visible()
    expect(tooltip).to_have_attribute("role", "tooltip")
    expect(tooltip).to_contain_text(seeded[0]["name"])
    expect(tooltip).to_contain_text(seeded[0]["country"])

    safe_trip.click()
    modal = page.locator("#calendar-detail-overlay")
    expect(modal).to_be_visible()
    expect(modal).to_contain_text(seeded[0]["name"])
    page.locator('[data-action="close-detail"]').click()
    expect(modal).to_be_hidden()

    safe_trip.focus()
    page.keyboard.press("Enter")
    expect(modal).to_be_visible()
    page.keyboard.press("Escape")
    expect(modal).to_be_hidden()

    next_button = page.locator('[data-action="next"]')
    prev_button = page.locator('[data-action="prev"]')
    today_button = page.locator('[data-action="today"]')

    next_button.click()
    expect(range_label).not_to_have_text(initial_range, timeout=3000)
    prev_button.click()
    expect(range_label).to_have_text(initial_range, timeout=3000)
    today_button.click()
    expect(range_label).to_have_text(initial_range, timeout=3000)

    search_input = page.locator("#calendar-search-input")
    search_input.fill("no matching employee")
    expect(page.locator("#calendar-empty")).to_be_visible()
    page.locator(".calendar-search-clear").click()
    expect(page.locator("#calendar-empty")).to_be_hidden()

    page.set_viewport_size({"width": 820, "height": 900})
    page.wait_for_timeout(100)
    desktop_box = page.locator(".calendar-shell").bounding_box()
    assert desktop_box and desktop_box["width"] <= 820
    page.set_viewport_size({"width": 414, "height": 896})
    page.wait_for_timeout(100)
    mobile_employee_overflow = page.locator("#calendar-employee-list").evaluate(
        "el => getComputedStyle(el).overflowY"
    )
    assert mobile_employee_overflow in {"auto", "scroll"}
    page.set_viewport_size(VIEWPORT)

    dashboard_response = page.context.request.get("/dashboard")
    assert dashboard_response.status == 200
    planner_response = page.context.request.get("/what_if_scenario")
    assert planner_response.status in {200, 302}
    employees_api = page.context.request.get("/api/employees/search")
    assert employees_api.status == 200

    # Stability checks.
    assert not console_issues, f"Console issues detected: {console_issues}"
    assert not js_exceptions, f"JavaScript exceptions detected: {js_exceptions}"
    assert not failed_requests, f"Network failures detected: {failed_requests}"

    page.close()
