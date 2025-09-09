#!/usr/bin/env python
"""
Script to fix rider assignments to enumerators
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

def fix_assignments():
    """Fix rider assignments"""
    
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        print(f"✅ Found enumerator: {enumerator.full_name}")
    except Enumerator.DoesNotExist:
        print("❌ Enumerator EN-2025-0002 not found!")
        return
    
    # Find riders that should be assigned to this enumerator
    unassigned_riders = Rider.objects.filter(
        enumerator_id_input='EN-2025-0002',
        assigned_enumerator__isnull=True
    )
    
    print(f"📋 Found {unassigned_riders.count()} unassigned riders with enumerator ID EN-2025-0002")
    
    # Assign them
    for rider in unassigned_riders:
        rider.assigned_enumerator = enumerator
        rider.save()
        print(f"✅ Assigned {rider.full_name} to {enumerator.unique_id}")
        
        # Create application if doesn't exist
        application, created = RiderApplication.objects.get_or_create(
            rider=rider,
            defaults={'submitted_at': timezone.now()}
        )
        if created:
            print(f"   📝 Created application: {application.reference_number}")
    
    # Also check for riders that registered with this enumerator ID but aren't assigned
    all_riders_with_enum_id = Rider.objects.filter(enumerator_id_input='EN-2025-0002')
    print(f"\n📊 All riders with enumerator ID EN-2025-0002: {all_riders_with_enum_id.count()}")
    
    for rider in all_riders_with_enum_id:
        if rider.assigned_enumerator != enumerator:
            rider.assigned_enumerator = enumerator
            rider.save()
            print(f"🔧 Fixed assignment for {rider.full_name}")
        
        # Ensure they have pending approval status if they completed onboarding
        if rider.status == Rider.REGISTERED and rider.age and rider.location:
            rider.status = Rider.PENDING_APPROVAL
            rider.save()
            print(f"🔄 Updated {rider.full_name} status to PENDING_APPROVAL")
    
    # Final check
    assigned_riders = enumerator.assigned_riders.all()
    pending_riders = enumerator.get_pending_riders()
    
    print(f"\n✅ Final Statistics for {enumerator.unique_id}:")
    print(f"   Total assigned: {assigned_riders.count()}")
    print(f"   Pending approval: {pending_riders.count()}")
    
    for rider in pending_riders:
        print(f"   📝 {rider.full_name} ({rider.phone_number}) - {rider.status}")
        try:
            app = rider.application
            print(f"      Reference: {app.reference_number}")
        except RiderApplication.DoesNotExist:
            print(f"      ⚠️  No application record")

if __name__ == '__main__':
    fix_assignments()