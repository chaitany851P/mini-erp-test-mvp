from django import forms
from .models import Admission
import uuid

class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 
                 'gender', 'address', 'course']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter full address'
            }),
            'course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course name'
            }),
        }
    
    def save(self, commit=True):
        admission = super().save(commit=False)
        if not admission.student_id:
            # Generate unique student ID
            admission.student_id = f"STD{str(uuid.uuid4().int)[:8]}"
        if commit:
            admission.save()
        return admission