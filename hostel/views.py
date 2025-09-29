from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import HostelRequestForm
from .models import HostelRequest, HostelAllocation

def hostel_request(request):
    """Hostel room request form"""
    if request.method == 'POST':
        form = HostelRequestForm(request.POST)
        if form.is_valid():
            hostel_request = form.save()
            messages.success(request, f'Hostel request submitted successfully! Request ID: {hostel_request.request_id}')
            return redirect('hostel:requests')
    else:
        form = HostelRequestForm()
    
    return render(request, 'hostel/request.html', {'form': form})

def hostel_requests(request):
    """List all hostel requests - Admin/Faculty view only"""
    from users.models import User
    # Only admin and faculty can see all requests
    if not (request.user.is_admin() or request.user.is_faculty()):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Access denied. Admin or Faculty role required.')
    
    requests = HostelRequest.objects.all()
    return render(request, 'hostel/requests.html', {'requests': requests})

def hostel_allocations(request):
    """List hostel allocations - Admin/Faculty can see all, Students see only their own"""
    from django.contrib.auth.decorators import login_required
    from users.models import User
    
    if request.user.is_admin() or request.user.is_faculty():
        # Admin and faculty can see all allocations
        allocations = HostelAllocation.objects.filter(is_active=True)
    elif request.user.is_student():
        # Students see only their own allocations
        # Match by student_id or email (depending on your data structure)
        allocations = HostelAllocation.objects.filter(
            is_active=True,
            student_id=getattr(request.user, 'student_id', None)
        )
    else:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Access denied.')
    
    return render(request, 'hostel/allocations.html', {'allocations': allocations})
