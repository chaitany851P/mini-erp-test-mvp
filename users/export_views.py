from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from users.models import User
from mini_erp.firebase_utils import get_all_documents
import pandas as pd
import io
from datetime import datetime, date

@login_required
def export_students_excel(request):
    """Export student data to Excel - Admin/Faculty only"""
    if not (request.user.is_admin() or request.user.is_faculty()):
        return HttpResponseForbidden('Access denied. Admin or Faculty role required.')
    
    # Get all students
    students = User.objects.filter(role='Student').order_by('created_at')
    
    # Prepare data for Excel
    data = []
    for student in students:
        data.append({
            'Student ID': student.student_id,
            'Name': student.get_display_name(),
            'Email': student.email,
            'Phone': student.phone or 'N/A',
            'Date of Birth': student.date_of_birth or 'N/A',
            'Address': student.address or 'N/A',
            'Active': 'Yes' if student.is_active else 'No',
            'Email Verified': 'Yes' if student.is_email_verified else 'No',
            'Created Date': student.created_at.strftime('%Y-%m-%d %H:%M') if student.created_at else 'N/A'
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Students', index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Students']
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
    
    output.seek(0)
    
    # Create response
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="students_export_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    return response

@login_required
def export_attendance_excel(request):
    """Export attendance data to Excel - Admin/Faculty only"""
    if not (request.user.is_admin() or request.user.is_faculty()):
        return HttpResponseForbidden('Access denied. Admin or Faculty role required.')
    
    # Get attendance data from Firestore
    attendance_docs = get_all_documents('attendance')
    
    # Prepare data for Excel
    data = []
    for doc in attendance_docs:
        data.append({
            'Student ID': doc.get('student_id', 'N/A'),
            'Date': doc.get('date', 'N/A'),
            'Present': 'Yes' if doc.get('present') else 'No',
            'Subject': doc.get('subject', 'N/A'),
            'Period': doc.get('period', 'N/A'),
            'Recorded At': doc.get('created_at', 'N/A')
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Sort by date and student ID
    if not df.empty:
        df = df.sort_values(['Date', 'Student ID'])
    
    # Create Excel file with multiple sheets
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Main attendance sheet
        df.to_excel(writer, sheet_name='Attendance Records', index=False)
        
        # Attendance Summary sheet
        if not df.empty:
            summary_data = []
            for student_id in df['Student ID'].unique():
                student_records = df[df['Student ID'] == student_id]
                total_days = len(student_records)
                present_days = len(student_records[student_records['Present'] == 'Yes'])
                attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
                
                summary_data.append({
                    'Student ID': student_id,
                    'Total Days': total_days,
                    'Present Days': present_days,
                    'Absent Days': total_days - present_days,
                    'Attendance Rate (%)': round(attendance_rate, 2)
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Attendance Summary', index=False)
        
        # Format sheets
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col_num in range(len(df.columns) if sheet_name == 'Attendance Records' else len(summary_df.columns)):
                worksheet.set_column(col_num, col_num, 15)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="attendance_export_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    return response

@login_required
def export_fees_excel(request):
    """Export fee data to Excel - Admin/Faculty only"""
    if not (request.user.is_admin() or request.user.is_faculty()):
        return HttpResponseForbidden('Access denied. Admin or Faculty role required.')
    
    # Get fee data from Firestore
    fee_docs = get_all_documents('fees')
    
    # Prepare data for Excel
    data = []
    for doc in fee_docs:
        data.append({
            'Student ID': doc.get('student_id', 'N/A'),
            'Student Name': doc.get('student_name', 'N/A'),
            'Fee Type': doc.get('fee_type', 'N/A'),
            'Amount': doc.get('amount', 0),
            'Due Date': doc.get('due_date', 'N/A'),
            'Status': doc.get('status', 'N/A').title(),
            'Paid Date': doc.get('paid_at', 'N/A'),
            'Created At': doc.get('created_at', 'N/A')
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Sort by due date
    if not df.empty:
        df = df.sort_values(['Due Date', 'Student ID'])
    
    # Create Excel file with multiple sheets
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Main fees sheet
        df.to_excel(writer, sheet_name='Fee Records', index=False)
        
        # Fee Summary sheet
        if not df.empty:
            summary_data = []
            for student_id in df['Student ID'].unique():
                student_records = df[df['Student ID'] == student_id]
                total_amount = student_records['Amount'].sum()
                paid_amount = student_records[student_records['Status'] == 'Completed']['Amount'].sum()
                pending_amount = total_amount - paid_amount
                
                summary_data.append({
                    'Student ID': student_id,
                    'Student Name': student_records['Student Name'].iloc[0],
                    'Total Amount': total_amount,
                    'Paid Amount': paid_amount,
                    'Pending Amount': pending_amount,
                    'Payment Status': 'Completed' if pending_amount == 0 else 'Partial' if paid_amount > 0 else 'Pending'
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Fee Summary', index=False)
        
        # Overdue fees sheet
        if not df.empty:
            today = date.today().isoformat()
            overdue_df = df[(df['Status'] != 'Completed') & (df['Due Date'] < today)]
            if not overdue_df.empty:
                overdue_df.to_excel(writer, sheet_name='Overdue Fees', index=False)
        
        # Format sheets
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#FFE6E6',
            'border': 1
        })
        
        currency_format = workbook.add_format({'num_format': '$#,##0.00'})
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col_num in range(8):  # Adjust based on columns
                worksheet.set_column(col_num, col_num, 15)
                if col_num in [3, 4, 5]:  # Amount columns
                    worksheet.set_column(col_num, col_num, 12, currency_format)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="fees_export_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    return response

@login_required
def export_risk_analysis_excel(request):
    """Export risk analysis data to Excel - Admin/Faculty only"""
    if not (request.user.is_admin() or request.user.is_faculty()):
        return HttpResponseForbidden('Access denied. Admin or Faculty role required.')
    
    from students.views import evaluate_risk
    from mini_erp.firebase_utils import get_all_documents
    
    # Get all student IDs from attendance records
    attendance_docs = get_all_documents('attendance')
    student_ids = list(set([doc.get('student_id') for doc in attendance_docs if doc.get('student_id')]))
    
    # Prepare risk analysis data
    data = []
    for student_id in student_ids:
        try:
            risk_data = evaluate_risk(student_id)
            data.append({
                'Student ID': student_id,
                'Attendance %': risk_data.get('attendance_percent', 0),
                'At Risk': 'Yes' if risk_data.get('at_risk', False) else 'No',
                'Overdue Fees': 'Yes' if risk_data.get('overdue_fees', False) else 'No',
                'Failing Grades': 'Yes' if risk_data.get('failing_grades', False) else 'No',
                'Risk Reasons': ', '.join(risk_data.get('reasons', [])),
                'Total Risk Factors': len(risk_data.get('reasons', []))
            })
        except Exception as e:
            print(f"Error evaluating risk for {student_id}: {e}")
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Sort by risk level (at-risk first)
    if not df.empty:
        df = df.sort_values(['At Risk', 'Total Risk Factors'], ascending=[False, False])
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Risk Analysis', index=False)
        
        # Format the sheet
        workbook = writer.book
        worksheet = writer.sheets['Risk Analysis']
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#FFD700',
            'border': 1
        })
        
        # Risk highlighting formats
        high_risk_format = workbook.add_format({'bg_color': '#FFE6E6'})
        low_risk_format = workbook.add_format({'bg_color': '#E6FFE6'})
        
        # Apply formatting
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
        
        # Highlight at-risk students
        for row_num in range(1, len(df) + 1):
            if df.iloc[row_num - 1]['At Risk'] == 'Yes':
                worksheet.set_row(row_num, None, high_risk_format)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="risk_analysis_export_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    return response

@login_required
def export_comprehensive_report(request):
    """Export comprehensive report with all data - Admin only"""
    if not request.user.is_admin():
        return HttpResponseForbidden('Access denied. Admin role required.')
    
    # This would be a comprehensive report combining all data
    # For now, we'll create a summary report
    
    students = User.objects.filter(role='Student')
    attendance_docs = get_all_documents('attendance')
    fee_docs = get_all_documents('fees')
    
    # Create summary data
    summary_data = {
        'Total Students': students.count(),
        'Active Students': students.filter(is_active=True).count(),
        'Total Attendance Records': len(attendance_docs),
        'Total Fee Records': len(fee_docs),
        'Report Generated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Create Excel with summary
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Summary sheet
        summary_df = pd.DataFrame([summary_data])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Add note sheet
        notes = [
            ['Note', 'This is a comprehensive report generated from the Mini ERP system'],
            ['Generated By', request.user.get_display_name()],
            ['Generated On', timezone.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['System', 'Mini ERP - Student Management System']
        ]
        notes_df = pd.DataFrame(notes, columns=['Field', 'Value'])
        notes_df.to_excel(writer, sheet_name='Report Info', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="comprehensive_report_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    return response