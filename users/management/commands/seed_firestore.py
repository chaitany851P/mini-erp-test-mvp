from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from mini_erp.firebase_utils import (
    initialize_firebase, add_document, get_firestore_client,
    get_all_documents, delete_document
)
import json
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed user data to Firestore database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing Firestore data before seeding',
        )
        parser.add_argument(
            '--sync-all',
            action='store_true',
            help='Sync all Django users to Firestore',
        )
        parser.add_argument(
            '--roles-only',
            action='store_true',
            help='Only sync user roles to Firestore',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test Firestore connection only',
        )
    
    def handle(self, *args, **options):
        if options['test_connection']:
            self.test_firestore_connection()
            return
        
        # Initialize Firebase
        self.stdout.write('Initializing Firebase connection...')
        db = initialize_firebase()
        
        if db is None:
            self.stdout.write(
                self.style.ERROR(
                    'Failed to initialize Firebase. Please check your credentials and configuration.'
                )
            )
            return
        
        self.stdout.write(self.style.SUCCESS('Firebase connected successfully!'))
        
        if options['clear']:
            self.clear_firestore_data()
        
        if options['roles_only']:
            self.sync_user_roles()
        else:
            self.sync_users_to_firestore(sync_all=options['sync_all'])
        
        # Also seed some sample data for admissions, fees, and hostel
        self.seed_sample_data()
    
    def test_firestore_connection(self):
        """Test Firestore connection"""
        try:
            self.stdout.write('Testing Firestore connection...')
            db = initialize_firebase()
            
            if db is None:
                self.stdout.write(
                    self.style.ERROR('Failed to connect to Firestore.')
                )
                return
            
            # Try to write and read a test document
            test_data = {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'message': 'Connection test successful'
            }
            
            doc_id = add_document('connection_test', test_data, 'test_doc')
            
            if doc_id:
                self.stdout.write(
                    self.style.SUCCESS(
                        '✅ Firestore connection test successful!\n'
                        '✅ Write permissions: OK\n'
                        '✅ Document created with ID: test_doc'
                    )
                )
                
                # Clean up test document
                delete_document('connection_test', 'test_doc')
                self.stdout.write('🧹 Test document cleaned up.')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Failed to write test document to Firestore.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Firestore connection test failed: {e}')
            )
    
    def clear_firestore_data(self):
        """Clear existing Firestore data"""
        self.stdout.write('Clearing existing Firestore data...')
        
        collections_to_clear = [
            'users',
            'roles', 
            'students',
            'admissions',
            'fees',
            'hostel_requests',
            'hostel_allocations',
            'leave_applications'
        ]
        
        cleared_count = 0
        
        for collection_name in collections_to_clear:
            try:
                docs = get_all_documents(collection_name)
                for doc in docs:
                    delete_document(collection_name, doc['id'])
                    cleared_count += 1
                
                if docs:
                    self.stdout.write(f'  ✅ Cleared {len(docs)} documents from {collection_name}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Error clearing {collection_name}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'🧹 Cleared {cleared_count} documents total from Firestore')
        )
    
    def sync_user_roles(self):
        """Sync only user roles to Firestore"""
        self.stdout.write('Syncing user roles to Firestore...')
        
        users = User.objects.all()
        synced_count = 0
        
        for user in users:
            try:
                role_data = {
                    'role': user.role,
                    'email': user.email,
                    'updated_at': timezone.now().isoformat()
                }
                
                doc_id = add_document('roles', role_data, str(user.id))
                if doc_id:
                    synced_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to sync role for {user.email}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Synced {synced_count} user roles to Firestore')
        )
    
    def sync_users_to_firestore(self, sync_all=False):
        """Sync users to Firestore"""
        self.stdout.write('Syncing users to Firestore...')
        
        users = User.objects.all()
        
        synced_users = 0
        synced_roles = 0
        synced_students = 0
        
        for user in users:
            try:
                # Sync to users collection
                user_data = {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'phone': user.phone or '',
                    'address': user.address or '',
                    'is_active': user.is_active,
                    'is_email_verified': user.is_email_verified,
                    'student_id': user.student_id or '',
                    'employee_id': user.employee_id or '',
                    'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else '',
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat(),
                    'display_name': user.get_display_name(),
                    'role_display': user.get_role_display(),
                }
                
                # Sync to users collection
                user_doc_id = add_document('users', user_data, str(user.id))
                if user_doc_id:
                    synced_users += 1
                    self.stdout.write(f'  👤 {user.role}: {user.get_display_name()} ({user.email})')
                
                # Sync to roles collection (for Firebase Auth integration)
                role_data = {
                    'role': user.role,
                    'email': user.email,
                    'user_id': str(user.id),
                    'updated_at': timezone.now().isoformat()
                }
                
                role_doc_id = add_document('roles', role_data, str(user.id))
                if role_doc_id:
                    synced_roles += 1
                
                # If student, also add to students collection
                if user.is_student() and user.student_id:
                    student_data = {
                        'student_id': user.student_id,
                        'user_id': str(user.id),
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.get_display_name(),
                        'phone': user.phone or '',
                        'address': user.address or '',
                        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else '',
                        'enrollment_date': user.created_at.isoformat(),
                        'status': 'active' if user.is_active else 'inactive',
                        'credits': 0,  # Default credits
                        'gpa': 0.0,    # Default GPA
                        'semester': 1,  # Default semester
                        'updated_at': timezone.now().isoformat()
                    }
                    
                    student_doc_id = add_document('students', student_data, user.student_id)
                    if student_doc_id:
                        synced_students += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to sync user {user.email}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Firestore Sync Complete!\n'
                f'✅ Users synced: {synced_users}\n'
                f'✅ Roles synced: {synced_roles}\n'
                f'✅ Students synced: {synced_students}'
            )
        )
    
    def seed_sample_data(self):
        """Seed sample data for admissions, fees, and hostel"""
        self.stdout.write('\nSeeding sample ERP data...')
        
        # Get some students for sample data
        students = User.objects.filter(role='Student')[:5]
        
        if not students:
            self.stdout.write(self.style.WARNING('No students found for sample data'))
            return
        
        # Sample admissions data
        admissions_data = []
        for i, student in enumerate(students[:3]):
            admission = {
                'student_id': student.student_id,
                'student_name': student.get_display_name(),
                'email': student.email,
                'phone': student.phone or f'+1-555-000{i}',
                'course': 'Computer Science' if i % 2 == 0 else 'Business Administration',
                'status': 'approved',
                'application_date': (timezone.now() - timezone.timedelta(days=30+i)).isoformat(),
                'approval_date': (timezone.now() - timezone.timedelta(days=20+i)).isoformat(),
                'semester': 'Fall 2025',
                'created_at': timezone.now().isoformat()
            }
            admissions_data.append(admission)
        
        # Add admissions to Firestore
        for admission in admissions_data:
            add_document('admissions', admission, admission['student_id'])
        
        # Sample fees data
        fees_data = []
        for i, student in enumerate(students):
            fee = {
                'transaction_id': f'TXN{student.student_id}{i:03d}',
                'student_id': student.student_id,
                'student_name': student.get_display_name(),
                'student_email': student.email,
                'amount': str(5000 + (i * 500)),  # Different amounts
                'payment_mode': ['online', 'cash', 'card'][i % 3],
                'fee_type': ['tuition', 'hostel', 'library'][i % 3],
                'status': 'completed' if i % 2 == 0 else 'pending',
                'notes': f'Semester fee payment for {student.get_display_name()}',
                'due_date': (timezone.now() + timezone.timedelta(days=30)).isoformat(),
                'created_at': timezone.now().isoformat()
            }
            fees_data.append(fee)
        
        # Add fees to Firestore
        for fee in fees_data:
            add_document('fees', fee, fee['transaction_id'])
        
        # Sample hostel requests
        hostel_requests = []
        for i, student in enumerate(students[:3]):
            request = {
                'request_id': f'HST{student.student_id}{i:03d}',
                'student_id': student.student_id,
                'student_name': student.get_display_name(),
                'student_email': student.email,
                'student_phone': student.phone or f'+1-555-000{i}',
                'room_type': ['single', 'double', 'triple'][i % 3],
                'preferences': f'Ground floor preferred by {student.first_name}',
                'status': ['pending', 'approved', 'rejected'][i % 3],
                'created_at': timezone.now().isoformat(),
                'processed_at': timezone.now().isoformat() if i > 0 else ''
            }
            hostel_requests.append(request)
        
        # Add hostel requests to Firestore
        for request in hostel_requests:
            add_document('hostel_requests', request, request['request_id'])
        
        # Sample hostel allocations (for approved requests)
        hostel_allocations = []
        approved_requests = [req for req in hostel_requests if req['status'] == 'approved']
        
        for i, request in enumerate(approved_requests):
            allocation = {
                'allocation_id': f'ALLOC{request["student_id"]}{i:03d}',
                'student_id': request['student_id'],
                'student_name': request['student_name'],
                'room_number': f'R{100 + i}',
                'room_type': request['room_type'],
                'allocated_at': timezone.now().isoformat(),
                'check_in_date': (timezone.now() + timezone.timedelta(days=7)).isoformat(),
                'check_out_date': (timezone.now() + timezone.timedelta(days=365)).isoformat(),
                'is_active': True
            }
            hostel_allocations.append(allocation)
        
        # Add hostel allocations to Firestore
        for allocation in hostel_allocations:
            add_document('hostel_allocation', allocation, allocation['allocation_id'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'📊 Sample data seeded:\n'
                f'  🎓 Admissions: {len(admissions_data)}\n'
                f'  💰 Fee records: {len(fees_data)}\n'
                f'  🏠 Hostel requests: {len(hostel_requests)}\n'
                f'  🔑 Hostel allocations: {len(hostel_allocations)}'
            )
        )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 FIRESTORE SEEDING COMPLETE!'))
        self.stdout.write('='*60)
        self.stdout.write(
            'Your Firebase Firestore now contains:\n'
            '✅ All user accounts with roles\n'
            '✅ Student records with credits\n'
            '✅ Sample admission data\n'
            '✅ Sample fee records\n'
            '✅ Sample hostel requests and allocations\n\n'
            '🚀 Ready for Firebase integration!'
        )
