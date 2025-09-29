from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from mini_erp.firebase_utils import get_collection_count, get_all_documents
from admissions.models import Admission
from fees.models import FeePayment
from hostel.models import HostelCapacity, HostelAllocation
from mini_erp.auth import role_required, user_in_groups
import logging
import json
import time
from datetime import date

logger = logging.getLogger(__name__)

def admin_dashboard(request):
    """Admin dashboard with statistics"""
    stats = {}
    
    try:
        from mini_erp.firebase_utils import get_all_documents_cached, get_collection_count, start_snapshot_watch
        # Admissions count
        start_snapshot_watch('admissions')
        firestore_admissions_count = get_collection_count('admissions')
        local_admissions_count = Admission.objects.count()
        stats['admissions_count'] = max(firestore_admissions_count, local_admissions_count)
        
        # Fees total
        start_snapshot_watch('fees')
        firestore_fees = get_all_documents_cached('fees', ttl_seconds=10)
        local_fees = FeePayment.objects.filter(status='completed')
        
        firestore_total = sum(float(fee.get('amount', 0)) for fee in firestore_fees if (fee.get('status') or '').lower() == 'completed')
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
        logger.error(f'Error loading dashboard stats: {e}')
        stats = {
            'admissions_count': 0,
            'fees_total': 0,
            'hostel_occupancy': 0,
        }
    
    return render(request, 'dashboard/admin.html', {'stats': stats})

# -----------------------------
# Predictive Intervention Dashboard
# -----------------------------

def _risk_score_and_level(attendance_percent: float, overdue_fees: bool, failing_grades: bool):
    """Compute a lightweight risk score and discrete level.
    Heuristic:
    - Attendance <50% => +2, <75% => +1
    - Overdue fees => +1
    - Failing grades => +2
    Levels: 0 = Low, 1-2 = Medium, >=3 = High
    """
    score = 0
    if attendance_percent < 50:
        score += 2
    elif attendance_percent < 75:
        score += 1
    if overdue_fees:
        score += 1
    if failing_grades:
        score += 2
    if score >= 3:
        level = 'High'
    elif score >= 1:
        level = 'Medium'
    else:
        level = 'Low'
    return score, level


@login_required
def predictive_dashboard(request):
    """Render the predictive dashboard UI (cards, table, charts, alerts)."""
    # Allow admin and counselor access
    if not (request.user.is_admin() or user_in_groups(request.user, ['counselor'])):
        return HttpResponseForbidden('Access denied. Admin or counselor role required.')
    return render(request, 'dashboard/dashboard.html')


@login_required
def students_data_json(request):
    """Return aggregated at-risk list with risk_score and risk_level for table rendering."""
    # Allow admin and counselor access
    if not (request.user.is_admin() or user_in_groups(request.user, ['counselor'])):
        return HttpResponseForbidden('Access denied. Admin or counselor role required.')
    try:
        threshold = float(request.GET.get('attendance_threshold', '75'))
    except ValueError:
        threshold = 75.0

    # Reuse existing evaluator
    data = _evaluate_all_students(threshold)
    enriched = []
    for item in data:
        score, level = _risk_score_and_level(item.get('attendance_percent', 100.0), item.get('overdue_fees', False), item.get('failing_grades', False))
        enriched.append({
            **item,
            'risk_score': score,
            'risk_level': level,
        })
    return JsonResponse({'items': enriched})


@login_required
def alerts_json(request):
    """Return recent notifications for alerts panel."""
    # Allow admin and counselor access
    if not (request.user.is_admin() or user_in_groups(request.user, ['counselor'])):
        return HttpResponseForbidden('Access denied. Admin or counselor role required.')
    from mini_erp.firebase_utils import get_all_documents_cached, start_snapshot_watch
    start_snapshot_watch('notifications')
    docs = get_all_documents_cached('notifications', ttl_seconds=10)
    # Sort by created_at desc if available
    try:
        docs.sort(key=lambda d: d.get('created_at') or '', reverse=True)
    except Exception:
        pass
    return JsonResponse({'items': docs[:50]})


def _get_student_id_for_user(user):
    """Map logged-in user to their student_id. Prefer user.student_id, fallback to Admission.email mapping."""
    try:
        if not user.is_authenticated:
            return None
        sid = getattr(user, 'student_id', None)
        if sid:
            return sid
        adm = Admission.objects.filter(email=user.email).first()
        return adm.student_id if adm else None
    except Exception:
        return None


@login_required
def my_dashboard(request):
    """Student self dashboard: render same UI read-only, focused on own risk summary."""
    if user_in_groups(request.user, ['admin', 'counselor']):
        # Admin/counselor should use the predictive dashboard view
        return HttpResponseForbidden('Use the predictive dashboard view')
    return render(request, 'dashboard/dashboard.html', {'self_mode': True})


@login_required
def my_summary_json(request):
    """Return self-only risk summary for the logged-in student using cached Firestore reads."""
    sid = _get_student_id_for_user(request.user)
    if not sid:
        return JsonResponse({'error': 'No linked student_id for this user'}, status=404)
    try:
        from mini_erp.firebase_utils import get_all_documents_cached, start_snapshot_watch
        for col in ['attendance', 'fees', 'exams']:
            start_snapshot_watch(col)
        att_docs = [d for d in get_all_documents_cached('attendance', ttl_seconds=15) if d.get('student_id') == sid]
        fee_docs = [d for d in get_all_documents_cached('fees', ttl_seconds=15) if d.get('student_id') == sid]
        exam_docs = [d for d in get_all_documents_cached('exams', ttl_seconds=15) if d.get('student_id') == sid]
        # Compute attendance percent
        total = len(att_docs)
        present = sum(1 for d in att_docs if d.get('present') is True)
        attendance_percent = round((present / total) * 100.0, 2) if total > 0 else 100.0
        # Overdue fees
        from datetime import date as _date
        today = _date.today().isoformat()
        overdue = any(((fd.get('status') or 'pending').lower() != 'completed') and fd.get('due_date') and fd['due_date'] < today for fd in fee_docs)
        # Failing grades
        failing = False
        for e in exam_docs:
            try:
                score = float(e.get('score', 0))
                tot = float(e.get('total', 100) or 100)
                if (score / tot) * 100.0 < 40.0:
                    failing = True
                    break
            except Exception:
                continue
        # Score and level
        score, level = _risk_score_and_level(attendance_percent, overdue, failing)
        risk = {
            'student_id': sid,
            'attendance_percent': attendance_percent,
            'overdue_fees': overdue,
            'failing_grades': failing,
            'reasons': [
                *([f"Attendance {attendance_percent}% < 75.0%"] if attendance_percent < 75.0 else []),
                *(["Overdue fee(s)"] if overdue else []),
                *(["Failing grades"] if failing else []),
            ],
            'risk_score': score,
            'risk_level': level,
            'at_risk': score >= 1,
        }
        return JsonResponse({'item': risk})
    except Exception as e:
        return JsonResponse({'error': f'Risk calculation failed: {e}'}, status=500)


# Predictive: at-risk students

def _evaluate_all_students(attendance_threshold: float = 75.0):
    # Collect unique student_ids from Firestore collections
    ids = set()
    from mini_erp.firebase_utils import get_all_documents_cached, start_snapshot_watch
    for col in ['attendance', 'fees', 'exams']:
        try:
            start_snapshot_watch(col)
            for d in get_all_documents_cached(col, ttl_seconds=15):
                sid = d.get('student_id')
                if sid:
                    ids.add(sid)
        except Exception:
            continue
    # Compute risk per student
    from students.views import evaluate_risk  # reuse logic
    at_risk = []
    for sid in ids:
        risk = evaluate_risk(sid)
        if risk['at_risk']:
            at_risk.append(risk)
    # Sort by number of reasons desc, then lowest attendance
    at_risk.sort(key=lambda r: (-(len(r['reasons'])), r['attendance_percent']))
    return at_risk


@login_required
def at_risk_json(request):
    # Allow admin and counselor access
    if not (request.user.is_admin() or user_in_groups(request.user, ['counselor'])):
        return HttpResponseForbidden('Access denied. Admin or counselor role required.')
    try:
        threshold = float(request.GET.get('attendance_threshold', '75'))
    except ValueError:
        threshold = 75.0
    data = _evaluate_all_students(threshold)
    # Optional filters
    sid = request.GET.get('student_id')
    if sid:
        data = [d for d in data if d['student_id'] == sid]
    return JsonResponse({'items': data})


@login_required
def at_risk_stream(request):
    # Allow admin and counselor access
    if not (request.user.is_admin() or user_in_groups(request.user, ['counselor'])):
        return HttpResponseForbidden('Access denied. Admin or counselor role required.')
    # SSE stream with periodic refresh
    try:
        threshold = float(request.GET.get('attendance_threshold', '75'))
    except ValueError:
        threshold = 75.0

    def event_stream():
        for _ in range(120):  # ~10 minutes at 5s interval
            payload = json.dumps({'items': _evaluate_all_students(threshold)})
            yield f"event: at_risk\n".encode('utf-8')
            yield f"data: {payload}\n\n".encode('utf-8')
            time.sleep(5)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response


# Analytics: richer aggregates for visuals

def _in_date_range(doc_date, start, end):
    if not doc_date:
        return True
    try:
        # doc_date is ISO YYYY-MM-DD
        return (not start or doc_date >= start) and (not end or doc_date <= end)
    except Exception:
        return True


def _compute_attendance_distribution(attendance_docs, start, end):
    # Compute attendance rate per student id, then bucket
    per_student = {}
    for d in attendance_docs:
        if not _in_date_range(d.get('date'), start, end):
            continue
        sid = d.get('student_id')
        if not sid:
            continue
        present = 1 if d.get('present') else 0
        total, pres = per_student.get(sid, (0, 0))
        per_student[sid] = (total + 1, pres + present)
    buckets = {
        '<50%': 0,
        '50-75%': 0,
        '75-90%': 0,
        '90-100%': 0,
    }
    for sid, (total, pres) in per_student.items():
        if total == 0:
            continue
        pct = pres * 100.0 / total
        if pct < 50:
            buckets['<50%'] += 1
        elif pct < 75:
            buckets['50-75%'] += 1
        elif pct < 90:
            buckets['75-90%'] += 1
        else:
            buckets['90-100%'] += 1
    return buckets


def _compute_fees_metrics(fee_docs, start, end):
    status_counts = {}
    total_collected = 0.0
    total_pending = 0.0
    overdue_count = 0
    today = date.today().isoformat()
    collected_by_date = {}
    for d in fee_docs:
        due = d.get('due_date')
        if not _in_date_range(due, start, end):
            continue
        status = (d.get('status') or 'pending').lower()
        amount = float(d.get('amount', 0) or 0)
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == 'completed':
            total_collected += amount
            # approximate by due_date for timeseries (no paid_at field available)
            key = due or today
            collected_by_date[key] = collected_by_date.get(key, 0.0) + amount
        else:
            total_pending += amount
            if due and due < today:
                overdue_count += 1
    # Sort timeseries
    timeseries = sorted(collected_by_date.items())
    return {
        'status_counts': status_counts,
        'total_collected': round(total_collected, 2),
        'total_pending': round(total_pending, 2),
        'overdue_count': overdue_count,
        'collected_timeseries': [{'date': k, 'amount': v} for k, v in timeseries],
    }


def _compute_exam_distribution(exam_docs, start, end):
    buckets = {
        '0-40% (Fail)': 0,
        '40-60%': 0,
        '60-80%': 0,
        '80-100%': 0,
    }
    for d in exam_docs:
        if not _in_date_range(d.get('exam_date'), start, end):
            continue
        try:
            score = float(d.get('score', 0))
            total = float(d.get('total', 100) or 100)
            pct = (score / total) * 100.0
            if pct < 40:
                buckets['0-40% (Fail)'] += 1
            elif pct < 60:
                buckets['40-60%'] += 1
            elif pct < 80:
                buckets['60-80%'] += 1
            else:
                buckets['80-100%'] += 1
        except Exception:
            continue
    return buckets


def _compute_at_risk_reasons(attendance_docs, fee_docs, exam_docs, start, end):
    # Build student-wise flags
    students = set([d.get('student_id') for d in attendance_docs if d.get('student_id')]) \
        | set([d.get('student_id') for d in fee_docs if d.get('student_id')]) \
        | set([d.get('student_id') for d in exam_docs if d.get('student_id')])

    # Attendance percentage per student
    per_student = {}
    for d in attendance_docs:
        if not _in_date_range(d.get('date'), start, end):
            continue
        sid = d.get('student_id')
        if not sid:
            continue
        total, pres = per_student.get(sid, (0, 0))
        pres += 1 if d.get('present') else 0
        per_student[sid] = (total + 1, pres)

    today = date.today().isoformat()
    reasons_count = {
        'Attendance <75%': 0,
        'Overdue fees': 0,
        'Failing grades': 0,
    }
    at_risk = 0
    for sid in students:
        att_ok = True
        overdue = False
        failing = False
        total, pres = per_student.get(sid, (0, 0))
        if total > 0:
            pct = pres * 100.0 / total
            att_ok = pct >= 75.0
        # fees
        for f in fee_docs:
            if f.get('student_id') != sid:
                continue
            if not _in_date_range(f.get('due_date'), start, end):
                continue
            status = (f.get('status') or 'pending').lower()
            due = f.get('due_date')
            if due and due < today and status != 'completed':
                overdue = True
                break
        # exams
        for e in exam_docs:
            if e.get('student_id') != sid:
                continue
            if not _in_date_range(e.get('exam_date'), start, end):
                continue
            try:
                score = float(e.get('score', 0))
                total_e = float(e.get('total', 100) or 100)
                pct_e = (score / total_e) * 100.0
                if pct_e < 40.0:
                    failing = True
                    break
            except Exception:
                continue
        # Count
        any_risk = False
        if not att_ok:
            reasons_count['Attendance <75%'] += 1
            any_risk = True
        if overdue:
            reasons_count['Overdue fees'] += 1
            any_risk = True
        if failing:
            reasons_count['Failing grades'] += 1
            any_risk = True
        if any_risk:
            at_risk += 1
    return {
        'reasons_count': reasons_count,
        'at_risk_count': at_risk,
    }


def _compute_leaves_status(leaves_docs, start, end):
    counts = {}
    for d in leaves_docs:
        if not _in_date_range(d.get('created_at') or d.get('start_date'), start, end):
            continue
        s = (d.get('status') or 'pending').lower()
        counts[s] = counts.get(s, 0) + 1
    return counts


def _compute_hostel_status(hostel_docs, start, end):
    counts = {}
    for d in hostel_docs:
        if not _in_date_range(d.get('created_at'), start, end):
            continue
        s = (d.get('status') or 'pending').lower()
        counts[s] = counts.get(s, 0) + 1
    return counts


def _month_key(iso_date: str | None) -> str | None:
    if not iso_date:
        return None
    try:
        return iso_date[:7]  # YYYY-MM
    except Exception:
        return None


def _compute_risk_trend(attendance_docs, fee_docs, exam_docs, months: int = 6):
    """Compute monthly risk level counts (Low/Medium/High) over the last N months using current Firestore data.
    Heuristic per month mirrors _risk_score_and_level:
    - Attendance computed from that month
    - Overdue fees if due_date <= end of month and status != completed
    - Failing grades if any exam in that month with <40%
    """
    from datetime import date
    # Build last N months keys in chronological order
    today = date.today()
    keys = []
    y, m = today.year, today.month
    for _ in range(months):
        keys.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    keys = list(reversed(keys))

    # Group docs per month
    att_by_month = {k: [] for k in keys}
    fee_by_month = {k: [] for k in keys}
    exam_by_month = {k: [] for k in keys}
    for d in attendance_docs:
        mk = _month_key(d.get('date'))
        if mk in att_by_month:
            att_by_month[mk].append(d)
    for d in fee_docs:
        mk = _month_key(d.get('due_date'))
        if mk in fee_by_month:
            fee_by_month[mk].append(d)
    for d in exam_docs:
        mk = _month_key(d.get('exam_date'))
        if mk in exam_by_month:
            exam_by_month[mk].append(d)

    trend = []
    for mk in keys:
        att_docs = att_by_month.get(mk, [])
        fee_docs_m = fee_by_month.get(mk, [])
        exam_docs_m = exam_by_month.get(mk, [])
        # Student set for this month
        students = set()
        students |= {d.get('student_id') for d in att_docs if d.get('student_id')}
        students |= {d.get('student_id') for d in fee_docs_m if d.get('student_id')}
        students |= {d.get('student_id') for d in exam_docs_m if d.get('student_id')}
        # Attendance aggregates
        per_student = {}
        for d in att_docs:
            sid = d.get('student_id')
            if not sid:
                continue
            total, pres = per_student.get(sid, (0, 0))
            pres += 1 if d.get('present') else 0
            per_student[sid] = (total + 1, pres)
        # Fees overdue as of end of month
        # Compare strings YYYY-MM-DD <= mk-31 by prefix
        def is_overdue(f):
            status = (f.get('status') or 'pending').lower()
            due = f.get('due_date') or ''
            return due[:7] <= mk and status != 'completed'
        # Exams failing if any exam <40
        def is_failing(e):
            try:
                score = float(e.get('score', 0))
                total = float(e.get('total', 100) or 100)
                return (score / total) * 100.0 < 40.0
            except Exception:
                return False
        high = medium = low = 0
        for sid in students:
            total, pres = per_student.get(sid, (0, 0))
            att_pct = (pres * 100.0 / total) if total > 0 else 100.0
            overdue = any(is_overdue(f) for f in fee_docs_m if f.get('student_id') == sid)
            failing = any(is_failing(e) for e in exam_docs_m if e.get('student_id') == sid)
            score, level = _risk_score_and_level(att_pct, overdue, failing)
            if level == 'High':
                high += 1
            elif level == 'Medium':
                medium += 1
            else:
                low += 1
        trend.append({'month': mk, 'high': high, 'medium': medium, 'low': low})
    return trend


def _compute_analytics(start: str | None, end: str | None, student_id: str | None):
    # Pull docs using cached reads and start snapshot watchers to reduce reads
    from mini_erp.firebase_utils import get_all_documents_cached, start_snapshot_watch
    for col in ['attendance', 'fees', 'exams', 'leaves', 'hostel_requests']:
        start_snapshot_watch(col)
    attendance = get_all_documents_cached('attendance', ttl_seconds=15)
    fees = get_all_documents_cached('fees', ttl_seconds=15)
    exams = get_all_documents_cached('exams', ttl_seconds=15)
    leaves = get_all_documents_cached('leaves', ttl_seconds=15)
    hostel = get_all_documents_cached('hostel_requests', ttl_seconds=15)

    # Optional filter by student_id early to speed up
    if student_id:
        attendance = [d for d in attendance if d.get('student_id') == student_id]
        fees = [d for d in fees if d.get('student_id') == student_id]
        exams = [d for d in exams if d.get('student_id') == student_id]
        leaves = [d for d in leaves if d.get('student_id') == student_id]
        hostel = [d for d in hostel if d.get('student_id') == student_id]

    attendance_dist = _compute_attendance_distribution(attendance, start, end)
    fees_metrics = _compute_fees_metrics(fees, start, end)
    exam_dist = _compute_exam_distribution(exams, start, end)
    leaves_status = _compute_leaves_status(leaves, start, end)
    hostel_status = _compute_hostel_status(hostel, start, end)
    risk = _compute_at_risk_reasons(attendance, fees, exams, start, end)
    risk_trend = _compute_risk_trend(attendance, fees, exams, months=6)

    return {
        'attendance_distribution': attendance_dist,
        'fees': fees_metrics,
        'exams_distribution': exam_dist,
        'leaves_status': leaves_status,
        'hostel_status': hostel_status,
        'risk': risk,
        'risk_trend': risk_trend,
    }


@login_required
def analytics_json(request):
    # Allow admin and counselor access
    if not (request.user.is_admin() or user_in_groups(request.user, ['counselor'])):
        return HttpResponseForbidden('Access denied. Admin or counselor role required.')
    start = request.GET.get('from')
    end = request.GET.get('to')
    sid = request.GET.get('student_id')
    data = _compute_analytics(start, end, sid)
    return JsonResponse({'analytics': data})


@login_required
def analytics_stream(request):
    # Allow admin and counselor access
    if not (request.user.is_admin() or user_in_groups(request.user, ['counselor'])):
        return HttpResponseForbidden('Access denied. Admin or counselor role required.')
    start = request.GET.get('from')
    end = request.GET.get('to')
    sid = request.GET.get('student_id')

    def event_stream():
        for _ in range(120):
            payload = json.dumps({'analytics': _compute_analytics(start, end, sid)})
            yield f"event: analytics\n".encode('utf-8')
            yield f"data: {payload}\n\n".encode('utf-8')
            time.sleep(5)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response
