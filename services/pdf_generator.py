# services/pdf_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime

def generate_pdf_report(report_data):
    """Generate professional PDF report from comparison data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph("ClauseCompare™ Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Report metadata
    created_at = report_data.get('metadata', {}).get('createdAt', '')
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_at = dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            pass
    
    metadata_data = [
        ['Report ID:', report_data.get('report_id', 'N/A')],
        ['Generated:', created_at],
        ['Original File:', report_data.get('file_a_name', 'N/A')],
        ['Modified File:', report_data.get('file_b_name', 'N/A')],
    ]
    
    metadata_table = Table(metadata_data, colWidths=[2*inch, 4.5*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Risk score box
    risk_score = report_data.get('risk_score', 0)
    risk_color = colors.HexColor('#dc2626') if risk_score >= 70 else colors.HexColor('#f59e0b') if risk_score >= 40 else colors.HexColor('#10b981')
    
    risk_data = [
        ['OVERALL RISK SCORE'],
        [f'{risk_score}/100'],
    ]
    
    risk_table = Table(risk_data, colWidths=[6.5*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 36),
        ('TEXTCOLOR', (0, 1), (-1, 1), risk_color),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#e5e7eb')),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Executive summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary_text = report_data.get('summary', 'No summary available')
    story.append(Paragraph(summary_text, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    # Verdict
    if report_data.get('verdict'):
        story.append(Paragraph("Verdict", heading_style))
        story.append(Paragraph(report_data['verdict'], styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
    
    # Changes breakdown
    metadata = report_data.get('metadata', {})
    type_breakdown = metadata.get('typeBreakdown', {})
    if type_breakdown:
        story.append(Paragraph("Changes Summary", heading_style))
        
        breakdown_data = [
            ['Change Type', 'Count'],
            ['Added', str(type_breakdown.get('Added', 0))],
            ['Removed', str(type_breakdown.get('Removed', 0))],
            ['Modified', str(type_breakdown.get('Modified', 0))],
            ['Reworded', str(type_breakdown.get('Reworded', 0))],
        ]
        
        breakdown_table = Table(breakdown_data, colWidths=[3*inch, 3.5*inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(breakdown_table)
        story.append(PageBreak())
    
    # Detailed changes
    diffs = report_data.get('diffs', [])
    if diffs:
        story.append(Paragraph("Detailed Clause Analysis", heading_style))
        story.append(Spacer(1, 0.2*inch))
        
        for i, diff in enumerate(diffs[:20], 1):  # Limit to first 20 for reasonable PDF size
            # Clause header
            clause_title = f"{i}. {diff.get('clause', 'Unknown')} - {diff.get('type', 'Modified')}"
            story.append(Paragraph(clause_title, ParagraphStyle(
                'ClauseTitle',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=8
            )))
            
            # Severity badge
            severity = diff.get('severity', 'Medium')
            severity_color = {
                'High': colors.HexColor('#dc2626'),
                'Medium': colors.HexColor('#f59e0b'),
                'Low': colors.HexColor('#10b981')
            }.get(severity, colors.grey)
            
            severity_text = f"{severity} Risk"
            if diff.get('confidence'):
                severity_text += f" - Confidence: {diff['confidence']}%"
            
            severity_data = [[severity_text]]
            severity_table = Table(severity_data, colWidths=[6.5*inch])
            severity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), severity_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(severity_table)
            story.append(Spacer(1, 0.1*inch))
            
            # Summary
            summary = diff.get('summary', '')
            if summary:
                story.append(Paragraph(f"<b>Summary:</b> {summary}", styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))
            
            # Explanation
            explanation = diff.get('explanation', '')
            if explanation:
                story.append(Paragraph(f"<b>Analysis:</b> {explanation}", styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))
            
            # Suggestions
            suggestions = diff.get('suggestions', [])
            if suggestions:
                story.append(Paragraph("<b>Negotiation Suggestions:</b>", styles['BodyText']))
                for suggestion in suggestions[:3]:  # Limit to top 3
                    story.append(Paragraph(f"• {suggestion}", styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
        
        if len(diffs) > 20:
            story.append(Paragraph(f"<i>Note: Showing first 20 of {len(diffs)} total changes.</i>", styles['BodyText']))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = """
    <para align=center>
    <font size=8 color=#6b7280>
    This report was generated by ClauseCompare™ AI Contract Analysis Platform.<br/>
    For questions or support, visit clausecompare.com<br/>
    © 2025 ClauseCompare. All rights reserved.
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, styles['BodyText']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
