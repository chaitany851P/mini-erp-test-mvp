from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from .forms import FeePaymentForm
from .models import FeePayment
from .pdf_generator import generate_fee_receipt_pdf, save_receipt_pdf
from mini_erp.firebase_utils import add_document, get_all_documents, get_document
import logging

logger = logging.getLogger(__name__)

def fee_payment(request):
    """Fee payment form"""
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            try:
                fee_payment = form.save()
                
                # Save to Firestore
                payment_data = {
                    'transaction_id': fee_payment.transaction_id,
                    'student_id': fee_payment.student_id,
                    'student_name': fee_payment.student_name,
                    'student_email': fee_payment.student_email,
                    'amount': str(fee_payment.amount),
                    'payment_mode': fee_payment.payment_mode,
                    'fee_type': fee_payment.fee_type,
                    'status': fee_payment.status,
                    'notes': fee_payment.notes,
                    'created_at': fee_payment.created_at.isoformat(),
                }
                
                doc_id = add_document('fees', payment_data, fee_payment.transaction_id)
                
                messages.success(request, f'Payment processed successfully! Transaction ID: {fee_payment.transaction_id}')
                return redirect('fees:receipt', transaction_id=fee_payment.transaction_id)
                    
            except Exception as e:
                logger.error(f'Error processing payment: {e}')
                messages.error(request, 'Error processing payment. Please try again.')
    else:
        form = FeePaymentForm()
    
    return render(request, 'fees/payment.html', {'form': form})

def fee_list(request):
    """List all fee payments"""
    try:
        # Get from Firestore and local database
        firestore_fees = get_all_documents('fees')
        local_fees = FeePayment.objects.all()
        
        # Combine and process
        all_fees = firestore_fees + [
            {
                'transaction_id': fee.transaction_id,
                'student_name': fee.student_name,
                'amount': str(fee.amount),
                'fee_type': fee.fee_type,
                'status': fee.status,
                'created_at': fee.created_at.isoformat(),
            }
            for fee in local_fees
        ]
        
        # Sort by created_at descending
        all_fees.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
    except Exception as e:
        logger.error(f'Error fetching fees: {e}')
        all_fees = []
        messages.error(request, 'Error loading payment history.')
    
    return render(request, 'fees/list.html', {'fees': all_fees})

def download_receipt(request, transaction_id):
    """Download fee receipt PDF"""
    try:
        # Try to get from local database first
        try:
            fee_payment = FeePayment.objects.get(transaction_id=transaction_id)
        except FeePayment.DoesNotExist:
            # If not found locally, create a basic object from Firestore data
            firestore_data = get_document('fees', transaction_id)
            if not firestore_data:
                raise Http404("Receipt not found")
            
            # Create a basic FeePayment object for PDF generation
            class MockFeePayment:
                def __init__(self, data):
                    self.transaction_id = data.get('transaction_id')
                    self.student_id = data.get('student_id')
                    self.student_name = data.get('student_name')
                    self.student_email = data.get('student_email')
                    self.amount = float(data.get('amount', 0))
                    self.payment_mode = data.get('payment_mode')
                    self.fee_type = data.get('fee_type')
                    self.status = data.get('status')
                    self.notes = data.get('notes', '')
                    from datetime import datetime
                    self.created_at = datetime.fromisoformat(data.get('created_at'))
                    
                def get_payment_mode_display(self):
                    return self.payment_mode
                
                def get_status_display(self):
                    return self.status
                    
            fee_payment = MockFeePayment(firestore_data)
        
        return generate_fee_receipt_pdf(fee_payment)
        
    except Exception as e:
        logger.error(f'Error generating receipt: {e}')
        raise Http404("Receipt not found")
