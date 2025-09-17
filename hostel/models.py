from django.db import models
from django.utils import timezone
import uuid

# Create your models here.
class HostelRequest(models.Model):
    ROOM_TYPE_CHOICES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('triple', 'Triple Room'),
        ('dormitory', 'Dormitory'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    request_id = models.CharField(max_length=50, unique=True)
    student_id = models.CharField(max_length=20)
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField()
    student_phone = models.CharField(max_length=15)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    preferences = models.TextField(blank=True, help_text="Any special preferences or requirements")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.request_id} - {self.student_id} - {self.room_type}"
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"HST{str(uuid.uuid4().int)[:8]}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']

class HostelAllocation(models.Model):
    allocation_id = models.CharField(max_length=50, unique=True)
    student_id = models.CharField(max_length=20)
    student_name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=20, choices=HostelRequest.ROOM_TYPE_CHOICES)
    allocated_at = models.DateTimeField(default=timezone.now)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.allocation_id} - {self.student_id} - Room {self.room_number}"
    
    def save(self, *args, **kwargs):
        if not self.allocation_id:
            self.allocation_id = f"ALLOC{str(uuid.uuid4().int)[:8]}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-allocated_at']

class HostelCapacity(models.Model):
    room_type = models.CharField(max_length=20, choices=HostelRequest.ROOM_TYPE_CHOICES, unique=True)
    total_capacity = models.PositiveIntegerField()
    occupied = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.room_type} - {self.occupied}/{self.total_capacity}"
    
    @property
    def available(self):
        return self.total_capacity - self.occupied
    
    @property
    def occupancy_percentage(self):
        if self.total_capacity == 0:
            return 0
        return (self.occupied / self.total_capacity) * 100
    
    class Meta:
        verbose_name_plural = "Hostel Capacities"
