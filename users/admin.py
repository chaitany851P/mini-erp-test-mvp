from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role-based fields"""
    
    list_display = (
        'email', 'get_full_name', 'role', 'get_id_display', 
        'is_active', 'is_email_verified', 'created_at'
    )
    
    list_filter = (
        'role', 'is_active', 'is_email_verified', 'is_staff', 'is_superuser', 'created_at'
    )
    
    search_fields = (
        'email', 'first_name', 'last_name', 'student_id', 'employee_id', 'phone'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'username', 'phone', 
                'date_of_birth', 'address', 'profile_picture'
            )
        }),
        ('Role & IDs', {
            'fields': ('role', 'student_id', 'employee_id')
        }),
        ('Status', {
            'fields': (
                'is_active', 'is_email_verified', 'is_staff', 'is_superuser'
            )
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2', 'first_name', 'last_name',
                'role', 'is_active', 'is_staff'
            ),
        }),
    )
    
    ordering = ('-created_at',)
    
    def get_id_display(self, obj):
        """Display appropriate ID based on role"""
        if obj.role == 'Student' and obj.student_id:
            return obj.student_id
        elif obj.role in ['Admin', 'Faculty'] and obj.employee_id:
            return obj.employee_id
        return '-'
    get_id_display.short_description = 'ID'
    
    def get_full_name(self, obj):
        """Display full name with role badge"""
        full_name = obj.get_full_name() or obj.username
        role_colors = {
            'Admin': '#dc3545',    # Red
            'Faculty': '#fd7e14',  # Orange
            'Student': '#28a745'   # Green
        }
        color = role_colors.get(obj.role, '#6c757d')
        return format_html(
            '{} <span style="background: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            full_name, color, obj.role
        )
    get_full_name.short_description = 'Name'
    
    actions = ['verify_email', 'unverify_email', 'make_admin', 'make_faculty', 'make_student']
    
    def verify_email(self, request, queryset):
        """Mark selected users as email verified"""
        count = queryset.update(is_email_verified=True)
        self.message_user(request, f'{count} users marked as email verified.')
    verify_email.short_description = 'Mark as email verified'
    
    def unverify_email(self, request, queryset):
        """Mark selected users as email unverified"""
        count = queryset.update(is_email_verified=False)
        self.message_user(request, f'{count} users marked as email unverified.')
    unverify_email.short_description = 'Mark as email unverified'
    
    def make_admin(self, request, queryset):
        """Change selected users role to Admin"""
        count = queryset.update(role='Admin')
        self.message_user(request, f'{count} users changed to Admin role.')
    make_admin.short_description = 'Change role to Admin'
    
    def make_faculty(self, request, queryset):
        """Change selected users role to Faculty"""
        count = queryset.update(role='Faculty')
        self.message_user(request, f'{count} users changed to Faculty role.')
    make_faculty.short_description = 'Change role to Faculty'
    
    def make_student(self, request, queryset):
        """Change selected users role to Student"""
        count = queryset.update(role='Student')
        self.message_user(request, f'{count} users changed to Student role.')
    make_student.short_description = 'Change role to Student'
