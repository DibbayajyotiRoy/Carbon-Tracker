from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from datetime import datetime
import io
from typing import List, Dict, Any

def generate_professional_report(user_id: str, data: Dict[str, Any]) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#2E7D32"), # Green branding
        spaceAfter=20,
        alignment=1 # Center
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#1B5E20"),
        spaceBefore=15,
        spaceAfter=10
    )
    
    normal_style = styles["Normal"]
    
    elements = []
    
    # 1. Header Section
    elements.append(Paragraph("Carbon Tracker - Professional Audit Report", title_style))
    elements.append(Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Paragraph(f"<b>User Identification:</b> {user_id}", normal_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # 2. Executive Summary
    elements.append(Paragraph("Executive Summary", header_style))
    
    summary_data = [["Category", "CO2e (kg)", "Percentage"]]
    total_co2 = data.get("total_co2", 0)
    
    categories = [
        ("Diet", data.get("diet_total", 0)),
        ("Transport", data.get("transport_total", 0)),
        ("Energy", data.get("energy_total", 0))
    ]
    
    for cat, val in categories:
        perc = (val / total_co2 * 100) if total_co2 > 0 else 0
        summary_data.append([cat, f"{val:.2f}", f"{perc:.1f}%"])
        
    summary_data.append(["<b>Total</b>", f"<b>{total_co2:.2f}</b>", "<b>100%</b>"])
    
    summary_table = Table(summary_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E8F5E9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4 * inch))
    
    # 3. Detailed Audit
    
    # --- Diet ---
    elements.append(Paragraph("Diet Audit", header_style))
    diet_items = data.get("diet_items", [])
    if diet_items:
        diet_data = [["Food Item", "Qty (g)", "CO2e (kg)"]]
        # Show top 10 highest impact items
        sorted_diet = sorted(diet_items, key=lambda x: x['co2_kg'], reverse=True)[:10]
        for item in sorted_diet:
            diet_data.append([item['food_type'], f"{item['quantity_grams']:.0f}", f"{item['co2_kg']:.2f}"])
            
        t = Table(diet_data, colWidths=[2.5 * inch, 1.25 * inch, 1.25 * inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#FFF3E0")), # Light Orange
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#E65100")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No diet records found.", normal_style))
        
    elements.append(Spacer(1, 0.3 * inch))
    
    # --- Transport ---
    elements.append(Paragraph("Transport Audit", header_style))
    transport_logs = data.get("transport_logs", [])
    if transport_logs:
        dist = sum(log['distance_km'] for log in transport_logs)
        vehicle = data.get("vehicle", {})
        elements.append(Paragraph(f"<b>Total Distance Traveled:</b> {dist:.2f} km", normal_style))
        if vehicle:
            elements.append(Paragraph(f"<b>Vehicle:</b> {vehicle.get('make', 'N/A')} {vehicle.get('model', 'N/A')} ({vehicle.get('year', 'N/A')})", normal_style))
            elements.append(Paragraph(f"<b>Efficiency:</b> {vehicle.get('emission_factor', 0):.4f} kg CO2e/km", normal_style))
    else:
        elements.append(Paragraph("No transport records found.", normal_style))
        
    elements.append(Spacer(1, 0.3 * inch))
    
    # --- Utilities ---
    elements.append(Paragraph("Utilities Audit (Electricity & LPG)", header_style))
    bills = data.get("electricity_bills", [])
    lpg = data.get("lpg_records", [])
    
    if bills or lpg:
        if bills:
            elements.append(Paragraph("<b>Electricity Usage:</b>", normal_style))
            bill_data = [["Bill Name", "Units", "CO2e (kg)"]]
            for b in bills:
                # extracted_data might be a dict or string JSON
                units = 0
                if isinstance(b['extracted_data'], dict):
                    units = b['extracted_data'].get("unitsConsumed", 0)
                bill_data.append([b['file_name'], f"{units}", f"{b['carbon_emitted']:.2f}"])
            
            t = Table(bill_data, colWidths=[3 * inch, 1 * inch, 1 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")), # Light Blue
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0D47A1")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.2 * inch))
            
        if lpg:
            elements.append(Paragraph("<b>LPG Usage:</b>", normal_style))
            lpg_data = [["Date", "Cylinders", "CO2e (kg)"]]
            for r in lpg:
                date_str = r['created_at'].strftime('%Y-%m-%d') if isinstance(r['created_at'], datetime) else "N/A"
                lpg_data.append([date_str, f"{r['cylinders_consumed']}", f"{r['carbon_emitted']:.2f}"])
            
            t = Table(lpg_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3E5F5")), # Light Purple
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#4A148C")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
            ]))
            elements.append(t)
    else:
        elements.append(Paragraph("No utility records found.", normal_style))
        
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
