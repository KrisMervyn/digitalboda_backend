#!/usr/bin/env python
"""
Script to create a complete test rider with proper enumerator assignment
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from django.contrib.auth.models import User
from riders.models import Enumerator, Rider, RiderApplication
from django.utils import timezone

def create_complete_test_rider():
    """Create a test rider that goes through the complete flow"""
    
    # Get the enumerator
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        print(f"✅ Found enumerator: {enumerator.full_name} ({enumerator.unique_id})")
    except Enumerator.DoesNotExist:
        print("❌ Enumerator EN-2025-0002 not found!")
        return None
    
    # Create a test rider (simulating the registration process)
    test_phone = '+256777123456'
    
    try:
        rider = Rider.objects.get(phone_number=test_phone)
        print(f"✅ Test rider already exists: {rider.full_name}")
        # Update the assignment to make sure it's correct
        rider.assigned_enumerator = enumerator
        rider.enumerator_id_input = 'EN-2025-0002'
        rider.save()
    except Rider.DoesNotExist:
        # Step 1: Registration (simulating what happens when rider registers)
        rider = Rider.objects.create(
            phone_number=test_phone,
            first_name='Test',
            last_name='Pending',
            assigned_enumerator=enumerator,
            enumerator_id_input='EN-2025-0002',
            experience_level=Rider.NEW_RIDER,
            status=Rider.REGISTERED  # Initially registered
        )
        print(f"✅ Created test rider: {rider.full_name}")
    
    # Step 2: Onboarding completion (simulating what happens after onboarding)
    rider.age = 28
    rider.location = 'Kampala Central'
    rider.national_id_number = 'CF1234567890123'
    rider.status = Rider.PENDING_APPROVAL  # Move to pending approval
    rider.save()
    print(f"✅ Updated rider to PENDING_APPROVAL status")
    
    # Step 3: Create application (simulating onboarding submission)
    application, created = RiderApplication.objects.get_or_create(
        rider=rider,
        defaults={'submitted_at': timezone.now()}
    )
    
    if created:
        print(f"✅ Created application with reference: {application.reference_number}")
    else:
        print(f"✅ Application exists: {application.reference_number}")
    
    return rider

def verify_enumerator_can_see_rider():
    """Verify that the enumerator can see the pending rider"""
    
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        
        # Check assigned riders
        all_assigned = enumerator.assigned_riders.all()
        pending_riders = enumerator.get_pending_riders()
        
        print(f"\n📊 Verification for {enumerator.unique_id}:")
        print(f"   Total assigned riders: {all_assigned.count()}")
        print(f"   Pending approval: {pending_riders.count()}")
        
        if pending_riders.exists():
            print(f"\n📝 Pending Riders:")
            for rider in pending_riders:
                print(f"   - {rider.full_name} ({rider.phone_number})")
                print(f"     Status: {rider.status}")
                print(f"     Age: {rider.age}")
                print(f"     Location: {rider.location}")
                print(f"     ID Input: {rider.enumerator_id_input}")
                print(f"     Assigned Enum: {rider.assigned_enumerator.unique_id if rider.assigned_enumerator else 'None'}")
                
                try:
                    app = rider.application
                    print(f"     Reference: {app.reference_number}")
                    print(f"     Submitted: {app.submitted_at}")
                except RiderApplication.DoesNotExist:
                    print(f"     ⚠️  No application record")
                print()
        else:
            print(f"   ⚠️  No pending riders found")
            
        return pending_riders.count() > 0
        
    except Enumerator.DoesNotExist:
        print("❌ Enumerator not found!")
        return False

def test_api_endpoints():
    """Test the API endpoints that the enumerator app will call"""
    
    print(f"\n🧪 Testing API Simulation:")
    
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        
        # Simulate getting pending riders (what the API call does)
        pending_riders = enumerator.assigned_riders.filter(status=Rider.PENDING_APPROVAL)
        
        print(f"✅ API Simulation - Pending riders: {pending_riders.count()}")
        
        if pending_riders.exists():
            rider = pending_riders.first()
            print(f"   First rider: {rider.full_name}")
            print(f"   Status check: {rider.status == Rider.PENDING_APPROVAL}")
            print(f"   Has application: {hasattr(rider, 'application')}")
            
            try:
                app = rider.application
                print(f"   Reference number: {app.reference_number}")
            except RiderApplication.DoesNotExist:
                print(f"   ❌ No application found!")
                
        return pending_riders.count() > 0
        
    except Exception as e:
        print(f"❌ API Test failed: {e}")
        return False

def main():
    print("🚀 Creating complete test rider for enumerator workflow...\n")
    
    # Create the test rider
    rider = create_complete_test_rider()
    
    if rider:
        # Verify the enumerator can see it
        can_see = verify_enumerator_can_see_rider()
        
        # Test API simulation
        api_works = test_api_endpoints()
        
        if can_see and api_works:
            print(f"\n✅ SUCCESS! Enumerator EN-2025-0002 can now see pending riders.")
            print(f"   Login credentials: en_2025_0002 / enumerator123")
            print(f"   Test rider phone: {rider.phone_number}")
        else:
            print(f"\n❌ Something went wrong. Check the assignments.")
    else:
        print(f"\n❌ Failed to create test rider")

if __name__ == '__main__':
    main()