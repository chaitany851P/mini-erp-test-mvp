from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """Custom User model with role-based access control"""
    
    ROLE_CHOICES = [
        ('Admin', 'Administrator'),
        ('Faculty', 'Faculty Member'),
        ('Student', 'Student'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='Student',
        help_text='User role in the system'
    )
    
    email = models.EmailField(
        unique=True, 
        help_text='Email address - must be unique'
    )
    
    is_email_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their email address'
    )
    
    student_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        unique=True,
        help_text='Unique student ID for students'
    )
    
    employee_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        unique=True,
        help_text='Unique employee ID for faculty and admin'
    )
    
    phone = models.CharField(
        max_length=15, 
        blank=True,
        help_text='Contact phone number'
    )
    
    date_of_birth = models.DateField(
        blank=True, 
        null=True,
        help_text='Date of birth'
    )
    
    address = models.TextField(
        blank=True,
        help_text='Full address'
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        help_text='Profile picture'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='Account creation timestamp'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    # Override username requirement to use email as primary identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'
    
    def get_display_name(self):
        """Return display name for the user"""
        full_name = self.get_full_name()
        return full_name if full_name else self.username
    
    def get_role_display_with_id(self):
        """Return role with appropriate ID"""
        if self.role == 'Student' and self.student_id:
            return f'{self.get_role_display()} - {self.student_id}'
        elif self.role in ['Admin', 'Faculty'] and self.employee_id:
            return f'{self.get_role_display()} - {self.employee_id}'
        return self.get_role_display()
    
    def is_admin(self):
        """Check if user is an administrator"""
        return self.role == 'Admin'
    
    def is_faculty(self):
        """Check if user is faculty"""
        return self.role == 'Faculty'
    
    def is_student(self):
        """Check if user is a student"""
        return self.role == 'Student'
    
    def can_manage_students(self):
        """Check if user can manage students"""
        return self.role in ['Admin', 'Faculty']
    
    def can_approve_applications(self):
        """Check if user can approve applications"""
        return self.role == 'Admin'
    
    def save(self, *args, **kwargs):
        # Auto-generate student/employee ID if not provided
        if not self.pk:  # New user
            if self.role == 'Student' and not self.student_id:
                # Generate student ID (STU + timestamp)
                import time
                self.student_id = f'STU{int(time.time() * 1000) % 100000:05d}'
            elif self.role in ['Admin', 'Faculty'] and not self.employee_id:
                # Generate employee ID (EMP + timestamp)
                import time
                prefix = 'ADM' if self.role == 'Admin' else 'FAC'
                self.employee_id = f'{prefix}{int(time.time() * 1000) % 100000:05d}'
        
        super().save(*args, **kwargs)
