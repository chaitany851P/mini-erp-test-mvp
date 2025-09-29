import json
from datetime import datetime, date
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.timezone import make_aware
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

from mini_erp.firebase_utils import (
    add_document,
    get_document,
    get_all_documents,
    update_document,
    delete_document,
    query_collection,
    get_firestore_client,
)
from mini_erp.auth import role_required
from admissions.models import Admission

# ------------------------------
# Student Profile (Firestore SoT)
# ------------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def profile_collection(request):
    """GET: list profiles (admin/counselor only); POST: create/update profile.
    Students can only create/update their own profile based on Admission mapping.
    Stored in collection 'students'.
    """
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        if not user_in_groups(request.user, ['admin', 'counselor']):
            # Students: return only self
            sid = _get_student_id_for_user(request.user)
            if not sid:
                return JsonResponse({'items': []})
            doc = get_document('students', sid)
            return JsonResponse({'items': [doc] if doc else []})
        # Admin/counselor: list all
        docs = get_all_documents('students')
        return JsonResponse({'items': docs})

    # POST create/update
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    # Determine target student_id
    sid = data.get('student_id')
    if not user_in_groups(request.user, ['admin', 'counselor']):
        sid = _get_student_id_for_user(request.user)
    if not sid:
        return HttpResponseBadRequest('student_id required')
    payload = {
        'student_id': sid,
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name'),
        'email': data.get('email'),
        'phone': data.get('phone'),
        'address': data.get('address'),
        'course': data.get('course'),
        'updated_at': datetime.utcnow().isoformat() + 'Z',
    }
    # Merge with Admission base info if available
    adm = Admission.objects.filter(student_id=sid).first()
    if adm:
        payload.setdefault('email', adm.email)
        payload.setdefault('first_name', adm.first_name)
        payload.setdefault('last_name', adm.last_name)
        payload.setdefault('course', adm.course)
    add_document('students', payload, sid)
    return JsonResponse({'saved': True, 'item': payload}, status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def profile_document(request, student_id: str):
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        # Admin/counselor can see any; students can view self only
        if not user_in_groups(request.user, ['admin', 'counselor']):
            my_sid = _get_student_id_for_user(request.user)
            if my_sid != student_id:
                return JsonResponse({'error': 'Forbidden'}, status=403)
        doc = get_document('students', student_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse({'item': doc})
    if request.method == 'DELETE':
        if not user_in_groups(request.user, ['admin']):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        ok = delete_document('students', student_id)
        return JsonResponse({'deleted': ok})
    # PUT update
    if not user_in_groups(request.user, ['admin', 'counselor']):
        my_sid = _get_student_id_for_user(request.user)
        if my_sid != student_id:
            return JsonResponse({'error': 'Forbidden'}, status=403)
        
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    update_data = {k: v for k, v in data.items() if k in ['first_name','last_name','email','phone','address','course']}
    update_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    ok = update_document('students', student_id, update_data)
    return JsonResponse({'updated': ok})


# ------------------------------
# Leave Management (Firestore)
# ------------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def leaves_collection(request):
    """GET: list leaves (admin/counselor see all; students see self). POST: submit leave.
    Collection: 'leaves' with fields student_id, start_date, end_date, reason, status.
    """
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        docs = get_all_documents('leaves')
        if not user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
            my_sid = _get_student_id_for_user(request.user)
            docs = [d for d in docs if d.get('student_id') == my_sid]
        return JsonResponse({'items': docs})
    # POST
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    sid = data.get('student_id')
    if not user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
        sid = _get_student_id_for_user(request.user)
    if not sid:
        return HttpResponseBadRequest('student_id required')
    doc = {
        'student_id': sid,
        'start_date': to_iso_date(data.get('start_date') or date.today()),
        'end_date': to_iso_date(data.get('end_date') or date.today()),
        'reason': data.get('reason') or '',
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    doc_id = add_document('leaves', doc)
    if doc_id:
        send_status_email(sid, 'Leave request submitted', f"Your leave request from {doc['start_date']} to {doc['end_date']} has been submitted and is pending approval.")
        return JsonResponse({'id': doc_id, **doc}, status=201)
    return HttpResponseBadRequest('Failed to submit leave')


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def leaves_document(request, doc_id: str):
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        doc = get_document('leaves', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if not user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
            my_sid = _get_student_id_for_user(request.user)
            if doc.get('student_id') != my_sid:
                return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'id': doc_id, **doc})
    if request.method == 'DELETE':
        # Allow deletion by admin or owner while pending
        doc = get_document('leaves', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if user_in_groups(request.user, ['admin']) or (doc.get('status') == 'pending' and _get_student_id_for_user(request.user) == doc.get('student_id')):
            ok = delete_document('leaves', doc_id)
            return JsonResponse({'deleted': ok})
        return JsonResponse({'error': 'Forbidden'}, status=403)
    # PUT update (e.g., status)
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    # Only admin/teacher/counselor can change status; owners can edit reason/dates if pending
    doc = get_document('leaves', doc_id) or {}
    my_sid = _get_student_id_for_user(request.user)
    update_data = {}
    if user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
        if 'status' in data:
            update_data['status'] = data['status']
    if doc.get('status') == 'pending' and doc.get('student_id') == my_sid:
        for f in ['start_date','end_date','reason']:
            if f in data:
                update_data[f] = data[f]
    if not update_data:
        return HttpResponseBadRequest('No fields to update')
    update_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    ok = update_document('leaves', doc_id, update_data)
    if ok and 'status' in update_data:
        send_status_email(doc.get('student_id'), 'Leave request updated', f"Your leave request status is now: {update_data['status']}")
    return JsonResponse({'updated': ok})


# --------------------------------
# Hostel Applications (Firestore)
# --------------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def hostel_applications_collection(request):
    """GET: list hostel applications; POST: submit new application.
    Uses 'hostel_requests' collection.
    """
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        docs = get_all_documents('hostel_requests')
        if not user_in_groups(request.user, ['admin', 'counselor']):
            my_sid = _get_student_id_for_user(request.user)
            docs = [d for d in docs if d.get('student_id') == my_sid]
        return JsonResponse({'items': docs})
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    sid = data.get('student_id')
    if not user_in_groups(request.user, ['admin', 'counselor']):
        sid = _get_student_id_for_user(request.user)
    if not sid:
        return HttpResponseBadRequest('student_id required')
    doc = {
        'student_id': sid,
        'student_name': data.get('student_name'),
        'student_email': data.get('student_email'),
        'student_phone': data.get('student_phone'),
        'room_type': data.get('room_type') or 'single',
        'preferences': data.get('preferences') or '',
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    doc_id = add_document('hostel_requests', doc)
    if doc_id:
        send_status_email(sid, 'Hostel request submitted', 'Your hostel application has been submitted and is pending review.')
        return JsonResponse({'id': doc_id, **doc}, status=201)
    return HttpResponseBadRequest('Failed to submit hostel application')


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def hostel_applications_document(request, doc_id: str):
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        doc = get_document('hostel_requests', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if not user_in_groups(request.user, ['admin', 'counselor']):
            my_sid = _get_student_id_for_user(request.user)
            if doc.get('student_id') != my_sid:
                return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'id': doc_id, **doc})
    if request.method == 'DELETE':
        doc = get_document('hostel_requests', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if user_in_groups(request.user, ['admin']) or (doc.get('status') == 'pending' and _get_student_id_for_user(request.user) == doc.get('student_id')):
            ok = delete_document('hostel_requests', doc_id)
            return JsonResponse({'deleted': ok})
        return JsonResponse({'error': 'Forbidden'}, status=403)
    # PUT update (approve/reject)
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    doc = get_document('hostel_requests', doc_id) or {}
    update_data = {}
    if user_in_groups(request.user, ['admin', 'counselor']):
        if 'status' in data:
            update_data['status'] = data['status']
        if data.get('status') == 'approved':
            # Create allocation record
            alloc = {
                'allocation_id': f"ALLOC-{doc_id}",
                'student_id': doc.get('student_id'),
                'student_name': doc.get('student_name'),
                'room_number': data.get('room_number') or 'TBD',
                'room_type': doc.get('room_type'),
                'allocated_at': datetime.utcnow().isoformat() + 'Z',
                'is_active': True,
            }
            add_document('hostel_allocation', alloc, alloc['allocation_id'])
    else:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    update_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    ok = update_document('hostel_requests', doc_id, update_data)
    if ok and 'status' in update_data:
        send_status_email(doc.get('student_id'), 'Hostel application update', f"Your hostel application status is now: {update_data['status']}")
    return JsonResponse({'updated': ok})


# ------------------------------
# Simple pages (HTML)
# ------------------------------

@login_required
def profile_page(request):
    return render(request, 'students/profile.html')

@login_required
def leaves_page(request):
    return render(request, 'students/leaves.html')

@login_required
def hostel_applications_page(request):
    return render(request, 'students/hostel_applications.html')

# Admin/Counselor pages
@role_required(['admin', 'counselor', 'teacher'])
def admin_leaves_page(request):
    return render(request, 'students/admin_leaves.html')

@role_required(['admin', 'counselor'])
def admin_hostel_page(request):
    return render(request, 'students/admin_hostel.html')

# Utilities and remaining imports are defined above.

def _get_student_id_for_user(user):
    try:
        if not getattr(user, 'is_authenticated', False):
            return None
        # Prefer user.student_id if available
        sid = getattr(user, 'student_id', None)
        if sid:
            return sid
        # Fallback to mapping by Admission email
        adm = Admission.objects.filter(email=user.email).first()
        return adm.student_id if adm else None
    except Exception:
        return None


# ------------------------------
# Student Profile (Firestore SoT)
# ------------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def profile_collection(request):
    """GET: list profiles (admin/counselor only); POST: create/update profile.
    Students can only create/update their own profile based on Admission mapping.
    Stored in collection 'students'.
    """
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        if not user_in_groups(request.user, ['admin', 'counselor']):
            # Students: return only self
            sid = _get_student_id_for_user(request.user)
            if not sid:
                return JsonResponse({'items': []})
            doc = get_document('students', sid)
            return JsonResponse({'items': [doc] if doc else []})
        # Admin/counselor: list all
        docs = get_all_documents('students')
        return JsonResponse({'items': docs})

    # POST create/update
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    # Determine target student_id
    sid = data.get('student_id')
    if not user_in_groups(request.user, ['admin', 'counselor']):
        sid = _get_student_id_for_user(request.user)
    if not sid:
        return HttpResponseBadRequest('student_id required')
    payload = {
        'student_id': sid,
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name'),
        'email': data.get('email'),
        'phone': data.get('phone'),
        'address': data.get('address'),
        'course': data.get('course'),
        'updated_at': datetime.utcnow().isoformat() + 'Z',
    }
    # Merge with Admission base info if available
    adm = Admission.objects.filter(student_id=sid).first()
    if adm:
        payload.setdefault('email', adm.email)
        payload.setdefault('first_name', adm.first_name)
        payload.setdefault('last_name', adm.last_name)
        payload.setdefault('course', adm.course)
    add_document('students', payload, sid)
    return JsonResponse({'saved': True, 'item': payload}, status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def profile_document(request, student_id: str):
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        # Admin/counselor can see any; students can view self only
        if not user_in_groups(request.user, ['admin', 'counselor']):
            my_sid = _get_student_id_for_user(request.user)
            if my_sid != student_id:
                return JsonResponse({'error': 'Forbidden'}, status=403)
        doc = get_document('students', student_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse({'item': doc})
    if request.method == 'DELETE':
        if not user_in_groups(request.user, ['admin']):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        ok = delete_document('students', student_id)
        return JsonResponse({'deleted': ok})
    # PUT update
    if not user_in_groups(request.user, ['admin', 'counselor']):
        my_sid = _get_student_id_for_user(request.user)
        if my_sid != student_id:
            return JsonResponse({'error': 'Forbidden'}, status=403)
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    update_data = {k: v for k, v in data.items() if k in ['first_name','last_name','email','phone','address','course']}
    update_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    ok = update_document('students', student_id, update_data)
    return JsonResponse({'updated': ok})


# ------------------------------
# Leave Management (Firestore)
# ------------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def leaves_collection(request):
    """GET: list leaves (admin/counselor see all; students see self). POST: submit leave.
    Collection: 'leaves' with fields student_id, start_date, end_date, reason, status.
    """
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        from mini_erp.firebase_utils import get_all_documents_cached, start_snapshot_watch
        start_snapshot_watch('leaves')
        docs = get_all_documents_cached('leaves', ttl_seconds=15)
        if not user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
            my_sid = _get_student_id_for_user(request.user)
            docs = [d for d in docs if d.get('student_id') == my_sid]
        return JsonResponse({'items': docs})
    # POST
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    sid = data.get('student_id')
    if not user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
        sid = _get_student_id_for_user(request.user)
    if not sid:
        return HttpResponseBadRequest('student_id required')
    doc = {
        'student_id': sid,
        'start_date': to_iso_date(data.get('start_date') or date.today()),
        'end_date': to_iso_date(data.get('end_date') or date.today()),
        'reason': data.get('reason') or '',
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    doc_id = add_document('leaves', doc)
    if doc_id:
        send_status_email(sid, 'Leave request submitted', f"Your leave request from {doc['start_date']} to {doc['end_date']} has been submitted and is pending approval.")
        return JsonResponse({'id': doc_id, **doc}, status=201)
    return HttpResponseBadRequest('Failed to submit leave')


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def leaves_document(request, doc_id: str):
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        doc = get_document('leaves', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if not user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
            my_sid = _get_student_id_for_user(request.user)
            if doc.get('student_id') != my_sid:
                return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'id': doc_id, **doc})
    if request.method == 'DELETE':
        # Allow deletion by admin or owner while pending
        doc = get_document('leaves', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if user_in_groups(request.user, ['admin']) or (doc.get('status') == 'pending' and _get_student_id_for_user(request.user) == doc.get('student_id')):
            ok = delete_document('leaves', doc_id)
            return JsonResponse({'deleted': ok})
        return JsonResponse({'error': 'Forbidden'}, status=403)
    # PUT update (e.g., status)
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    # Only admin/teacher/counselor can change status; owners can edit reason/dates if pending
    doc = get_document('leaves', doc_id) or {}
    my_sid = _get_student_id_for_user(request.user)
    update_data = {}
    if user_in_groups(request.user, ['admin', 'counselor', 'teacher']):
        if 'status' in data:
            update_data['status'] = data['status']
    if doc.get('status') == 'pending' and doc.get('student_id') == my_sid:
        for f in ['start_date','end_date','reason']:
            if f in data:
                update_data[f] = data[f]
    if not update_data:
        return HttpResponseBadRequest('No fields to update')
    update_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    ok = update_document('leaves', doc_id, update_data)
    if ok and 'status' in update_data:
        send_status_email(doc.get('student_id'), 'Leave request updated', f"Your leave request status is now: {update_data['status']}")
    return JsonResponse({'updated': ok})


# --------------------------------
# Hostel Applications (Firestore)
# --------------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def hostel_applications_collection(request):
    """GET: list hostel applications; POST: submit new application.
    Uses 'hostel_requests' collection.
    """
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        from mini_erp.firebase_utils import get_all_documents_cached, start_snapshot_watch
        start_snapshot_watch('hostel_requests')
        docs = get_all_documents_cached('hostel_requests', ttl_seconds=15)
        if not user_in_groups(request.user, ['admin', 'counselor']):
            my_sid = _get_student_id_for_user(request.user)
            docs = [d for d in docs if d.get('student_id') == my_sid]
        return JsonResponse({'items': docs})
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    sid = data.get('student_id')
    if not user_in_groups(request.user, ['admin', 'counselor']):
        sid = _get_student_id_for_user(request.user)
    if not sid:
        return HttpResponseBadRequest('student_id required')
    doc = {
        'student_id': sid,
        'student_name': data.get('student_name'),
        'student_email': data.get('student_email'),
        'student_phone': data.get('student_phone'),
        'room_type': data.get('room_type') or 'single',
        'preferences': data.get('preferences') or '',
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    doc_id = add_document('hostel_requests', doc)
    if doc_id:
        send_status_email(sid, 'Hostel request submitted', 'Your hostel application has been submitted and is pending review.')
        return JsonResponse({'id': doc_id, **doc}, status=201)
    return HttpResponseBadRequest('Failed to submit hostel application')


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def hostel_applications_document(request, doc_id: str):
    from mini_erp.auth import user_in_groups
    if request.method == 'GET':
        doc = get_document('hostel_requests', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if not user_in_groups(request.user, ['admin', 'counselor']):
            my_sid = _get_student_id_for_user(request.user)
            if doc.get('student_id') != my_sid:
                return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'id': doc_id, **doc})
    if request.method == 'DELETE':
        doc = get_document('hostel_requests', doc_id)
        if not doc:
            return JsonResponse({'error': 'Not found'}, status=404)
        if user_in_groups(request.user, ['admin']) or (doc.get('status') == 'pending' and _get_student_id_for_user(request.user) == doc.get('student_id')):
            ok = delete_document('hostel_requests', doc_id)
            return JsonResponse({'deleted': ok})
        return JsonResponse({'error': 'Forbidden'}, status=403)
    # PUT update (approve/reject)
    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    doc = get_document('hostel_requests', doc_id) or {}
    update_data = {}
    if user_in_groups(request.user, ['admin', 'counselor']):
        if 'status' in data:
            update_data['status'] = data['status']
        if data.get('status') == 'approved':
            # Create allocation record
            alloc = {
                'allocation_id': f"ALLOC-{doc_id}",
                'student_id': doc.get('student_id'),
                'student_name': doc.get('student_name'),
                'room_number': data.get('room_number') or 'TBD',
                'room_type': doc.get('room_type'),
                'allocated_at': datetime.utcnow().isoformat() + 'Z',
                'is_active': True,
            }
            add_document('hostel_allocation', alloc, alloc['allocation_id'])
    else:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    update_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    ok = update_document('hostel_requests', doc_id, update_data)
    if ok and 'status' in update_data:
        send_status_email(doc.get('student_id'), 'Hostel application update', f"Your hostel application status is now: {update_data['status']}")
    return JsonResponse({'updated': ok})


# ------------------------------
# Simple pages (HTML)
# ------------------------------

@login_required
def profile_page(request):
    return render(request, 'students/profile.html')

@login_required
def leaves_page(request):
    return render(request, 'students/leaves.html')

@login_required
def hostel_applications_page(request):
    return render(request, 'students/hostel_applications.html')

# Admin/Counselor pages
@role_required(['admin', 'counselor', 'teacher'])
def admin_leaves_page(request):
    return render(request, 'students/admin_leaves.html')

@role_required(['admin', 'counselor'])
def admin_hostel_page(request):
    return render(request, 'students/admin_hostel.html')

# Utilities

@login_required
def student_risk_summary(request):
    """Get risk summary for the current logged-in student"""
    if not request.user.is_student():
        return JsonResponse({'error': 'Student access only'}, status=403)
    
    try:
        # Get student ID
        student_id = getattr(request.user, 'student_id', None)
        if not student_id:
            return JsonResponse({
                'attendance_percent': 'N/A',
                'risk_level': 'Unknown', 
                'at_risk': False,
                'reasons': ['Student ID not found']
            })
        
        # Calculate risk using existing function
        risk_data = evaluate_risk(student_id)
        
        # Add risk level calculation
        risk_score = 0
        if risk_data.get('attendance_percent', 100) < 50:
            risk_score += 2
        elif risk_data.get('attendance_percent', 100) < 75:
            risk_score += 1
        if risk_data.get('overdue_fees', False):
            risk_score += 1
        if risk_data.get('failing_grades', False):
            risk_score += 2
            
        if risk_score >= 3:
            risk_level = 'High'
        elif risk_score >= 1:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
            
        risk_data['risk_level'] = risk_level
        risk_data['risk_score'] = risk_score
        
        return JsonResponse(risk_data)
        
    except Exception as e:
        return JsonResponse({
            'attendance_percent': 'N/A',
            'risk_level': 'Unknown',
            'at_risk': False,
            'reasons': [f'Error calculating risk: {str(e)}']
        })

def parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        return None


def to_iso_date(dt):
    if isinstance(dt, str):
        return dt
    if isinstance(dt, date):
        return dt.isoformat()
    if isinstance(dt, datetime):
        return dt.date().isoformat()
    return None


def _filter_params(request):
    return {
        'student_id': request.GET.get('student_id'),
        'from': request.GET.get('from'),
        'to': request.GET.get('to'),
        'status': request.GET.get('status'),
        'subject': request.GET.get('subject'),
    }


# Risk evaluation

ATTENDANCE_THRESHOLD = 75.0
FAIL_GRADE_PERCENT = 40.0


def get_attendance_rate(student_id: str) -> float:
    if not student_id:
        return 100.0
    docs = query_collection('attendance', 'student_id', '==', student_id)
    total = len(docs)
    if total == 0:
        return 100.0
    present = sum(1 for d in docs if d.get('present') is True)
    return round((present / total) * 100, 2)


def has_overdue_fees(student_id: str) -> bool:
    if not student_id:
        return False
    today = date.today().isoformat()
    # Overdue: due_date < today and status != completed
    docs = query_collection('fees', 'student_id', '==', student_id)
    for d in docs:
        due_date = d.get('due_date')
        status = (d.get('status') or 'pending').lower()
        if due_date and due_date < today and status != 'completed':
            return True
    return False


def is_failing(student_id: str) -> bool:
    if not student_id:
        return False
    docs = query_collection('exams', 'student_id', '==', student_id)
    failing_any = False
    for d in docs:
        try:
            score = float(d.get('score', 0))
            total = float(d.get('total', 100)) or 100.0
            percent = (score / total) * 100.0
            if percent < FAIL_GRADE_PERCENT:
                failing_any = True
                break
        except Exception:
            continue
    return failing_any


def evaluate_risk(student_id: str):
    att = get_attendance_rate(student_id)
    overdue = has_overdue_fees(student_id)
    failing = is_failing(student_id)
    reasons = []
    if att < ATTENDANCE_THRESHOLD:
        reasons.append(f"Attendance {att}% < {ATTENDANCE_THRESHOLD}%")
    if overdue:
        reasons.append("Overdue fee(s)")
    if failing:
        reasons.append("Failing grades")
    return {
        'student_id': student_id,
        'at_risk': len(reasons) > 0,
        'attendance_percent': att,
        'overdue_fees': overdue,
        'failing_grades': failing,
        'reasons': reasons,
    }


def send_alerts(student_id: str, reasons: list):
    # In-app notification
    adm = Admission.objects.filter(student_id=student_id).first()
    notif = {
        'student_id': student_id,
        'student_name': f"{adm.first_name} {adm.last_name}" if adm else '',
        'type': 'risk_alert',
        'message': f"Student {student_id} flagged: {', '.join(reasons)}",
        'reasons': reasons,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'read': False,
    }
    add_document('notifications', notif)

    # Email alert (best-effort)
    if adm and settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        try:
            send_mail(
                subject=f"Student {student_id} at-risk alert",
                message=notif['message'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[adm.email],
                fail_silently=True,
            )
        except Exception:
            pass


def send_status_email(student_id: str, subject: str, message: str):
    """Send a one-off status email to the student if email configured."""
    adm = Admission.objects.filter(student_id=student_id).first()
    if not adm:
        return
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[adm.email],
                fail_silently=True,
            )
        except Exception:
            pass


# Attendance endpoints

@csrf_exempt
@role_required(['admin', 'teacher'])
@require_http_methods(["GET", "POST"])
def attendance_collection(request):
    if request.method == 'GET':
        params = _filter_params(request)
        docs = get_all_documents('attendance')
        # Filter in memory (could be moved to Firestore composite indexes for scale)
        if params['student_id']:
            docs = [d for d in docs if d.get('student_id') == params['student_id']]
        if params['from']:
            docs = [d for d in docs if d.get('date') and d['date'] >= params['from']]
        if params['to']:
            docs = [d for d in docs if d.get('date') and d['date'] <= params['to']]
        return JsonResponse({'items': docs})

    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    # Normalize
    doc = {
        'student_id': data.get('student_id'),
        'date': to_iso_date(data.get('date') or date.today()),
        'present': bool(data.get('present', True)),
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    doc_id = add_document('attendance', doc)
    if doc_id:
        # Evaluate and alert
        result = evaluate_risk(doc['student_id'])
        if result['at_risk']:
            send_alerts(doc['student_id'], result['reasons'])
        return JsonResponse({'id': doc_id, **doc}, status=201)
    return HttpResponseBadRequest('Failed to create attendance record')


@csrf_exempt
@role_required(['admin', 'teacher'])
@require_http_methods(["GET", "PUT", "DELETE"])
def attendance_document(request, doc_id: str):
    if request.method == 'GET':
        doc = get_document('attendance', doc_id)
        if doc is None:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse({'id': doc_id, **doc})

    if request.method == 'PUT':
        data = parse_json(request)
        if data is None:
            return HttpResponseBadRequest('Invalid JSON')
        update_data = {}
        if 'present' in data:
            update_data['present'] = bool(data['present'])
        if 'date' in data:
            update_data['date'] = to_iso_date(data['date'])
        if not update_data:
            return HttpResponseBadRequest('No fields to update')
        ok = update_document('attendance', doc_id, update_data)
        if ok:
            # Evaluate and alert
            doc = get_document('attendance', doc_id) or {}
            sid = doc.get('student_id') or data.get('student_id')
            if sid:
                result = evaluate_risk(sid)
                if result['at_risk']:
                    send_alerts(sid, result['reasons'])
            return JsonResponse({'updated': True})
        return HttpResponseBadRequest('Update failed')

    # DELETE
    ok = delete_document('attendance', doc_id)
    return JsonResponse({'deleted': ok})


# Fees endpoints (Firestore-backed)

@csrf_exempt
@role_required(['admin', 'accountant'])
@require_http_methods(["GET", "POST"])
def fees_collection(request):
    if request.method == 'GET':
        params = _filter_params(request)
        docs = get_all_documents('fees')
        if params['student_id']:
            docs = [d for d in docs if d.get('student_id') == params['student_id']]
        if params['status']:
            docs = [d for d in docs if (d.get('status') or '').lower() == params['status'].lower()]
        if params['from']:
            docs = [d for d in docs if d.get('due_date') and d['due_date'] >= params['from']]
        if params['to']:
            docs = [d for d in docs if d.get('due_date') and d['due_date'] <= params['to']]
        return JsonResponse({'items': docs})

    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    doc = {
        'student_id': data.get('student_id'),
        'amount': float(data.get('amount', 0)),
        'status': (data.get('status') or 'pending').lower(),
        'fee_type': data.get('fee_type') or 'Tuition',
        'due_date': to_iso_date(data.get('due_date') or date.today()),
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    doc_id = add_document('fees', doc)
    if doc_id:
        result = evaluate_risk(doc['student_id'])
        if result['at_risk']:
            send_alerts(doc['student_id'], result['reasons'])
        return JsonResponse({'id': doc_id, **doc}, status=201)
    return HttpResponseBadRequest('Failed to create fee record')


@csrf_exempt
@role_required(['admin', 'accountant'])
@require_http_methods(["GET", "PUT", "DELETE"])
def fees_document(request, doc_id: str):
    if request.method == 'GET':
        doc = get_document('fees', doc_id)
        if doc is None:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse({'id': doc_id, **doc})

    if request.method == 'PUT':
        data = parse_json(request)
        if data is None:
            return HttpResponseBadRequest('Invalid JSON')
        update_data = {}
        if 'status' in data:
            update_data['status'] = (data['status'] or '').lower()
        if 'amount' in data:
            update_data['amount'] = float(data['amount'])
        if 'due_date' in data:
            update_data['due_date'] = to_iso_date(data['due_date'])
        if not update_data:
            return HttpResponseBadRequest('No fields to update')
        ok = update_document('fees', doc_id, update_data)
        if ok:
            doc = get_document('fees', doc_id) or {}
            sid = doc.get('student_id') or data.get('student_id')
            if sid:
                result = evaluate_risk(sid)
                if result['at_risk']:
                    send_alerts(sid, result['reasons'])
            return JsonResponse({'updated': True})
        return HttpResponseBadRequest('Update failed')

    ok = delete_document('fees', doc_id)
    return JsonResponse({'deleted': ok})


# Exams endpoints

@csrf_exempt
@role_required(['admin', 'teacher'])
@require_http_methods(["GET", "POST"])
def exams_collection(request):
    if request.method == 'GET':
        params = _filter_params(request)
        docs = get_all_documents('exams')
        if params['student_id']:
            docs = [d for d in docs if d.get('student_id') == params['student_id']]
        if params['subject']:
            docs = [d for d in docs if (d.get('subject') or '').lower() == params['subject'].lower()]
        return JsonResponse({'items': docs})

    data = parse_json(request)
    if data is None:
        return HttpResponseBadRequest('Invalid JSON')
    doc = {
        'student_id': data.get('student_id'),
        'subject': data.get('subject') or 'General',
        'score': float(data.get('score', 0)),
        'total': float(data.get('total', 100)),
        'exam_date': to_iso_date(data.get('exam_date') or date.today()),
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    doc_id = add_document('exams', doc)
    if doc_id:
        result = evaluate_risk(doc['student_id'])
        if result['at_risk']:
            send_alerts(doc['student_id'], result['reasons'])
        return JsonResponse({'id': doc_id, **doc}, status=201)
    return HttpResponseBadRequest('Failed to create exam record')


@csrf_exempt
@role_required(['admin', 'teacher'])
@require_http_methods(["GET", "PUT", "DELETE"])
def exams_document(request, doc_id: str):
    if request.method == 'GET':
        doc = get_document('exams', doc_id)
        if doc is None:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse({'id': doc_id, **doc})

    if request.method == 'PUT':
        data = parse_json(request)
        if data is None:
            return HttpResponseBadRequest('Invalid JSON')
        update_data = {}
        if 'subject' in data:
            update_data['subject'] = data['subject']
        if 'score' in data:
            update_data['score'] = float(data['score'])
        if 'total' in data:
            update_data['total'] = float(data['total'])
        if 'exam_date' in data:
            update_data['exam_date'] = to_iso_date(data['exam_date'])
        if not update_data:
            return HttpResponseBadRequest('No fields to update')
        ok = update_document('exams', doc_id, update_data)
        if ok:
            doc = get_document('exams', doc_id) or {}
            sid = doc.get('student_id') or data.get('student_id')
            if sid:
                result = evaluate_risk(sid)
                if result['at_risk']:
                    send_alerts(sid, result['reasons'])
            return JsonResponse({'updated': True})
        return HttpResponseBadRequest('Update failed')

    ok = delete_document('exams', doc_id)
    return JsonResponse({'deleted': ok})


# Notifications endpoints

@csrf_exempt
@role_required(['admin', 'teacher', 'accountant', 'counselor'])
@require_http_methods(["GET"])
def notifications_collection(request):
    docs = get_all_documents('notifications')
    unread_only = request.GET.get('unread') in ['1', 'true', 'yes']
    if unread_only:
        docs = [d for d in docs if not d.get('read')]
    return JsonResponse({'items': docs})


@csrf_exempt
@role_required(['admin', 'teacher', 'accountant', 'counselor'])
@require_http_methods(["POST"])
def notification_mark_read(request, doc_id: str):
    ok = update_document('notifications', doc_id, {'read': True})
    return JsonResponse({'updated': ok})


# Student-only minimal fees endpoint using cached Firestore data
from django.contrib.auth.decorators import login_required

@login_required
@require_http_methods(["GET"])
def my_fees(request):
    """Return the logged-in student's own fees using cached Firestore data to minimize reads."""
    try:
        sid = _get_student_id_for_user(request.user)
        if not sid:
            return JsonResponse({'items': []})
        from mini_erp.firebase_utils import get_all_documents_cached, start_snapshot_watch
        start_snapshot_watch('fees')
        docs = get_all_documents_cached('fees', ttl_seconds=15)
        items = [d for d in docs if d.get('student_id') == sid]
        return JsonResponse({'items': items})
    except Exception:
        return JsonResponse({'items': []})
