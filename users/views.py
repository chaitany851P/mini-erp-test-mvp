from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User
from .forms import CustomUserCreationForm, AddStudentForm
import logging

logger = logging.getLogger(__name__)


def custom_login_view(request):
    """Custom login view with role-based redirects"""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            try:
                # Authenticate directly using email (since USERNAME_FIELD = 'email')
                user = authenticate(request, username=email, password=password)
                
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.get_display_name()}!')
                        
                        # Redirect based on role
                        next_url = request.GET.get('next') or get_dashboard_url(user)
                        return redirect(next_url)
                    else:
                        messages.error(request, 'Your account is inactive. Please contact administrator.')
                else:
                    messages.error(request, 'Invalid email or password.')
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
    
    return render(request, 'users/login.html')


def get_dashboard_url(user):
    """Get appropriate dashboard URL based on user role"""
    if user.role == 'Admin':
        return reverse('admin_dashboard')
    elif user.role == 'Faculty':
        return reverse('faculty_dashboard')
    elif user.role == 'Student':
        return reverse('student_dashboard')
    else:
        return reverse('home')


@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not request.user.is_admin():
        return HttpResponseForbidden("Access denied. Admin role required.")
    
    # Get system statistics
    stats = {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role='Student').count(),
        'total_faculty': User.objects.filter(role='Faculty').count(),
        'total_admins': User.objects.filter(role='Admin').count(),
        'pending_applications': 0,  # Will be updated when we implement applications
    }
    
    # Get recent users
    recent_users = User.objects.order_by('-created_at')[:5]
    
    return render(request, 'users/admin_dashboard.html', {
        'stats': stats,
        'recent_users': recent_users,
    })


@login_required
def faculty_dashboard(request):
    """Faculty dashboard view"""
    if not request.user.is_faculty():
        return HttpResponseForbidden("Access denied. Faculty role required.")
    
    # Get faculty-specific data
    students_count = User.objects.filter(role='Student').count()
    
    return render(request, 'users/faculty_dashboard.html', {
        'students_count': students_count,
    })


@login_required
def student_dashboard(request):
    """Student dashboard view"""
    if not request.user.is_student():
        return HttpResponseForbidden("Access denied. Student role required.")
    
    return render(request, 'users/student_dashboard.html')


def custom_signup_view(request):
    """Custom signup view"""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/signup.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_admin())
def admin_add_student_view(request):
    """Admin view to directly add active students with welcome email"""
    if request.method == 'POST':
        form = AddStudentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the student user
                    user = form.save()
                    user.is_email_verified = True  # Auto-verify admin-added students
                    user.save()
                    
                    # Send welcome email
                    send_welcome_email(user)
                    
                    messages.success(
                        request, 
                        f'Student {user.get_display_name()} (ID: {user.student_id}) has been added successfully! '
                        f'Welcome email sent to {user.email}.'
                    )
                    return redirect('admin_dashboard')
            except Exception as e:
                logger.error(f"Error adding student: {e}")
                messages.error(request, f'Error adding student: {str(e)}')
    else:
        form = AddStudentForm()
    
    return render(request, 'users/admin_add_student.html', {'form': form})


def send_welcome_email(user):
    """Send welcome email to new student"""
    try:
        subject = f'Welcome to Mini ERP - {user.get_display_name()}!'
        message = f"""
Dear {user.get_display_name()},

Welcome to the Mini ERP System!

Your student account has been created with the following details:
- Student ID: {user.student_id}
- Email: {user.email}
- Login URL: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'}/login/

You can now:
- View and pay fees
- Apply for hostel accommodation
- Submit leave applications
- Access your student dashboard

Please login with your email and password to get started.

If you have any questions, please contact the administration.

Best regards,
Mini ERP System
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")


def custom_logout_view(request):
    """Custom logout view"""
    if request.user.is_authenticated:
        messages.info(request, f'You have been logged out successfully. Goodbye, {request.user.get_display_name()}!')
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'users/profile.html', {'user': request.user})


@login_required
def users_list_view(request):
    """List all users - Admin only"""
    if not request.user.is_admin():
        return HttpResponseForbidden("Access denied. Admin role required.")
    
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all().order_by('-created_at')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    return render(request, 'users/users_list.html', {
        'users': users,
        'role_filter': role_filter,
        'role_choices': User.ROLE_CHOICES,
    })
