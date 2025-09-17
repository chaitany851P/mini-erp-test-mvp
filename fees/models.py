from django.db import models
from django.utils import timezone
import uuid

# Create your models here.
class FeePayment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True)
    student_id = models.CharField(max_length=20)
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    fee_type = models.CharField(max_length=100)  # Tuition, Hostel, Exam, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    receipt_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.student_id} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN{str(uuid.uuid4().int)[:10]}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
