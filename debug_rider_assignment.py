#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from riders.models import Rider, Enumerator

def debug_rider_assignment():
    print("🔍 DEBUGGING RIDER ASSIGNMENT ISSUE")
    print("=" * 50)
    
    # Check enumerator
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        print(f"✅ Enumerator found: {enumerator.full_name}")
        print(f"   ID: {enumerator.id}")
        print(f"   Unique ID: {enumerator.unique_id}")
    except Enumerator.DoesNotExist:
        print("❌ Enumerator EN-2025-0002 not found!")
        return
    
    # Check all riders
    all_riders = Rider.objects.all().order_by('-created_at')
    print(f"\n📋 ALL RIDERS ({all_riders.count()}):")
    print("-" * 30)
    
    for i, rider in enumerate(all_riders[:10], 1):
        print(f"{i}. {rider.full_name} ({rider.phone_number})")
        print(f"   Status: {rider.status}")
        print(f"   Assigned Enumerator: {rider.assigned_enumerator}")
        print(f"   Enumerator ID Input: {rider.enumerator_id_input}")
        print(f"   Reference: {rider.unique_id}")
        print()
    
    # Check riders assigned to EN-2025-0002
    assigned_riders = enumerator.assigned_riders.all()
    print(f"🔗 RIDERS ASSIGNED TO {enumerator.unique_id} ({assigned_riders.count()}):")
    print("-" * 40)
    
    if assigned_riders.exists():
        for rider in assigned_riders:
            print(f"• {rider.full_name} ({rider.phone_number}) - {rider.status}")
    else:
        print("❌ No riders assigned to this enumerator")
    
    # Check pending riders
    pending_riders = Rider.objects.filter(status=Rider.PENDING_APPROVAL)
    print(f"\n⏳ PENDING APPROVAL RIDERS ({pending_riders.count()}):")
    print("-" * 30)
    
    for rider in pending_riders:
        print(f"• {rider.full_name} ({rider.phone_number})")
        print(f"  Assigned to: {rider.assigned_enumerator}")
        print(f"  Enumerator input: {rider.enumerator_id_input}")
    
    # Check if there's a rider that should be assigned
    print(f"\n🔧 LOOKING FOR UNASSIGNED RIDERS WITH EN-2025-0002:")
    print("-" * 45)
    
    unassigned_riders = Rider.objects.filter(
        enumerator_id_input='EN-2025-0002',
        assigned_enumerator__isnull=True
    )
    
    if unassigned_riders.exists():
        print(f"❌ Found {unassigned_riders.count()} unassigned riders with EN-2025-0002")
        for rider in unassigned_riders:
            print(f"   • {rider.full_name} ({rider.phone_number})")
    else:
        print("✅ No unassigned riders found with EN-2025-0002")
    
    # Check if rider was assigned to wrong enumerator
    misassigned_riders = Rider.objects.filter(
        enumerator_id_input='EN-2025-0002'
    ).exclude(assigned_enumerator=enumerator)
    
    if misassigned_riders.exists():
        print(f"\n❌ MISASSIGNED RIDERS ({misassigned_riders.count()}):")
        for rider in misassigned_riders:
            print(f"   • {rider.full_name}: Expected EN-2025-0002 but assigned to {rider.assigned_enumerator}")
    
    return enumerator, all_riders, pending_riders

def fix_rider_assignment():
    print("\n🔧 ATTEMPTING TO FIX ASSIGNMENT ISSUES")
    print("=" * 45)
    
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        
        # Find riders who should be assigned to this enumerator
        riders_to_fix = Rider.objects.filter(
            enumerator_id_input='EN-2025-0002'
        ).exclude(assigned_enumerator=enumerator)
        
        if riders_to_fix.exists():
            print(f"🔧 Fixing {riders_to_fix.count()} rider assignments...")
            
            for rider in riders_to_fix:
                old_enumerator = rider.assigned_enumerator
                rider.assigned_enumerator = enumerator
                rider.save()
                
                print(f"✅ Fixed: {rider.full_name}")
                print(f"   From: {old_enumerator}")
                print(f"   To: {enumerator.full_name}")
        else:
            print("✅ All riders are correctly assigned")
        
        # Also check for completely unassigned riders
        unassigned = Rider.objects.filter(
            enumerator_id_input='EN-2025-0002',
            assigned_enumerator__isnull=True
        )
        
        if unassigned.exists():
            print(f"\n🔧 Assigning {unassigned.count()} unassigned riders...")
            
            for rider in unassigned:
                rider.assigned_enumerator = enumerator
                rider.save()
                print(f"✅ Assigned: {rider.full_name} to {enumerator.full_name}")
        
        print(f"\n✅ Assignment fixes complete!")
        
    except Exception as e:
        print(f"❌ Error fixing assignments: {e}")

def verify_fix():
    print("\n✅ VERIFYING FIXES")
    print("=" * 20)
    
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        assigned_riders = enumerator.assigned_riders.all()
        pending_riders = enumerator.assigned_riders.filter(status=Rider.PENDING_APPROVAL)
        
        print(f"Total assigned to {enumerator.unique_id}: {assigned_riders.count()}")
        print(f"Pending approval: {pending_riders.count()}")
        
        if pending_riders.exists():
            print("Pending riders:")
            for rider in pending_riders:
                print(f"  • {rider.full_name} ({rider.phone_number}) - {rider.status}")
        
        return pending_riders.count()
        
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return 0

if __name__ == "__main__":
    # Step 1: Debug current state
    debug_rider_assignment()
    
    # Step 2: Fix assignments
    fix_rider_assignment()
    
    # Step 3: Verify fixes
    pending_count = verify_fix()
    
    print(f"\n🎯 FINAL RESULT")
    print("=" * 15)
    print(f"Riders pending approval for EN-2025-0002: {pending_count}")
    
    if pending_count > 0:
        print("✅ Issue should now be fixed!")
        print("🔄 Refresh the enumerator dashboard to see pending riders")
    else:
        print("ℹ️  No riders currently pending for this enumerator")
        print("📱 Register a new rider with EN-2025-0002 to test")