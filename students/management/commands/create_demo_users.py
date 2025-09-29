from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = "Create demo groups and users (superadmin, admin, teacher, accountant, counselor, students). Safe to run multiple times."

    def handle(self, *args, **options):
        # Ensure groups
        admin_g, _ = Group.objects.get_or_create(name='admin')
        teacher_g, _ = Group.objects.get_or_create(name='teacher')
        accountant_g, _ = Group.objects.get_or_create(name='accountant')
        counselor_g, _ = Group.objects.get_or_create(name='counselor')

        def ensure_user(username, password, is_superuser=False, is_staff=True, groups=None):
            user, created = User.objects.get_or_create(username=username)
            # Always enforce flags and password to keep credentials predictable in dev
            user.is_superuser = is_superuser
            user.is_staff = is_staff
            user.set_password(password)
            user.save()
            if groups is not None:
                user.groups.set(groups)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated user: {username} (password/flags/groups)"))

        # Superadmin
        ensure_user('superadmin', 'admin123!', is_superuser=True, is_staff=True, groups=[admin_g])
        # Admin (non-superuser)
        ensure_user('admin', 'admin123!', is_superuser=False, is_staff=True, groups=[admin_g])
        # Teacher
        ensure_user('teacher1', 'teacher123!', is_superuser=False, is_staff=True, groups=[teacher_g])
        # Accountant
        ensure_user('account1', 'account123!', is_superuser=False, is_staff=True, groups=[accountant_g])
        # Counselor
        ensure_user('counselor1', 'counselor123!', is_superuser=False, is_staff=True, groups=[counselor_g])
        # Students (non-staff)
        ensure_user('student1', 'student123!', is_superuser=False, is_staff=False, groups=[])
        ensure_user('student2', 'student123!', is_superuser=False, is_staff=False, groups=[])

        self.stdout.write(self.style.SUCCESS('Demo users and groups are ready.'))
