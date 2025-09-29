from django.core.management.base import BaseCommand
from mini_erp.firebase_utils import add_document, get_all_documents
from users.models import User
import random
from datetime import datetime, date, timedelta
import uuid

class Command(BaseCommand):
    help = 'Seed analytics data for predictive intervention dashboard'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎲 Seeding analytics data for predictive dashboard...'))
        
        # Get existing students
        students = User.objects.filter(role='Student')
        if not students.exists():
            self.stdout.write(self.style.ERROR('❌ No students found! Run seed_users first.'))
            return
            
        self.stdout.write(f'📚 Found {students.count()} students to generate data for')
        
        # Clear existing data first
        self.stdout.write('🧹 Clearing existing analytics data...')
        
        # Generate data for each student
        for student in students:
            student_id = student.student_id or f"STU{student.id:05d}"
            self.stdout.write(f'  📊 Generating data for {student.get_display_name()} ({student_id})')
            
            # Generate attendance data (last 30 days)
            self.generate_attendance_data(student_id, student)
            
            # Generate fee records
            self.generate_fee_data(student_id, student)
            
            # Generate exam data
            self.generate_exam_data(student_id, student)
            
            # Generate leave requests
            self.generate_leave_data(student_id, student)
            
            # Generate hostel requests
            self.generate_hostel_data(student_id, student)
        
        # Generate some notifications/alerts
        self.generate_notifications()
        
        self.stdout.write(self.style.SUCCESS('✅ Analytics data seeded successfully!'))
        self.stdout.write(self.style.WARNING('🔍 You can now view the Predictive Intervention dashboard with populated data'))

    def generate_attendance_data(self, student_id, student):
        """Generate realistic attendance data for the last 30 days"""
        # Create different attendance patterns
        patterns = {
            'excellent': 0.95,  # 95% attendance
            'good': 0.85,      # 85% attendance  
            'average': 0.75,   # 75% attendance
            'poor': 0.60,      # 60% attendance (at-risk)
            'critical': 0.40   # 40% attendance (high risk)
        }
        
        # Assign pattern based on student for consistency
        pattern_key = list(patterns.keys())[hash(student_id) % len(patterns)]
        attendance_rate = patterns[pattern_key]
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday=0, Sunday=6
                is_present = random.random() < attendance_rate
                
                doc = {
                    'student_id': student_id,
                    'date': current_date.isoformat(),
                    'present': is_present,
                    'subject': random.choice(['Math', 'English', 'Science', 'History', 'Physics']),
                    'period': random.randint(1, 6),
                    'created_at': datetime.utcnow().isoformat() + 'Z'
                }
                add_document('attendance', doc)
            
            current_date += timedelta(days=1)

    def generate_fee_data(self, student_id, student):
        """Generate fee records with some overdue payments"""
        # Generate 3-4 fee records
        fee_types = ['Tuition', 'Library', 'Lab', 'Sports', 'Hostel']
        
        for i in range(random.randint(3, 4)):
            due_date = date.today() - timedelta(days=random.randint(-30, 60))
            is_overdue = due_date < date.today()
            
            # Higher chance of being overdue for 'poor' and 'critical' attendance students
            pattern_key = list(['excellent', 'good', 'average', 'poor', 'critical'])[hash(student_id) % 5]
            if pattern_key in ['poor', 'critical'] and is_overdue:
                status = 'pending' if random.random() < 0.7 else 'completed'
            else:
                status = 'completed' if random.random() < 0.8 else 'pending'
            
            amount = random.choice([500, 750, 1000, 1250, 1500])
            
            doc = {
                'student_id': student_id,
                'student_name': student.get_display_name(),
                'fee_type': random.choice(fee_types),
                'amount': amount,
                'due_date': due_date.isoformat(),
                'status': status,
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            if status == 'completed':
                doc['paid_at'] = (due_date + timedelta(days=random.randint(-5, 5))).isoformat()
            
            add_document('fees', doc)

    def generate_exam_data(self, student_id, student):
        """Generate exam scores with some failing grades"""
        subjects = ['Mathematics', 'English', 'Physics', 'Chemistry', 'Biology', 'History', 'Computer Science']
        
        # Determine performance level based on student pattern
        pattern_key = list(['excellent', 'good', 'average', 'poor', 'critical'])[hash(student_id) % 5]
        
        performance_ranges = {
            'excellent': (80, 95),
            'good': (70, 85),
            'average': (60, 75),
            'poor': (40, 65),
            'critical': (20, 50)
        }
        
        score_range = performance_ranges[pattern_key]
        
        for subject in random.sample(subjects, random.randint(4, 6)):
            score = random.randint(score_range[0], score_range[1])
            total = 100
            
            # Add some randomness - occasionally a good student might fail one subject
            if random.random() < 0.1 and pattern_key not in ['critical']:
                score = random.randint(25, 39)  # Failing grade
            
            exam_date = date.today() - timedelta(days=random.randint(1, 60))
            
            doc = {
                'student_id': student_id,
                'student_name': student.get_display_name(),
                'subject': subject,
                'score': score,
                'total': total,
                'percentage': round((score / total) * 100, 2),
                'exam_date': exam_date.isoformat(),
                'exam_type': random.choice(['Midterm', 'Final', 'Quiz', 'Assignment']),
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            add_document('exams', doc)

    def generate_leave_data(self, student_id, student):
        """Generate leave applications"""
        if random.random() < 0.4:  # 40% chance of having leave requests
            for _ in range(random.randint(1, 2)):
                start_date = date.today() + timedelta(days=random.randint(-30, 30))
                end_date = start_date + timedelta(days=random.randint(1, 5))
                
                doc = {
                    'student_id': student_id,
                    'student_name': student.get_display_name(),
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'reason': random.choice(['Medical', 'Family Emergency', 'Personal', 'Conference']),
                    'status': random.choice(['pending', 'approved', 'rejected']),
                    'created_at': datetime.utcnow().isoformat() + 'Z'
                }
                add_document('leaves', doc)

    def generate_hostel_data(self, student_id, student):
        """Generate hostel application requests"""
        if random.random() < 0.6:  # 60% chance of having hostel requests
            doc = {
                'student_id': student_id,
                'student_name': student.get_display_name(),
                'student_email': student.email,
                'student_phone': getattr(student, 'phone', '') or f"555-{random.randint(1000, 9999)}",
                'room_type': random.choice(['single', 'double', 'triple']),
                'preferences': random.choice(['Ground floor', 'Upper floor', 'Near library', 'Quiet area', '']),
                'status': random.choice(['pending', 'approved', 'rejected']),
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            add_document('hostel_requests', doc)

    def generate_notifications(self):
        """Generate sample notifications/alerts"""
        notifications = [
            {
                'student_id': 'STU00001',
                'student_name': 'John Doe',
                'message': 'Low attendance alert: Below 75% threshold',
                'type': 'attendance',
                'severity': 'high',
                'read': False,
                'created_at': datetime.utcnow().isoformat() + 'Z'
            },
            {
                'student_id': 'STU00002', 
                'student_name': 'Jane Smith',
                'message': 'Overdue fee payment: Tuition fee pending',
                'type': 'fees',
                'severity': 'medium',
                'read': False,
                'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat() + 'Z'
            },
            {
                'student_id': 'STU00003',
                'student_name': 'Bob Johnson', 
                'message': 'Failing grade alert: Mathematics below 40%',
                'type': 'academic',
                'severity': 'high',
                'read': True,
                'created_at': (datetime.utcnow() - timedelta(hours=6)).isoformat() + 'Z'
            }
        ]
        
        for notification in notifications:
            add_document('notifications', notification)