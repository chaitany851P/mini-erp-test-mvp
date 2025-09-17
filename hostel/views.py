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
    """List all hostel requests"""
    requests = HostelRequest.objects.all()
    return render(request, 'hostel/requests.html', {'requests': requests})

def hostel_allocations(request):
    """List all hostel allocations"""
    allocations = HostelAllocation.objects.filter(is_active=True)
    return render(request, 'hostel/allocations.html', {'allocations': allocations})
