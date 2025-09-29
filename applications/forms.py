from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import LeaveApplication, HostelApplication


class LeaveApplicationForm(forms.ModelForm):
    """Form for students to apply for leave"""
    
    class Meta:
        model = LeaveApplication
        fields = [
            'leave_type', 'start_date', 'end_date', 'reason',
            'contact_address', 'contact_phone'
        ]
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide detailed reason for leave request'
            }),
            'contact_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Address where you can be contacted during leave'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number during leave'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_start_date(self):
        """Validate start date is not in the past"""
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now().date():
            raise ValidationError('Start date cannot be in the past.')
        return start_date
    
    def clean_end_date(self):
        """Validate end date is after start date"""
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('End date must be after start date.')
            
            # Check if leave duration is reasonable (max 30 days)
            duration = (end_date - start_date).days + 1
            if duration > 30:
                raise ValidationError('Leave duration cannot exceed 30 days.')
        
        return end_date
    
    def save(self, commit=True):
        """Save with student user"""
        leave_app = super().save(commit=False)
        if self.user:
            leave_app.student = self.user
        
        if commit:
            leave_app.save()
            # Send notification email to student and admin
            leave_app.send_pending_notification()
        
        return leave_app


class HostelApplicationForm(forms.ModelForm):
    """Form for students to apply for hostel accommodation"""
    
    class Meta:
        model = HostelApplication
        fields = [
            'preferred_room_type', 'preferred_floor', 'guardian_name',
            'guardian_phone', 'guardian_address', 'medical_conditions',
            'dietary_requirements', 'roommate_preference', 'special_requests'
        ]
        widgets = {
            'preferred_room_type': forms.Select(attrs={'class': 'form-select'}),
            'preferred_floor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': 'Optional - preferred floor number'
            }),
            'guardian_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Guardian/Parent full name'
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Guardian contact number'
            }),
            'guardian_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Guardian complete address'
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any medical conditions, allergies, or health issues (Optional)'
            }),
            'dietary_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special dietary requirements (Optional)'
            }),
            'roommate_preference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preferred roommate name or specific requests (Optional)'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any other special requests or requirements (Optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make optional fields not required
        self.fields['preferred_floor'].required = False
        self.fields['medical_conditions'].required = False
        self.fields['dietary_requirements'].required = False
        self.fields['roommate_preference'].required = False
        self.fields['special_requests'].required = False
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        
        # Check if student already has an active hostel application
        if self.user and not self.instance.pk:  # Only for new applications
            existing_app = HostelApplication.objects.filter(
                student=self.user,
                status__in=['pending', 'approved']
            ).first()
            
            if existing_app:
                status_text = 'pending approval' if existing_app.is_pending else 'approved'
                raise ValidationError(
                    f'You already have a hostel application that is {status_text}. '
                    'Please contact administration if you need to make changes.'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save with student user"""
        hostel_app = super().save(commit=False)
        if self.user:
            hostel_app.student = self.user
        
        if commit:
            hostel_app.save()
            # Send notification email to student and admin
            hostel_app.send_pending_notification()
        
        return hostel_app


class AdminApprovalForm(forms.Form):
    """Form for admin to approve/reject applications"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Add comments for the student (optional for approval, recommended for rejection)'
        }),
        required=False
    )
    
    # Additional fields for hostel approval
    allocated_room = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Room number (for hostel approval)'
        }),
        required=False
    )
    
    allocated_bed = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bed number (for hostel approval)'
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.application_type = kwargs.pop('application_type', None)
        super().__init__(*args, **kwargs)
        
        # Hide room/bed fields for leave applications
        if self.application_type == 'leave':
            self.fields.pop('allocated_room', None)
            self.fields.pop('allocated_bed', None)
    
    def clean(self):
        """Validate approval form"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        comments = cleaned_data.get('comments')
        
        # Recommend comments for rejection
        if action == 'reject' and not comments:
            # Don't make it required, just recommend
            pass
        
        # For hostel approval, room number is recommended
        if (self.application_type == 'hostel' and 
            action == 'approve' and 
            not cleaned_data.get('allocated_room')):
            # Room allocation is optional but recommended
            pass
        
        return cleaned_data