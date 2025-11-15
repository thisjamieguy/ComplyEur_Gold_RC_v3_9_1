"""Marketing and informational pages for ComplyEur."""

from __future__ import annotations

import json
import os
from datetime import datetime

from flask import current_app, jsonify, make_response, redirect, render_template, request, url_for

from app.middleware.auth import login_required
from .base import ATTEMPT_WINDOW_SECONDS, MAX_ATTEMPTS, load_config, logger, main_bp


@main_bp.route('/')
def index():
    return render_template('landing.html')


@main_bp.route('/landing')
def landing():
    return render_template('landing.html')


@main_bp.route('/sitemap.xml')
def sitemap():
    """Generate sitemap.xml for SEO."""
    base_url = request.url_root.rstrip('/')
    urls = [
        {
            'loc': f'{base_url}{url_for("main.landing")}',
            'changefreq': 'monthly',
            'priority': '1.0',
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
        },
        {
            'loc': f'{base_url}{url_for("main.home")}',
            'changefreq': 'daily',
            'priority': '0.9',
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
        },
        {
            'loc': f'{base_url}{url_for("main.dashboard")}',
            'changefreq': 'daily',
            'priority': '0.9',
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
        },
        {
            'loc': f'{base_url}{url_for("main.privacy_policy")}',
            'changefreq': 'monthly',
            'priority': '0.5',
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
        },
        {
            'loc': f'{base_url}{url_for("main.cookie_policy")}',
            'changefreq': 'monthly',
            'priority': '0.5',
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
        },
        {
            'loc': f'{base_url}{url_for("main.entry_requirements")}',
            'changefreq': 'weekly',
            'priority': '0.8',
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
        },
    ]

    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for url in urls:
        sitemap_xml += f"""  <url>
    <loc>{url['loc']}</loc>
    <changefreq>{url['changefreq']}</changefreq>
    <priority>{url['priority']}</priority>
    <lastmod>{url['lastmod']}</lastmod>
  </url>
"""
    sitemap_xml += '</urlset>'

    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response


@main_bp.route('/robots.txt')
def robots():
    """Generate robots.txt for SEO."""
    robots_txt = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /static/build/

Sitemap: {request.url_root.rstrip('/')}/sitemap.xml
"""

    response = make_response(robots_txt)
    response.headers['Content-Type'] = 'text/plain'
    return response


@main_bp.route('/api/test')
def api_test():
    """Simple diagnostic endpoint."""
    return {'status': 'ok', 'path': request.path}


@main_bp.route('/help')
@login_required
def help_page():
    """Display help and tutorial page."""
    help_file = os.path.join(os.path.dirname(__file__), '..', 'help_content.json')
    try:
        with open(help_file, 'r') as file_handle:
            help_content = json.load(file_handle)
    except Exception:
        help_content = {
            'page_title': 'Help & User Guide',
            'page_subtitle': 'Learn how to use ComplyEur',
            'sections': [],
            'tutorial_steps': [],
            'quick_tips': [],
        }
    return render_template('help.html', help_content=help_content)


@main_bp.route('/entry-requirements')
@login_required
def entry_requirements():
    """Display EU entry requirements for UK citizens."""
    countries = sorted(current_app.config['EU_ENTRY_DATA'], key=lambda x: x['country'])
    return render_template('entry_requirements.html', countries=countries)


@main_bp.route('/api/entry-requirements')
@login_required
def entry_requirements_api():
    """API endpoint returning EU entry requirements as JSON."""
    countries = sorted(current_app.config['EU_ENTRY_DATA'], key=lambda x: x['country'])
    return jsonify(countries)


@main_bp.route('/api/entry-requirements/reload', methods=['POST'])
@login_required
def reload_entry_requirements():
    """Reload EU entry requirements data from JSON file."""
    try:
        data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'eu_entry_requirements.json')
        with open(data_file_path, 'r', encoding='utf-8') as data_file:
            new_data = json.load(data_file)
        current_app.config['EU_ENTRY_DATA'] = new_data
        return jsonify({
            'success': True,
            'message': f'Successfully reloaded {len(new_data)} countries',
            'count': len(new_data),
        })
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Error reloading data: {exc}'}), 500


@main_bp.route('/test-summary', methods=['GET'])
# @login_required  # Temporarily disabled for testing
def test_summary():
    """Temporary development-only summary page."""
    config = load_config()
    if not config.get('TEST_MODE', False):
        return render_template('404.html'), 404

    from app.models import get_db

    employee_id = request.args.get('employee_id', type=int)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id, name FROM employees ORDER BY name')
    employees = [type('Employee', (), {'id': row['id'], 'name': row['name']})() for row in cursor.fetchall()]

    trips_data = []
    selected_employee = None
    totals = {'total_days': 0, 'travel_days': 0, 'working_days': 0}

    if employee_id:
        cursor.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
        emp_row = cursor.fetchone()
        if emp_row:
            selected_employee = type('Employee', (), {'id': emp_row['id'], 'name': emp_row['name']})()
            cursor.execute('''
                SELECT id, country, entry_date, exit_date, purpose, travel_days
                FROM trips
                WHERE employee_id = ?
                ORDER BY entry_date DESC
            ''', (employee_id,))

            for row in cursor.fetchall():
                entry = datetime.strptime(row['entry_date'], '%Y-%m-%d').date()
                exit_date = datetime.strptime(row['exit_date'], '%Y-%m-%d').date()
                total_days = (exit_date - entry).days + 1
                travel_days = row['travel_days'] or 0
                working_days = total_days - travel_days

                from app.services.rolling90 import is_schengen_country
                is_schengen = is_schengen_country(row['country'])

                trip_info = {
                    'id': row['id'],
                    'country': row['country'],
                    'entry_date': row['entry_date'],
                    'exit_date': row['exit_date'],
                    'purpose': row['purpose'] or '',
                    'total_days': total_days,
                    'travel_days': travel_days,
                    'working_days': working_days,
                    'is_schengen': is_schengen,
                }
                trips_data.append(trip_info)

                totals['total_days'] += total_days
                totals['travel_days'] += travel_days
                totals['working_days'] += working_days

    return render_template(
        'test_summary.html',
        employees=employees,
        selected_employee=selected_employee,
        trips=trips_data,
        totals=totals,
    )
