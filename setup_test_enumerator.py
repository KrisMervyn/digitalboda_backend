#!/usr/bin/env python
"""
Script to create a test enumerator and verify the database setup
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from django.contrib.auth.models import User
from riders.models import Enumerator, Rider

def create_test_enumerator():
    """Create a test enumerator with ID EN-2025-0002"""
    
    # Check if enumerator already exists
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        print(f"✅ Enumerator EN-2025-0002 already exists: {enumerator.full_name}")
        return enumerator
    except Enumerator.DoesNotExist:
        pass
    
    # Create user account for enumerator
    username = 'en_2025_0002'
    try:
        user = User.objects.get(username=username)
        print(f"✅ User {username} already exists")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            password='enumerator123',  # Simple password for testing
            first_name='John',
            last_name='Enumerator',
            email='enumerator@test.com'
        )
        print(f"✅ Created user {username}")
    
    # Create enumerator profile
    enumerator = Enumerator.objects.create(
        user=user,
        unique_id='EN-2025-0002',
        first_name='John',
        last_name='Enumerator',
        phone_number='+256700000002',
        location='Kampala Central',
        assigned_region='Central Region',
        status=Enumerator.ACTIVE
    )
    
    print(f"✅ Created enumerator: {enumerator.full_name} (ID: {enumerator.unique_id})")
    return enumerator

def check_rider_assignments():
    """Check if any riders are assigned to our test enumerator"""
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        assigned_riders = enumerator.assigned_riders.all()
        pending_riders = enumerator.get_pending_riders()
        
        print(f"\n📊 Enumerator {enumerator.unique_id} Statistics:")
        print(f"   Total assigned riders: {assigned_riders.count()}")
        print(f"   Pending approval: {pending_riders.count()}")
        print(f"   Approved: {assigned_riders.filter(status=Rider.APPROVED).count()}")
        print(f"   Rejected: {assigned_riders.filter(status=Rider.REJECTED).count()}")
        
        if assigned_riders.exists():
            print(f"\n📝 Assigned Riders:")
            for rider in assigned_riders:
                print(f"   - {rider.full_name} ({rider.phone_number}) - Status: {rider.status}")
        else:
            print(f"\n⚠️  No riders assigned to {enumerator.unique_id}")
            
    except Enumerator.DoesNotExist:
        print("❌ Enumerator EN-2025-0002 not found!")

def create_test_rider():
    """Create a test rider assigned to our enumerator"""
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
    except Enumerator.DoesNotExist:
        print("❌ Enumerator not found! Run create_test_enumerator() first")
        return
    
    # Create a test rider
    test_phone = '+256700123456'
    
    try:
        rider = Rider.objects.get(phone_number=test_phone)
        print(f"✅ Test rider already exists: {rider.full_name}")
    except Rider.DoesNotExist:
        rider = Rider.objects.create(
            phone_number=test_phone,
            first_name='Test',
            last_name='Rider',
            assigned_enumerator=enumerator,
            enumerator_id_input='EN-2025-0002',
            status=Rider.PENDING_APPROVAL,
            experience_level=Rider.NEW_RIDER,
            age=25,
            location='Kampala',
            national_id_number='CF1234567890'
        )
        print(f"✅ Created test rider: {rider.full_name} assigned to {enumerator.unique_id}")
        
        # Create application
        from riders.models import RiderApplication
        from django.utils import timezone
        
        application, created = RiderApplication.objects.get_or_create(
            rider=rider,
            defaults={'submitted_at': timezone.now()}
        )
        
        if created:
            print(f"✅ Created application with reference: {application.reference_number}")
        else:
            print(f"✅ Application already exists: {application.reference_number}")

def main():
    print("🚀 Setting up test enumerator data...\n")
    
    # Create enumerator
    enumerator = create_test_enumerator()
    
    # Check current assignments
    check_rider_assignments()
    
    # Create test rider if none exist
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        if not enumerator.assigned_riders.exists():
            print(f"\n🔧 Creating test rider...")
            create_test_rider()
            
            # Check again after creating test rider
            check_rider_assignments()
    except Enumerator.DoesNotExist:
        pass
    
    print(f"\n✅ Setup complete!")
    print(f"   Enumerator login: en_2025_0002 / enumerator123")
    print(f"   Test rider phone: +256700123456")

if __name__ == '__main__':
    main()