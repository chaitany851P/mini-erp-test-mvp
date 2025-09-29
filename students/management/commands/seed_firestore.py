import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from mini_erp.firebase_utils import add_document

class Command(BaseCommand):
    help = "Seed Firestore with dummy data from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='seeds/firestore_dummy.json', help='Path to seed JSON file')

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        if not file_path.exists():
            raise CommandError(f"Seed file not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        total = 0
        for collection in ['admissions', 'attendance', 'fees', 'exams', 'notifications']:
            docs = data.get(collection, [])
            for doc in docs:
                # For admissions, use student_id as the Firestore document ID so detail page works
                if collection == 'admissions' and doc.get('student_id'):
                    add_document(collection, doc, doc.get('student_id'))
                else:
                    add_document(collection, doc)
                total += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {total} documents from {file_path}"))
