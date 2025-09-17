from django import forms
from .models import HostelRequest, HostelAllocation

class HostelRequestForm(forms.ModelForm):
    class Meta:
        model = HostelRequest
        fields = ['student_id', 'student_name', 'student_email', 'student_phone', 
                 'room_type', 'preferences']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Student ID'
            }),
            'student_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Student Name'
            }),
            'student_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Email Address'
            }),
            'student_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Phone Number'
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'preferences': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special preferences or requirements (optional)'
            }),
        }

class HostelAllocationForm(forms.ModelForm):
    class Meta:
        model = HostelAllocation
        fields = ['student_id', 'student_name', 'room_number', 'room_type', 
                 'check_in_date', 'check_out_date']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'student_name': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Room Number'
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'check_in_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'check_out_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }