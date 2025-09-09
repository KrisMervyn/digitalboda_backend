#!/usr/bin/env python
"""
Script to fix real rider assignments and remove test data
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from django.contrib.auth.models import User
from riders.models import Enumerator, Rider, RiderApplication

def remove_test_data():
    """Remove the test rider I created"""
    
    print("🧹 Removing test data...")
    
    try:
        test_rider = Rider.objects.get(phone_number='+256777123456')
        if test_rider.full_name == 'Test Pending':
            # Remove application first
            try:
                app = test_rider.application
                print(f"   🗑️ Removing test application: {app.reference_number}")
                app.delete()
            except RiderApplication.DoesNotExist:
                pass
            
            print(f"   🗑️ Removing test rider: {test_rider.full_name}")
            test_rider.delete()
        else:
            print(f"   ⚠️ Phone +256777123456 belongs to real user: {test_rider.full_name}")
    except Rider.DoesNotExist:
        print(f"   ✅ No test rider to remove")

def fix_today_steven():
    """Fix Today Steven's enumerator assignment"""
    
    print(f"\n🔧 Fixing Today Steven's assignment...")
    
    # Get Mukiibi enumerator  
    try:
        mukiibi = Enumerator.objects.get(unique_id='EN-2025-0002')
        print(f"   ✅ Found Mukiibi: {mukiibi.full_name} (ID: {mukiibi.unique_id})")
    except Enumerator.DoesNotExist:
        print(f"   ❌ Mukiibi enumerator not found!")
        return
    
    # Find Today Steven
    try:
        steven = Rider.objects.get(first_name='Today', last_name='Steven')
        print(f"   ✅ Found Today Steven: {steven.phone_number}")
        
        # Update assignment
        old_enum = steven.assigned_enumerator.unique_id if steven.assigned_enumerator else 'None'
        steven.assigned_enumerator = mukiibi
        steven.enumerator_id_input = 'EN-2025-0002'
        steven.save()
        
        print(f"   🔄 Changed assignment from {old_enum} to {mukiibi.unique_id}")
        
    except Rider.DoesNotExist:
        print(f"   ❌ Today Steven not found!")

def fix_mukwaya_andrew():
    """Fix Mukwaya Andrew's assignment if he should be assigned to Mukiibi"""
    
    print(f"\n🔧 Checking Mukwaya Andrew...")
    
    # Get Mukiibi enumerator  
    try:
        mukiibi = Enumerator.objects.get(unique_id='EN-2025-0002')
    except Enumerator.DoesNotExist:
        print(f"   ❌ Mukiibi enumerator not found!")
        return
    
    try:
        andrew = Rider.objects.get(phone_number='+256753109660')
        print(f"   ✅ Found Mukwaya Andrew: {andrew.full_name}")
        print(f"   📋 Current enumerator input: '{andrew.enumerator_id_input}'")
        print(f"   📋 Current assignment: {andrew.assigned_enumerator.unique_id if andrew.assigned_enumerator else 'None'}")
        
        # If he has no enumerator assigned, we should ask what ID he used
        if not andrew.assigned_enumerator and not andrew.enumerator_id_input:
            print(f"   ⚠️ Mukwaya Andrew has no enumerator assignment")
            print(f"   💡 You may need to ask him which enumerator ID he used during registration")
        elif andrew.enumerator_id_input == 'EN-2025-0002':
            # Assign to Mukiibi
            andrew.assigned_enumerator = mukiibi
            andrew.save()
            print(f"   🔄 Assigned Mukwaya Andrew to Mukiibi")
        else:
            print(f"   ✅ Mukwaya Andrew correctly assigned based on his input")
            
    except Rider.DoesNotExist:
        print(f"   ❌ Mukwaya Andrew not found!")

def verify_mukiibi_dashboard():
    """Verify what Mukiibi will see on his dashboard"""
    
    print(f"\n📊 Final verification for Mukiibi's dashboard...")
    
    try:
        mukiibi = Enumerator.objects.get(unique_id='EN-2025-0002')
        
        assigned_riders = mukiibi.assigned_riders.all()
        pending_riders = mukiibi.get_pending_riders()
        
        print(f"\n✅ Mukiibi ({mukiibi.unique_id}) Dashboard:")
        print(f"   Username: {mukiibi.user.username}")
        print(f"   Total assigned: {assigned_riders.count()}")
        print(f"   Pending approval: {pending_riders.count()}")
        
        if pending_riders.exists():
            print(f"\n📝 Pending Riders:")
            for rider in pending_riders:
                print(f"   - {rider.full_name} ({rider.phone_number})")
                print(f"     Status: {rider.status}")
                print(f"     Enumerator ID used: {rider.enumerator_id_input}")
                try:
                    app = rider.application
                    print(f"     Reference: {app.reference_number}")
                    print(f"     Submitted: {app.submitted_at}")
                except RiderApplication.DoesNotExist:
                    print(f"     ⚠️ No application record")
                print()
        else:
            print(f"   ⚠️ No pending riders")
            
        return pending_riders.count() > 0
        
    except Enumerator.DoesNotExist:
        print(f"   ❌ Mukiibi not found!")
        return False

def main():
    print("🔧 Fixing real rider assignments...\n")
    
    # Remove test data
    remove_test_data()
    
    # Fix Today Steven
    fix_today_steven()
    
    # Check Mukwaya Andrew
    fix_mukwaya_andrew()
    
    # Verify final state
    has_pending = verify_mukiibi_dashboard()
    
    if has_pending:
        print(f"\n✅ SUCCESS! Mukiibi can now see his real pending riders.")
        print(f"   Login with username: Mukiibi")
        print(f"   (Use the password you set up for this account)")
    else:
        print(f"\n⚠️ No pending riders found for Mukiibi.")
        print(f"   Check if riders completed onboarding properly.")

if __name__ == '__main__':
    main()