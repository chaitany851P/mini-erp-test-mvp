from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
import uuid


class LeaveApplication(models.Model):
    """Leave Application model for students to apply for leave"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('family', 'Family Emergency'),
        ('academic', 'Academic Purpose'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Student'}
    )
    
    # Leave details
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(help_text='Detailed reason for leave')
    
    # Contact during leave
    contact_address = models.TextField(
        help_text='Address where student can be contacted during leave'
    )
    contact_phone = models.CharField(
        max_length=15,
        help_text='Phone number during leave'
    )
    
    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Admin response
    admin_comments = models.TextField(
        blank=True,
        help_text='Comments from admin when approving/rejecting'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_leave_applications',
        limit_choices_to={'role__in': ['Admin', 'Faculty']}
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Application'
        verbose_name_plural = 'Leave Applications'
    
    def __str__(self):
        return f'{self.student.get_display_name()} - {self.get_leave_type_display()} ({self.status})'
    
    @property
    def duration_days(self):
        """Calculate leave duration in days"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
    
    def approve(self, admin_user, comments=''):
        """Approve the leave application"""
        self.status = 'approved'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.admin_comments = comments
        self.save()
        self.send_status_email()
    
    def reject(self, admin_user, comments=''):
        """Reject the leave application"""
        self.status = 'rejected'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.admin_comments = comments
        self.save()
        self.send_status_email()
    
    def send_status_email(self):
        """Send email notification about application status"""
        try:
            subject = f'Leave Application {self.status.title()} - {self.get_leave_type_display()}'
            
            if self.status == 'approved':
                message = f"""
Dear {self.student.get_display_name()},

Your leave application has been APPROVED.

Details:
- Leave Type: {self.get_leave_type_display()}
- Duration: {self.start_date} to {self.end_date} ({self.duration_days} days)
- Reason: {self.reason}

Admin Comments: {self.admin_comments or 'None'}
Processed by: {self.processed_by.get_display_name() if self.processed_by else 'Admin'}

Please ensure you follow all leave protocols during your absence.

Best regards,
Mini ERP Administration
                """
            else:  # rejected
                message = f"""
Dear {self.student.get_display_name()},

Your leave application has been REJECTED.

Details:
- Leave Type: {self.get_leave_type_display()}
- Duration: {self.start_date} to {self.end_date} ({self.duration_days} days)
- Reason: {self.reason}

Reason for rejection: {self.admin_comments or 'Not specified'}
Processed by: {self.processed_by.get_display_name() if self.processed_by else 'Admin'}

If you have questions, please contact the administration.

Best regards,
Mini ERP Administration
                """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.student.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't raise to avoid disrupting workflow
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send leave application status email: {e}")
    
    def send_pending_notification(self):
        """Send notification email when application is submitted"""
        try:
            # Email to student
            subject = f'Leave Application Submitted - {self.get_leave_type_display()}'
            message = f"""
Dear {self.student.get_display_name()},

Your leave application has been successfully submitted and is pending review.

Application Details:
- Leave Type: {self.get_leave_type_display()}
- Duration: {self.start_date} to {self.end_date} ({self.duration_days} days)
- Reason: {self.reason}
- Contact: {self.contact_phone}

You will receive an email notification once your application is reviewed by the administration.

Best regards,
Mini ERP System
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.student.email],
                fail_silently=True,
            )
            
            # Email to admin (get first admin user)
            from users.models import User
            admin_users = User.objects.filter(role='Admin')
            if admin_users.exists():
                admin_subject = f'New Leave Application - {self.student.get_display_name()}'
                admin_message = f"""
A new leave application has been submitted and requires review.

Student: {self.student.get_display_name()} ({self.student.email})
Student ID: {self.student.student_id}
Leave Type: {self.get_leave_type_display()}
Duration: {self.start_date} to {self.end_date} ({self.duration_days} days)
Reason: {self.reason}
Contact during leave: {self.contact_phone}

Please review and approve/reject this application in the admin panel.

Mini ERP System
                """
                
                admin_emails = [admin.email for admin in admin_users]
                send_mail(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send leave application pending notification: {e}")


class HostelApplication(models.Model):
    """Hostel Application model for students to apply for hostel accommodation"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    ROOM_TYPES = [
        ('single', 'Single Room'),
        ('double', 'Double Sharing'),
        ('triple', 'Triple Sharing'),
        ('dormitory', 'Dormitory'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Student'}
    )
    
    # Hostel preferences
    preferred_room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    preferred_floor = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text='Preferred floor number (optional)'
    )
    
    # Personal information
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    guardian_address = models.TextField()
    
    # Health and lifestyle
    medical_conditions = models.TextField(
        blank=True,
        help_text='Any medical conditions or allergies (optional)'
    )
    dietary_requirements = models.TextField(
        blank=True,
        help_text='Special dietary requirements (optional)'
    )
    
    # Additional preferences
    roommate_preference = models.CharField(
        max_length=200,
        blank=True,
        help_text='Preferred roommate name or any specific requests (optional)'
    )
    special_requests = models.TextField(
        blank=True,
        help_text='Any other special requests or requirements'
    )
    
    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Admin response
    admin_comments = models.TextField(
        blank=True,
        help_text='Comments from admin when approving/rejecting'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_hostel_applications',
        limit_choices_to={'role__in': ['Admin', 'Faculty']}
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Allocation details (filled when approved)
    allocated_room = models.CharField(
        max_length=50,
        blank=True,
        help_text='Room number allocated (filled when approved)'
    )
    allocated_bed = models.CharField(
        max_length=10,
        blank=True,
        help_text='Bed number allocated (filled when approved)'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Hostel Application'
        verbose_name_plural = 'Hostel Applications'
        # Ensure one application per student
        constraints = [
            models.UniqueConstraint(
                fields=['student'], 
                condition=models.Q(status__in=['pending', 'approved']),
                name='one_active_hostel_application_per_student'
            )
        ]
    
    def __str__(self):
        return f'{self.student.get_display_name()} - {self.get_preferred_room_type_display()} ({self.status})'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
    
    def approve(self, admin_user, comments='', room_number='', bed_number=''):
        """Approve the hostel application"""
        self.status = 'approved'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.admin_comments = comments
        self.allocated_room = room_number
        self.allocated_bed = bed_number
        self.save()
        self.send_status_email()
    
    def reject(self, admin_user, comments=''):
        """Reject the hostel application"""
        self.status = 'rejected'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.admin_comments = comments
        self.save()
        self.send_status_email()
    
    def send_status_email(self):
        """Send email notification about application status"""
        try:
            subject = f'Hostel Application {self.status.title()} - {self.get_preferred_room_type_display()}'
            
            if self.status == 'approved':
                allocation_info = ''
                if self.allocated_room:
                    allocation_info = f'\n\nAllocation Details:\n- Room: {self.allocated_room}'
                    if self.allocated_bed:
                        allocation_info += f'\n- Bed: {self.allocated_bed}'
                
                message = f"""
Dear {self.student.get_display_name()},

Congratulations! Your hostel application has been APPROVED.

Application Details:
- Room Type: {self.get_preferred_room_type_display()}
- Guardian: {self.guardian_name} ({self.guardian_phone})
{allocation_info}

Admin Comments: {self.admin_comments or 'None'}
Processed by: {self.processed_by.get_display_name() if self.processed_by else 'Admin'}

Please report to the hostel office for check-in procedures and room key collection.

Best regards,
Hostel Administration
                """
            else:  # rejected
                message = f"""
Dear {self.student.get_display_name()},

We regret to inform you that your hostel application has been REJECTED.

Application Details:
- Room Type: {self.get_preferred_room_type_display()}
- Guardian: {self.guardian_name} ({self.guardian_phone})

Reason for rejection: {self.admin_comments or 'Not specified'}
Processed by: {self.processed_by.get_display_name() if self.processed_by else 'Admin'}

If you have questions, please contact the hostel administration.

Best regards,
Hostel Administration
                """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.student.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't raise to avoid disrupting workflow
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send hostel application status email: {e}")
    
    def send_pending_notification(self):
        """Send notification email when hostel application is submitted"""
        try:
            # Email to student
            subject = f'Hostel Application Submitted - {self.get_preferred_room_type_display()}'
            message = f"""
Dear {self.student.get_display_name()},

Your hostel application has been successfully submitted and is pending review.

Application Details:
- Preferred Room Type: {self.get_preferred_room_type_display()}
- Guardian: {self.guardian_name} ({self.guardian_phone})
- Special Requests: {self.special_requests or 'None'}

You will receive an email notification once your application is reviewed by the hostel administration.

Best regards,
Hostel Administration
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.student.email],
                fail_silently=True,
            )
            
            # Email to admin
            from users.models import User
            admin_users = User.objects.filter(role='Admin')
            if admin_users.exists():
                admin_subject = f'New Hostel Application - {self.student.get_display_name()}'
                admin_message = f"""
A new hostel application has been submitted and requires review.

Student: {self.student.get_display_name()} ({self.student.email})
Student ID: {self.student.student_id}
Preferred Room Type: {self.get_preferred_room_type_display()}
Guardian: {self.guardian_name} ({self.guardian_phone})
Medical Conditions: {self.medical_conditions or 'None'}
Dietary Requirements: {self.dietary_requirements or 'None'}
Special Requests: {self.special_requests or 'None'}

Please review and approve/reject this application in the admin panel.

Hostel Administration
                """
                
                admin_emails = [admin.email for admin in admin_users]
                send_mail(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send hostel application pending notification: {e}")
