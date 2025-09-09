from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from riders.models import Enumerator


class Command(BaseCommand):
    help = 'Create a test enumerator for development'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='enum001', help='Username for enumerator')
        parser.add_argument('--password', type=str, default='enum123', help='Password for enumerator')
        parser.add_argument('--first_name', type=str, default='John', help='First name')
        parser.add_argument('--last_name', type=str, default='Enumerator', help='Last name')
        parser.add_argument('--phone', type=str, default='+256700000001', help='Phone number')
        parser.add_argument('--location', type=str, default='Kampala', help='Location')
        parser.add_argument('--region', type=str, default='Central', help='Assigned region')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        phone = options['phone']
        location = options['location']
        region = options['region']

        # Create or get user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"✅ Created user: {username}")
        else:
            self.stdout.write(f"👥 User already exists: {username}")

        # Create or get enumerator
        enumerator, enum_created = Enumerator.objects.get_or_create(
            user=user,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone,
                'location': location,
                'assigned_region': region,
                'status': Enumerator.ACTIVE,
                'approved_at': timezone.now()
            }
        )
        
        if enum_created:
            # Generate unique ID
            enumerator.generate_unique_id()
            self.stdout.write(f"✅ Created enumerator: {enumerator.full_name} ({enumerator.unique_id})")
        else:
            self.stdout.write(f"👤 Enumerator already exists: {enumerator.full_name} ({enumerator.unique_id})")

        self.stdout.write(self.style.SUCCESS(f"""
🏍️ Enumerator ready for testing!
   Username: {username}
   Password: {password}
   Enumerator ID: {enumerator.unique_id}
   Phone: {enumerator.phone_number}
   Location: {enumerator.location}
   Status: {enumerator.status}
        """))