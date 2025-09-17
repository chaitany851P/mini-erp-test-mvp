from django import forms
from .models import FeePayment

class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ['student_id', 'student_name', 'student_email', 'amount', 
                 'payment_mode', 'fee_type', 'notes']
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
                'placeholder': 'Enter Student Email'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Amount',
                'step': '0.01',
                'min': '0'
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fee_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Tuition Fee, Hostel Fee, Exam Fee'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }
        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        return amount