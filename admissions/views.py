from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from .forms import AdmissionForm
from .models import Admission
from mini_erp.firebase_utils import add_document, get_all_documents, get_document
import logging

logger = logging.getLogger(__name__)

def admission_apply(request):
    """Student application form"""
    if request.method == 'POST':
        form = AdmissionForm(request.POST)
        if form.is_valid():
            try:
                admission = form.save()
                
                # Save to Firestore
                admission_data = {
                    'student_id': admission.student_id,
                    'first_name': admission.first_name,
                    'last_name': admission.last_name,
                    'email': admission.email,
                    'phone': admission.phone,
                    'date_of_birth': admission.date_of_birth.isoformat(),
                    'gender': admission.gender,
                    'address': admission.address,
                    'course': admission.course,
                    'status': admission.status,
                    'created_at': admission.created_at.isoformat(),
                    'updated_at': admission.updated_at.isoformat(),
                }
                
                doc_id = add_document('admissions', admission_data, admission.student_id)
                if doc_id:
                    messages.success(request, f'Application submitted successfully! Your Student ID is: {admission.student_id}')
                    return redirect('admissions:detail', student_id=admission.student_id)
                else:
                    messages.warning(request, 'Application saved locally but failed to sync with cloud storage.')
                    return redirect('admissions:detail', student_id=admission.student_id)
                    
            except Exception as e:
                logger.error(f'Error saving admission: {e}')
                messages.error(request, 'Error submitting application. Please try again.')
    else:
        form = AdmissionForm()
    
    return render(request, 'admissions/apply.html', {'form': form})

def admission_list(request):
    """List all admissions"""
    try:
        # Get from Firestore first
        firestore_admissions = get_all_documents('admissions')
        
        # Fallback to local database
        local_admissions = Admission.objects.all()
        
        # Combine and deduplicate
        all_admissions = []
        seen_ids = set()
        
        for admission in firestore_admissions:
            if admission.get('student_id') not in seen_ids:
                all_admissions.append(admission)
                seen_ids.add(admission['student_id'])
        
        for admission in local_admissions:
            if admission.student_id not in seen_ids:
                all_admissions.append({
                    'student_id': admission.student_id,
                    'first_name': admission.first_name,
                    'last_name': admission.last_name,
                    'email': admission.email,
                    'course': admission.course,
                    'status': admission.status,
                    'created_at': admission.created_at.isoformat(),
                })
                seen_ids.add(admission.student_id)
        
        # Sort by created_at descending
        all_admissions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
    except Exception as e:
        logger.error(f'Error fetching admissions: {e}')
        all_admissions = []
        messages.error(request, 'Error loading applications.')
    
    return render(request, 'admissions/list.html', {'admissions': all_admissions})

def admission_detail(request, student_id):
    """View admission details"""
    try:
        # Try Firestore first
        admission_data = get_document('admissions', student_id)
        
        if not admission_data:
            # Fallback to local database
            try:
                admission = Admission.objects.get(student_id=student_id)
                admission_data = {
                    'student_id': admission.student_id,
                    'first_name': admission.first_name,
                    'last_name': admission.last_name,
                    'email': admission.email,
                    'phone': admission.phone,
                    'date_of_birth': admission.date_of_birth.isoformat(),
                    'gender': admission.get_gender_display(),
                    'address': admission.address,
                    'course': admission.course,
                    'status': admission.get_status_display(),
                    'created_at': admission.created_at.isoformat(),
                    'updated_at': admission.updated_at.isoformat(),
                }
            except Admission.DoesNotExist:
                raise Http404("Admission not found")
        
        if not admission_data:
            raise Http404("Admission not found")
            
        return render(request, 'admissions/detail.html', {'admission': admission_data})
        
    except Exception as e:
        logger.error(f'Error fetching admission details: {e}')
        raise Http404("Admission not found")
