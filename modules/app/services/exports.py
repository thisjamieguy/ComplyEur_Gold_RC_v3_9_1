import sqlite3
import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .rolling90 import presence_days, days_used_in_window


def calculate_eu_days_from_trips(trips: List[Dict], reference_date: datetime.date) -> int:
    """Calculate Schengen days within 180-day window from reference_date.
    Ireland (IE) trips are excluded from calculations."""
    # Use the new rolling90 logic that filters out Ireland
    presence = presence_days(trips)
    return days_used_in_window(presence, reference_date)


def export_trips_csv(db_path: str, employee_id: int = None) -> str:
    """Export trips to CSV format.
    If employee_id is provided, export only that employee's trips.
    Returns CSV as string."""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if employee_id:
        c.execute('''
            SELECT employees.name, trips.country, trips.entry_date, 
                   trips.exit_date, trips.travel_days
            FROM trips
            JOIN employees ON trips.employee_id = employees.id
            WHERE trips.employee_id = ?
            ORDER BY trips.entry_date DESC
        ''', (employee_id,))
    else:
        c.execute('''
            SELECT employees.name, trips.country, trips.entry_date, 
                   trips.exit_date, trips.travel_days
            FROM trips
            JOIN employees ON trips.employee_id = employees.id
            ORDER BY employees.name, trips.entry_date DESC
        ''')
    
    rows = c.fetchall()
    conn.close()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Employee Name', 'Country', 'Entry Date', 'Exit Date', 'Travel Days', 'Schengen Status'])
    
    for row in rows:
        # Determine if country is Schengen (exclude Ireland)
        is_schengen = row['country'].upper() not in ['IE', 'IRELAND']
        schengen_status = 'Schengen' if is_schengen else 'Non-Schengen'
        
        writer.writerow([
            row['name'],
            row['country'],
            row['entry_date'],
            row['exit_date'],
            row['travel_days'] or 0,
            schengen_status
        ])
    
    return output.getvalue()


def export_employee_report_pdf(db_path: str, employee_id: int) -> bytes:
    """Generate PDF report for an employee with trip history and compliance status.
    Returns PDF as bytes."""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get employee
    c.execute('SELECT id, name FROM employees WHERE id = ?', (employee_id,))
    emp = c.fetchone()
    if not emp:
        conn.close()
        raise ValueError('Employee not found')
    
    # Get trips
    c.execute('''
        SELECT country, entry_date, exit_date, travel_days
        FROM trips
        WHERE employee_id = ?
        ORDER BY entry_date DESC
    ''', (employee_id,))
    trips = [dict(row) for row in c.fetchall()]
    conn.close()
    
    # Calculate days used
    today = datetime.now().date()
    days_used = calculate_eu_days_from_trips(trips, today)
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph('EU Trip Compliance Report', title_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Employee info
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>Employee:</b> {emp['name']}", info_style))
    elements.append(Paragraph(f"<b>Report Date:</b> {today.strftime('%d-%m-%Y')}", info_style))
    elements.append(Paragraph(f"<b>Days Used (Last 180 days):</b> {days_used} / 90", info_style))
    
    # Status indicator
    if days_used > 90:
        status_text = f'<font color="red"><b>⚠ OVER LIMIT by {days_used - 90} days</b></font>'
    elif days_used > 80:
        status_text = f'<font color="orange"><b>⚠ WARNING: {90 - days_used} days remaining</b></font>'
    else:
        status_text = f'<font color="green"><b>✓ SAFE: {90 - days_used} days remaining</b></font>'
    
    elements.append(Paragraph(f"<b>Status:</b> {status_text}", info_style))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Trips table
    if trips:
        elements.append(Paragraph('<b>Trip History</b>', styles['Heading2']))
        elements.append(Spacer(1, 0.2 * inch))
        
        table_data = [['Country', 'Entry Date', 'Exit Date', 'Duration']]
        for trip in trips:
            entry = datetime.strptime(trip['entry_date'], '%Y-%m-%d').date()
            exit_date = datetime.strptime(trip['exit_date'], '%Y-%m-%d').date()
            duration = (exit_date - entry).days + 1
            
            table_data.append([
                trip['country'],
                entry.strftime('%d-%m-%Y'),
                exit_date.strftime('%d-%m-%Y'),
                f"{duration} days"
            ])
        
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph('No trips recorded.', styles['Normal']))
    
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(
        '<i>This report is generated for compliance tracking purposes only. '
        'Data is stored locally and not shared with third parties.</i>',
        styles['Italic']
    ))
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def export_all_employees_report_pdf(db_path: str) -> bytes:
    """Generate PDF report for all employees with summary.
    Returns PDF as bytes."""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT id, name FROM employees ORDER BY name')
    employees = c.fetchall()
    
    today = datetime.now().date()
    employee_data = []
    
    for emp in employees:
        c.execute('''
            SELECT country, entry_date, exit_date
            FROM trips
            WHERE employee_id = ?
        ''', (emp['id'],))
        trips = [dict(row) for row in c.fetchall()]
        
        days_used = calculate_eu_days_from_trips(trips, today)
        trip_count = len(trips)
        
        employee_data.append({
            'name': emp['name'],
            'days_used': days_used,
            'trip_count': trip_count,
            'status': 'Over Limit' if days_used > 90 else ('Warning' if days_used > 80 else 'Safe')
        })
    
    conn.close()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph('EU Trip Compliance Summary', title_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    elements.append(Paragraph(f"<b>Report Date:</b> {today.strftime('%d-%m-%Y')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Total Employees:</b> {len(employees)}", styles['Normal']))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Summary table
    if employee_data:
        table_data = [['Employee Name', 'Days Used', 'Trips', 'Status']]
        
        for emp_data in employee_data:
            status_color = 'red' if emp_data['status'] == 'Over Limit' else (
                'orange' if emp_data['status'] == 'Warning' else 'green'
            )
            table_data.append([
                emp_data['name'],
                f"{emp_data['days_used']}/90",
                str(emp_data['trip_count']),
                emp_data['status']
            ])
        
        table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(table)
    
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(
        '<i>This report is generated for compliance tracking purposes only.</i>',
        styles['Italic']
    ))
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

