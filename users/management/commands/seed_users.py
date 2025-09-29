from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with 20 legit-looking users (Admin/Faculty/Student) with credits'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users before seeding',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing users...')
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Existing users cleared.'))
        
        self.stdout.write('Seeding users...')
        
        with transaction.atomic():
            # Seed data
            admins_data = [
                {
                    'username': 'admin1',
                    'email': 'admin@minierp.edu',
                    'first_name': 'John',
                    'last_name': 'Anderson',
                    'role': 'Admin',
                    'phone': '+1-555-0101',
                    'address': '123 Admin Street, University City, UC 12345',
                },
                {
                    'username': 'admin2',
                    'email': 'sarah.admin@minierp.edu',
                    'first_name': 'Sarah',
                    'last_name': 'Williams',
                    'role': 'Admin',
                    'phone': '+1-555-0102',
                    'address': '456 Management Ave, University City, UC 12346',
                },
            ]
            
            faculty_data = [
                {
                    'username': 'prof_smith',
                    'email': 'robert.smith@minierp.edu',
                    'first_name': 'Robert',
                    'last_name': 'Smith',
                    'role': 'Faculty',
                    'phone': '+1-555-0201',
                    'address': '789 Faculty Row, University City, UC 12347',
                },
                {
                    'username': 'prof_johnson',
                    'email': 'mary.johnson@minierp.edu',
                    'first_name': 'Mary',
                    'last_name': 'Johnson',
                    'role': 'Faculty',
                    'phone': '+1-555-0202',
                    'address': '321 Professor Lane, University City, UC 12348',
                },
                {
                    'username': 'prof_brown',
                    'email': 'david.brown@minierp.edu',
                    'first_name': 'David',
                    'last_name': 'Brown',
                    'role': 'Faculty',
                    'phone': '+1-555-0203',
                    'address': '654 Academic Circle, University City, UC 12349',
                },
                {
                    'username': 'prof_davis',
                    'email': 'jennifer.davis@minierp.edu',
                    'first_name': 'Jennifer',
                    'last_name': 'Davis',
                    'role': 'Faculty',
                    'phone': '+1-555-0204',
                    'address': '987 Education Blvd, University City, UC 12350',
                },
            ]
            
            # Generate realistic student data
            student_first_names = [
                'Emily', 'Michael', 'Sarah', 'James', 'Jessica', 'William', 'Ashley', 'David',
                'Amanda', 'Christopher', 'Brittany', 'Matthew', 'Stephanie', 'Joshua',
                'Megan', 'Andrew', 'Samantha', 'Daniel', 'Rachel', 'Ryan'
            ]
            
            student_last_names = [
                'Miller', 'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson',
                'White', 'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson'
            ]
            
            students_data = []
            for i in range(16):  # 16 students + 2 admins + 4 faculty = 22 total
                first_name = student_first_names[i % len(student_first_names)]
                last_name = student_last_names[i % len(student_last_names)]
                
                students_data.append({
                    'username': f'student_{first_name.lower()}_{last_name.lower()}_{i+1}',
                    'email': f'{first_name.lower()}.{last_name.lower()}{i+1}@student.minierp.edu',
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'Student',
                    'phone': f'+1-555-{random.randint(1000, 9999)}',
                    'address': f'{random.randint(100, 999)} Student Drive, Dorm {chr(65 + (i % 6))}, University City, UC 1235{i % 10}',
                    'date_of_birth': datetime(
                        year=random.randint(1998, 2005),
                        month=random.randint(1, 12),
                        day=random.randint(1, 28)
                    ).date()
                })
            
            # Create users
            created_count = 0
            
            # Create admins
            for data in admins_data:
                user = self.create_user(data, 'admin123')
                created_count += 1
                self.stdout.write(f'Created {user.role}: {user.get_display_name()} ({user.email})')
            
            # Create faculty
            for data in faculty_data:
                user = self.create_user(data, 'faculty123')
                created_count += 1
                self.stdout.write(f'Created {user.role}: {user.get_display_name()} ({user.email})')
            
            # Create students
            for data in students_data:
                user = self.create_user(data, 'student123')
                created_count += 1
                self.stdout.write(f'Created {user.role}: {user.get_display_name()} ({user.email})')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} users\n'
                    f'- {len(admins_data)} Admins\n'
                    f'- {len(faculty_data)} Faculty\n'
                    f'- {len(students_data)} Students'
                )
            )
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write('LOGIN CREDENTIALS:')
            self.stdout.write('='*60)
            self.stdout.write('All users have these default passwords:')
            self.stdout.write('- Admins: admin123')
            self.stdout.write('- Faculty: faculty123')
            self.stdout.write('- Students: student123')
            self.stdout.write('\nExample logins:')
            self.stdout.write('- admin@minierp.edu (Admin)')
            self.stdout.write('- robert.smith@minierp.edu (Faculty)')
            self.stdout.write('- emily.miller1@student.minierp.edu (Student)')
            self.stdout.write('='*60)
    
    def create_user(self, data, password):
        """Create a user with the given data and password"""
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=password,
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            date_of_birth=data.get('date_of_birth'),
            is_email_verified=True,  # All seeded users are verified
            is_active=True,
        )
        
        return user