from django.core.management.base import BaseCommand
from mini_erp.firebase_utils import (
    initialize_firebase, get_all_documents, get_collection_count
)
import json


class Command(BaseCommand):
    help = 'View data in Firestore collections'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--collection',
            type=str,
            help='Specific collection to view (users, roles, students, admissions, fees, hostel_requests, etc.)',
        )
        parser.add_argument(
            '--count-only',
            action='store_true',
            help='Show only document counts for all collections',
        )
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Show summary of all collections',
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
        elif options['summary']:
            self.show_summary(collections)
        elif options['collection']:
            self.show_collection_data(options['collection'])
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
                        self.stdout.write(
                            f'  👤 {doc.get("role", "Unknown")}: {doc.get("display_name", "N/A")} '
                            f'({doc.get("email", "N/A")})'
                        )
                    elif collection_name == 'roles':
                        self.stdout.write(
                            f'  🔐 {doc.get(\"role\", \"Unknown\")}: {doc.get(\"email\", \"N/A\")}'
                        )
                    elif collection_name == 'students':
                        self.stdout.write(
                            f'  🎓 {doc.get(\"student_id\", \"N/A\")}: {doc.get(\"full_name\", \"N/A\")} '\n                            f'(Credits: {doc.get(\"credits\", 0)})'
                        )
                    elif collection_name == 'admissions':
                        self.stdout.write(
                            f'  📝 {doc.get(\"student_id\", \"N/A\")}: {doc.get(\"student_name\", \"N/A\")} '\n                            f'- {doc.get(\"course\", \"N/A\")} ({doc.get(\"status\", \"N/A\")})'
                        )
                    elif collection_name == 'fees':
                        self.stdout.write(
                            f'  💰 {doc.get(\"transaction_id\", \"N/A\")}: ${doc.get(\"amount\", \"0\")} '\n                            f'- {doc.get(\"fee_type\", \"N/A\")} ({doc.get(\"status\", \"N/A\")})'
                        )
                    elif collection_name == 'hostel_requests':
                        self.stdout.write(
                            f'  🏠 {doc.get(\"request_id\", \"N/A\")}: {doc.get(\"student_name\", \"N/A\")} '\n                            f'- {doc.get(\"room_type\", \"N/A\")} ({doc.get(\"status\", \"N/A\")})'
                        )
                    elif collection_name == 'hostel_allocation':
                        self.stdout.write(
                            f'  🔑 {doc.get(\"allocation_id\", \"N/A\")}: {doc.get(\"student_name\", \"N/A\")} '\n                            f'- Room {doc.get(\"room_number\", \"N/A\")} ({doc.get(\"room_type\", \"N/A\")})'
                        )
                    else:
                        # Generic display
                        key_field = next((k for k in ['name', 'title', 'id'] if k in doc), list(doc.keys())[0])
                        self.stdout.write(f'  📄 {key_field}: {doc.get(key_field, \"N/A\")}')
                
                if count > 3:
                    self.stdout.write(f'  ... and {count - 3} more documents')
            else:
                self.stdout.write(f'\\n📂 {collection_name.upper()}: Empty')
        
        self.stdout.write('\\n' + '=' * 60)
        total_docs = sum(get_collection_count(c) for c in collections)
        self.stdout.write(f'🎯 Total documents across all collections: {total_docs}')
    
    def show_collection_data(self, collection_name):
        \"\"\"Show detailed data for a specific collection\"\"\"
        docs = get_all_documents(collection_name)
        
        if not docs:
            self.stdout.write(f'📂 Collection \"{collection_name}\" is empty or does not exist.')
            return
        
        self.stdout.write(f'📁 COLLECTION: {collection_name.upper()}')
        self.stdout.write(f'📊 Total documents: {len(docs)}')
        self.stdout.write('=' * 60)
        
        for i, doc in enumerate(docs, 1):
            self.stdout.write(f'\\n📄 Document {i}:')
            self.stdout.write('-' * 20)
            
            # Pretty print the document data
            for key, value in doc.items():
                if isinstance(value, str) and len(value) > 50:
                    # Truncate long strings
                    display_value = value[:47] + '...'
                else:
                    display_value = value
                
                self.stdout.write(f'  {key:<20}: {display_value}')
        
        self.stdout.write('\\n' + '=' * 60)