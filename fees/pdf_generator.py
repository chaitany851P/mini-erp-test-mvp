"""
PDF generation utility for fee receipts using ReportLab
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
import os
from datetime import datetime
import io
from django.http import HttpResponse

def generate_fee_receipt_pdf(fee_payment):
    """
    Generate PDF receipt for fee payment
    
    Args:
        fee_payment: FeePayment model instance
    
    Returns:
        HttpResponse with PDF content
    """
    # Create a bytes buffer for the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        alignment=TA_LEFT,
        textColor=colors.black
    )
    
    # Title
    title = Paragraph("Mini ERP System", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Fee Payment Receipt", subtitle_style)
    elements.append(subtitle)
    
    # Add space
    elements.append(Spacer(1, 20))
    
    # Receipt details table
    receipt_data = [
        ['Receipt No:', fee_payment.transaction_id],
        ['Date:', fee_payment.created_at.strftime('%B %d, %Y')],
        ['Time:', fee_payment.created_at.strftime('%I:%M %p')],
        ['', ''],  # Empty row for spacing
        ['Student ID:', fee_payment.student_id],
        ['Student Name:', fee_payment.student_name],
        ['Student Email:', fee_payment.student_email],
        ['', ''],  # Empty row for spacing
        ['Fee Type:', fee_payment.fee_type],
        ['Payment Mode:', fee_payment.get_payment_mode_display()],
        ['Amount Paid:', f"${fee_payment.amount:.2f}"],
        ['Status:', fee_payment.get_status_display()],
    ]
    
    if fee_payment.notes:
        receipt_data.append(['', ''])
        receipt_data.append(['Notes:', fee_payment.notes])
    
    # Create table
    receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        
        # Highlight amount row
        ('BACKGROUND', (0, 10), (-1, 10), colors.lightgrey),
        ('FONTNAME', (0, 10), (-1, 10), 'Helvetica-Bold'),
        
        # Add borders to non-empty rows
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(receipt_table)
    
    # Add space
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    footer_text = f"""
    <para align=center>
    <b>Thank you for your payment!</b><br/>
    This is a computer-generated receipt.<br/>
    For queries, contact the accounts department.<br/><br/>
    Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    </para>
    """
    
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Create HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{fee_payment.transaction_id}.pdf"'
    response.write(pdf_content)
    
    return response

def save_receipt_pdf(fee_payment, save_path=None):
    """
    Save fee receipt PDF to file system
    
    Args:
        fee_payment: FeePayment model instance
        save_path: Optional custom save path
    
    Returns:
        str: File path where PDF was saved
    """
    if save_path is None:
        save_path = os.path.join(settings.MEDIA_ROOT, 'receipts', f'receipt_{fee_payment.transaction_id}.pdf')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Create a file buffer for the PDF
    doc = SimpleDocTemplate(save_path, pagesize=A4, 
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles (same as above)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    # Title
    title = Paragraph("Mini ERP System", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Fee Payment Receipt", subtitle_style)
    elements.append(subtitle)
    
    # Add space
    elements.append(Spacer(1, 20))
    
    # Receipt details table (same as above)
    receipt_data = [
        ['Receipt No:', fee_payment.transaction_id],
        ['Date:', fee_payment.created_at.strftime('%B %d, %Y')],
        ['Time:', fee_payment.created_at.strftime('%I:%M %p')],
        ['', ''],
        ['Student ID:', fee_payment.student_id],
        ['Student Name:', fee_payment.student_name],
        ['Student Email:', fee_payment.student_email],
        ['', ''],
        ['Fee Type:', fee_payment.fee_type],
        ['Payment Mode:', fee_payment.get_payment_mode_display()],
        ['Amount Paid:', f"${fee_payment.amount:.2f}"],
        ['Status:', fee_payment.get_status_display()],
    ]
    
    if fee_payment.notes:
        receipt_data.append(['', ''])
        receipt_data.append(['Notes:', fee_payment.notes])
    
    # Create table
    receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 10), (-1, 10), colors.lightgrey),
        ('FONTNAME', (0, 10), (-1, 10), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(receipt_table)
    
    # Add space
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    footer_text = f"""
    <para align=center>
    <b>Thank you for your payment!</b><br/>
    This is a computer-generated receipt.<br/>
    For queries, contact the accounts department.<br/><br/>
    Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    </para>
    """
    
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)
    
    # Build the PDF
    doc.build(elements)
    
    return save_path
