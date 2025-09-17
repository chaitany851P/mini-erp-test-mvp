from django.shortcuts import render
from mini_erp.firebase_utils import get_collection_count, get_all_documents
from admissions.models import Admission
from fees.models import FeePayment
from hostel.models import HostelCapacity
import logging

logger = logging.getLogger(__name__)

def home_view(request):
    """Home page with basic statistics"""
    stats = {}
    
    try:
        # Admissions count
        firestore_admissions_count = get_collection_count('admissions')
        local_admissions_count = Admission.objects.count()
        stats['admissions_count'] = max(firestore_admissions_count, local_admissions_count)
        
        # Fees total
        firestore_fees = get_all_documents('fees')
        local_fees = FeePayment.objects.filter(status='completed')
        
        firestore_total = sum(float(fee.get('amount', 0)) for fee in firestore_fees if fee.get('status') == 'completed')
        local_total = sum(float(fee.amount) for fee in local_fees)
        stats['fees_total'] = max(firestore_total, local_total)
        
        # Hostel occupancy
        try:
            capacity_data = HostelCapacity.objects.all()
            if capacity_data.exists():
                total_capacity = sum(c.total_capacity for c in capacity_data)
                total_occupied = sum(c.occupied for c in capacity_data)
                stats['hostel_occupancy'] = round((total_occupied / total_capacity * 100), 1) if total_capacity > 0 else 0
            else:
                stats['hostel_occupancy'] = 0
        except Exception as e:
            logger.error(f'Error calculating hostel occupancy: {e}')
            stats['hostel_occupancy'] = 0
        
    except Exception as e:
        logger.error(f'Error loading home page stats: {e}')
        stats = {
            'admissions_count': 0,
            'fees_total': 0,
            'hostel_occupancy': 0,
        }
    
    return render(request, 'home.html', {'stats': stats})