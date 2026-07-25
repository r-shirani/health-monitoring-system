from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_vital_signs_pdf(response_stream, device, user, vitals, stats, date_range, start_filter, end_filter, now):
    doc = SimpleDocTemplate(
        response_stream, 
        pagesize=letter, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=30, 
        bottomMargin=30
    )
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#1a365d'), alignment=1)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#2c5282'), spaceBefore=15, spaceAfter=5)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=15)

    story.append(Paragraph("Patient Vital Signs Medical Report", title_style))
    story.append(Spacer(1, 15))
    
    info_text = f"<b>Device Name:</b> {device.name} | <b>Hardware ID:</b> {device.device_id}<br/>" \
                f"<b>Account:</b> {user.username} | <b>Export Date:</b> {now.strftime('%Y-%m-%d %H:%M:%S')}<br/>" \
                f"<b>Report Range:</b> {date_range.upper()} ({start_filter.strftime('%Y-%m-%d')} to {end_filter.strftime('%Y-%m-%d')})"
    story.append(Paragraph(info_text, body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("1. Executive Medical Summary", section_style))
    summary_data = [
        ['Vital Sign', 'Average (Mean)', 'Minimum', 'Maximum'],
        ['Heart Rate (BPM)', f"{stats['avg_hr']:.1f}" if stats['avg_hr'] else 'N/A', stats['min_hr'] or 'N/A', stats['max_hr'] or 'N/A'],
        ['Blood Oxygen (SpO2)', f"{stats['avg_ox']:.1f}%" if stats['avg_ox'] else 'N/A', f"{stats['min_ox']}%" if stats['min_ox'] else 'N/A', f"{stats['max_ox']}%" if stats['max_ox'] else 'N/A']
    ]
    t_summary = Table(summary_data, colWidths=[150, 120, 100, 100])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f7fafc')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))

    story.append(Paragraph("2. Detailed Vital Signs Log", section_style))
    log_data = [['#', 'Timestamp', 'Heart Rate (BPM)', 'Oxygen Level (SpO2)']]
    
    for idx, r in enumerate(vitals[:50], 1):
        log_data.append([idx, r.timestamp.strftime('%Y-%m-%d %H:%M:%S'), r.heart_rate, f"{r.oxygen_level}%"])
        
    t_log = Table(log_data, colWidths=[40, 180, 130, 120])
    t_log.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#edf2f7')),
    ]))
    story.append(t_log)

    doc.build(story)