from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.core.mail import send_mail
from django.conf import settings
from .forms import AdmissionForm
from .models import Admission
from mini_erp.firebase_utils import add_document, get_all_documents, get_document, update_document
from mini_erp.auth import role_required
import logging
from datetime import datetime, timezone

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
    
    # Compute summary counts for template (avoid fragile template math)
    status_map = {'pending': 0, 'approved': 0, 'rejected': 0}
    for a in all_admissions:
        s = (a.get('status') or '').lower()
        if s in status_map:
            status_map[s] += 1
    context = {
        'admissions': all_admissions,
        'pending_count': status_map['pending'],
        'approved_count': status_map['approved'],
        'rejected_count': status_map['rejected'],
    }
    return render(request, 'admissions/list.html', context)

@role_required(['admin', 'counselor'])
def approve_admission(request, student_id: str):
    if request.method != 'POST':
        return redirect('admissions:detail', student_id=student_id)
    update_document('admissions', student_id, {
        'status': 'approved',
        'updated_at': datetime.now(timezone.utc).isoformat()
    })
    try:
        adm = Admission.objects.get(student_id=student_id)
        adm.status = 'approved'
        adm.save()
    except Admission.DoesNotExist:
        pass
    # Email notify
    try:
        adm = Admission.objects.get(student_id=student_id)
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            send_mail(
                subject=f"Admission approved: {student_id}",
                message=f"Dear {adm.first_name}, your admission has been approved.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[adm.email],
                fail_silently=True,
            )
    except Admission.DoesNotExist:
        pass
    messages.success(request, f'Admission {student_id} approved')
    return redirect('admissions:detail', student_id=student_id)

@role_required(['admin', 'counselor'])
def reject_admission(request, student_id: str):
    if request.method != 'POST':
        return redirect('admissions:detail', student_id=student_id)
    update_document('admissions', student_id, {
        'status': 'rejected',
        'updated_at': datetime.now(timezone.utc).isoformat()
    })
    try:
        adm = Admission.objects.get(student_id=student_id)
        adm.status = 'rejected'
        adm.save()
    except Admission.DoesNotExist:
        pass
    # Email notify
    try:
        adm = Admission.objects.get(student_id=student_id)
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            send_mail(
                subject=f"Admission update: {student_id}",
                message=f"Dear {adm.first_name}, your admission has been rejected.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[adm.email],
                fail_silently=True,
            )
    except Admission.DoesNotExist:
        pass
    messages.info(request, f'Admission {student_id} rejected')
    return redirect('admissions:detail', student_id=student_id)

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

@role_required(['admin', 'counselor'])
def manage_admissions_page(request):
    """Admin/Counselor view to approve/reject admissions inline"""
    # Reuse admission_list data aggregation
    return admission_list(request)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.core.mail import send_mail
from django.conf import settings
from .forms import AdmissionForm
from .models import Admission
from mini_erp.firebase_utils import add_document, get_all_documents, get_document, update_document
from mini_erp.auth import role_required
import logging
from datetime import datetime, timezone

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
    
    # Compute summary counts for template (avoid fragile template math)
    status_map = {'pending': 0, 'approved': 0, 'rejected': 0}
    for a in all_admissions:
        s = (a.get('status') or '').lower()
        if s in status_map:
            status_map[s] += 1
    context = {
        'admissions': all_admissions,
        'pending_count': status_map['pending'],
        'approved_count': status_map['approved'],
        'rejected_count': status_map['rejected'],
    }
    return render(request, 'admissions/list.html', context)

@role_required(['admin', 'counselor'])
def approve_admission(request, student_id: str):
    if request.method != 'POST':
        return redirect('admissions:detail', student_id=student_id)
    # Upsert Firestore doc with approved status
    ok = update_document('admissions', student_id, {
        'status': 'approved',
        'updated_at': datetime.now(timezone.utc).isoformat()
    })
    if not ok:
        # Create minimal Firestore record if it does not exist
        try:
            adm_local = Admission.objects.get(student_id=student_id)
            base = {
                'student_id': adm_local.student_id,
                'first_name': adm_local.first_name,
                'last_name': adm_local.last_name,
                'email': adm_local.email,
                'course': adm_local.course,
                'status': 'approved',
                'created_at': adm_local.created_at.isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
        except Admission.DoesNotExist:
            base = {
                'student_id': student_id,
                'status': 'approved',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
        add_document('admissions', base, student_id)
    # Update local DB if present
    try:
        adm = Admission.objects.get(student_id=student_id)
        adm.status = 'approved'
        adm.save()
    except Admission.DoesNotExist:
        pass
    # Email notify
    try:
        adm = Admission.objects.get(student_id=student_id)
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            send_mail(
                subject=f"Admission approved: {student_id}",
                message=f"Dear {adm.first_name}, your admission has been approved.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[adm.email],
                fail_silently=True,
            )
    except Admission.DoesNotExist:
        pass
    messages.success(request, f'Admission {student_id} approved')
    return redirect('admissions:detail', student_id=student_id)

@role_required(['admin', 'counselor'])
def reject_admission(request, student_id: str):
    if request.method != 'POST':
        return redirect('admissions:detail', student_id=student_id)
    # Upsert Firestore doc with rejected status
    ok = update_document('admissions', student_id, {
        'status': 'rejected',
        'updated_at': datetime.now(timezone.utc).isoformat()
    })
    if not ok:
        try:
            adm_local = Admission.objects.get(student_id=student_id)
            base = {
                'student_id': adm_local.student_id,
                'first_name': adm_local.first_name,
                'last_name': adm_local.last_name,
                'email': adm_local.email,
                'course': adm_local.course,
                'status': 'rejected',
                'created_at': adm_local.created_at.isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
        except Admission.DoesNotExist:
            base = {
                'student_id': student_id,
                'status': 'rejected',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
        add_document('admissions', base, student_id)
    # Update local DB if present
    try:
        adm = Admission.objects.get(student_id=student_id)
        adm.status = 'rejected'
        adm.save()
    except Admission.DoesNotExist:
        pass
    # Email notify
    try:
        adm = Admission.objects.get(student_id=student_id)
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            send_mail(
                subject=f"Admission update: {student_id}",
                message=f"Dear {adm.first_name}, your admission has been rejected.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[adm.email],
                fail_silently=True,
            )
    except Admission.DoesNotExist:
        pass
    messages.info(request, f'Admission {student_id} rejected')
    return redirect('admissions:detail', student_id=student_id)

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


def admission_lookup_api(request, student_id: str):
    """Return minimal student info by student_id for form auto-fill (JSON)."""
    from django.http import JsonResponse
    try:
        # Try Firestore admissions first for latest course mapping
        data = get_document('admissions', student_id)
        if not data:
            try:
                adm = Admission.objects.get(student_id=student_id)
                data = {
                    'student_id': adm.student_id,
                    'first_name': adm.first_name,
                    'last_name': adm.last_name,
                    'email': adm.email,
                    'phone': adm.phone,
                    'course': adm.course,
                }
            except Admission.DoesNotExist:
                return JsonResponse({'error': 'Not found'}, status=404)
        # Normalize name and email for UI
        full_name = f"{data.get('first_name','').strip()} {data.get('last_name','').strip()}".strip()
        return JsonResponse({
            'student_id': data.get('student_id'),
            'student_name': full_name,
            'student_email': data.get('email'),
            'phone': data.get('phone'),
            'course': data.get('course'),
        })
    except Exception as e:
        logger.error(f'lookup api error: {e}')
        from django.http import JsonResponse
        return JsonResponse({'error': 'Lookup failed'}, status=500)
