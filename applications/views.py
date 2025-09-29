from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import LeaveApplication, HostelApplication
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def leaves_collection_local(request):
    """Local Django model-based leave applications - fallback when Firebase is unavailable"""
    
    if request.method == 'GET':
        # Get leaves for current user only if student
        if request.user.is_student():
            leaves = LeaveApplication.objects.filter(student=request.user).order_by('-created_at')
        else:
            # Admin/Faculty can see all
            leaves = LeaveApplication.objects.all().order_by('-created_at')
        
        data = []
        for leave in leaves:
            data.append({
                'id': str(leave.id),
                'student_id': leave.student.student_id if hasattr(leave.student, 'student_id') else leave.student.username,
                'student_name': leave.student.get_display_name(),
                'start_date': leave.start_date.isoformat() if leave.start_date else None,
                'end_date': leave.end_date.isoformat() if leave.end_date else None,
                'reason': leave.reason,
                'status': leave.status,
                'created_at': leave.created_at.isoformat() if leave.created_at else None
            })
        
        return JsonResponse({'items': data})
    
    elif request.method == 'POST':
        try:
            # Parse JSON body
            data = json.loads(request.body.decode('utf-8'))
            
            # Create leave application
            leave = LeaveApplication.objects.create(
                student=request.user,
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                reason=data.get('reason', ''),
                status='pending'
            )
            
            return JsonResponse({
                'id': str(leave.id),
                'student_id': request.user.student_id if hasattr(request.user, 'student_id') else request.user.username,
                'student_name': request.user.get_display_name(),
                'start_date': leave.start_date.isoformat() if leave.start_date else None,
                'end_date': leave.end_date.isoformat() if leave.end_date else None,
                'reason': leave.reason,
                'status': leave.status,
                'created_at': leave.created_at.isoformat()
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def hostel_applications_collection_local(request):
    """Local Django model-based hostel applications - fallback when Firebase is unavailable"""
    
    if request.method == 'GET':
        # Get hostel applications for current user only if student
        if request.user.is_student():
            applications = HostelApplication.objects.filter(student=request.user).order_by('-created_at')
        else:
            # Admin/Faculty can see all
            applications = HostelApplication.objects.all().order_by('-created_at')
        
        data = []
        for app in applications:
            data.append({
                'id': str(app.id),
                'student_id': app.student.student_id if hasattr(app.student, 'student_id') else app.student.username,
                'student_name': app.student.get_display_name(),
                'student_email': app.student.email,
                'student_phone': app.student.phone if hasattr(app.student, 'phone') else '',
                'room_type': app.room_type,
                'preferences': app.preferences,
                'status': app.status,
                'created_at': app.created_at.isoformat() if app.created_at else None
            })
        
        return JsonResponse({'items': data})
    
    elif request.method == 'POST':
        try:
            # Parse JSON body
            data = json.loads(request.body.decode('utf-8'))
            
            # Create hostel application
            application = HostelApplication.objects.create(
                student=request.user,
                room_type=data.get('room_type', 'single'),
                preferences=data.get('preferences', ''),
                status='pending'
            )
            
            return JsonResponse({
                'id': str(application.id),
                'student_id': request.user.student_id if hasattr(request.user, 'student_id') else request.user.username,
                'student_name': request.user.get_display_name(),
                'student_email': request.user.email,
                'student_phone': getattr(request.user, 'phone', ''),
                'room_type': application.room_type,
                'preferences': application.preferences,
                'status': application.status,
                'created_at': application.created_at.isoformat()
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
