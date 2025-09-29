from django.core.management.base import BaseCommand
from mini_erp.firebase_utils import (
    initialize_firebase, get_all_documents, get_collection_count
)


class Command(BaseCommand):
    help = 'View data in Firestore collections'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count-only',
            action='store_true',
            help='Show only document counts for all collections',
        )
    
    def handle(self, *args, **options):
        # Initialize Firebase
        self.stdout.write('Connecting to Firestore...')
        db = initialize_firebase()
        
        if db is None:
            self.stdout.write(
                self.style.ERROR(
                    'Failed to connect to Firestore. Please check your configuration.'
                )
            )
            return
        
        self.stdout.write(self.style.SUCCESS('✅ Connected to Firestore!\n'))
        
        collections = [
            'users', 'roles', 'students', 'admissions', 'fees', 
            'hostel_requests', 'hostel_allocation', 'leave_applications'
        ]
        
        if options['count_only']:
            self.show_collection_counts(collections)
        else:
            self.show_summary(collections)
    
    def show_collection_counts(self, collections):
        """Show document counts for all collections"""
        self.stdout.write('📊 FIRESTORE COLLECTION COUNTS')
        self.stdout.write('=' * 50)
        
        total_docs = 0
        for collection_name in collections:
            count = get_collection_count(collection_name)
            total_docs += count
            
            if count > 0:
                self.stdout.write(f'  📁 {collection_name:<20} {count:>3} documents')
            else:
                self.stdout.write(f'  📂 {collection_name:<20} {count:>3} documents (empty)')
        
        self.stdout.write('=' * 50)
        self.stdout.write(f'🎯 Total documents: {total_docs}')
    
    def show_summary(self, collections):
        """Show summary of all collections with sample data"""
        self.stdout.write('📋 FIRESTORE DATA SUMMARY')
        self.stdout.write('=' * 60)
        
        for collection_name in collections:
            docs = get_all_documents(collection_name)
            count = len(docs)
            
            if count > 0:
                self.stdout.write(f'\n📁 {collection_name.upper()} ({count} documents):')
                self.stdout.write('-' * 30)
                
                # Show first few documents with key info
                for i, doc in enumerate(docs[:3]):  # Show first 3
                    if collection_name == 'users':
                        role = doc.get('role', 'Unknown')
                        name = doc.get('display_name', 'N/A')
                        email = doc.get('email', 'N/A')
                        self.stdout.write(f'  👤 {role}: {name} ({email})')
                        
                    elif collection_name == 'roles':
                        role = doc.get('role', 'Unknown')
                        email = doc.get('email', 'N/A')
                        self.stdout.write(f'  🔐 {role}: {email}')
                        
                    elif collection_name == 'students':
                        student_id = doc.get('student_id', 'N/A')
                        full_name = doc.get('full_name', 'N/A')
                        credits = doc.get('credits', 0)
                        self.stdout.write(f'  🎓 {student_id}: {full_name} (Credits: {credits})')
                        
                    elif collection_name == 'admissions':
                        student_id = doc.get('student_id', 'N/A')
                        student_name = doc.get('student_name', 'N/A')
                        course = doc.get('course', 'N/A')
                        status = doc.get('status', 'N/A')
                        self.stdout.write(f'  📝 {student_id}: {student_name} - {course} ({status})')
                        
                    elif collection_name == 'fees':
                        txn_id = doc.get('transaction_id', 'N/A')
                        amount = doc.get('amount', '0')
                        fee_type = doc.get('fee_type', 'N/A')
                        status = doc.get('status', 'N/A')
                        self.stdout.write(f'  💰 {txn_id}: ${amount} - {fee_type} ({status})')
                        
                    elif collection_name == 'hostel_requests':
                        req_id = doc.get('request_id', 'N/A')
                        student_name = doc.get('student_name', 'N/A')
                        room_type = doc.get('room_type', 'N/A')
                        status = doc.get('status', 'N/A')
                        self.stdout.write(f'  🏠 {req_id}: {student_name} - {room_type} ({status})')
                        
                    elif collection_name == 'hostel_allocation':
                        alloc_id = doc.get('allocation_id', 'N/A')
                        student_name = doc.get('student_name', 'N/A')
                        room_number = doc.get('room_number', 'N/A')
                        room_type = doc.get('room_type', 'N/A')
                        self.stdout.write(f'  🔑 {alloc_id}: {student_name} - Room {room_number} ({room_type})')
                        
                    else:
                        # Generic display
                        key_field = next((k for k in ['name', 'title', 'id'] if k in doc), list(doc.keys())[0])
                        self.stdout.write(f'  📄 {key_field}: {doc.get(key_field, "N/A")}')
                
                if count > 3:
                    self.stdout.write(f'  ... and {count - 3} more documents')
            else:
                self.stdout.write(f'\n📂 {collection_name.upper()}: Empty')
        
        self.stdout.write('\n' + '=' * 60)
        total_docs = sum(get_collection_count(c) for c in collections)
        self.stdout.write(f'🎯 Total documents across all collections: {total_docs}')