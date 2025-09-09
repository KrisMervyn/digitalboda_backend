#!/usr/bin/env python
"""
Script to check real database data for Mukiibi and Today Steven
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from django.contrib.auth.models import User
from riders.models import Enumerator, Rider, RiderApplication

def check_mukiibi_enumerator():
    """Find Mukiibi enumerator in the database"""
    
    print("🔍 Searching for Mukiibi enumerator...")
    
    # Search by name
    mukiibi_enums = Enumerator.objects.filter(
        first_name__icontains='mukiibi'
    ) | Enumerator.objects.filter(
        last_name__icontains='mukiibi'
    )
    
    print(f"📊 Found {mukiibi_enums.count()} enumerator(s) with 'Mukiibi' in name:")
    
    for enum in mukiibi_enums:
        print(f"\n✅ Enumerator: {enum.full_name}")
        print(f"   ID: {enum.unique_id}")
        print(f"   Username: {enum.user.username}")
        print(f"   Phone: {enum.phone_number}")
        print(f"   Location: {enum.location}")
        print(f"   Status: {enum.status}")
        
        # Check assigned riders
        assigned_riders = enum.assigned_riders.all()
        pending_riders = enum.get_pending_riders()
        
        print(f"   📝 Assigned riders: {assigned_riders.count()}")
        print(f"   ⏳ Pending riders: {pending_riders.count()}")
        
        if assigned_riders.exists():
            print(f"   📋 Rider list:")
            for rider in assigned_riders:
                print(f"      - {rider.full_name} ({rider.phone_number}) - {rider.status}")
    
    return mukiibi_enums

def find_today_steven():
    """Find Today Steven rider"""
    
    print(f"\n🔍 Searching for Today Steven rider...")
    
    # Search by name
    steven_riders = Rider.objects.filter(
        first_name__icontains='today'
    ) | Rider.objects.filter(
        last_name__icontains='steven'
    ) | Rider.objects.filter(
        first_name__icontains='steven'
    )
    
    print(f"📊 Found {steven_riders.count()} rider(s) with 'Today' or 'Steven' in name:")
    
    for rider in steven_riders:
        print(f"\n✅ Rider: {rider.full_name}")
        print(f"   Phone: {rider.phone_number}")
        print(f"   Status: {rider.status}")
        print(f"   Enumerator ID input: {rider.enumerator_id_input}")
        print(f"   Assigned enumerator: {rider.assigned_enumerator.unique_id if rider.assigned_enumerator else 'None'}")
        print(f"   Age: {rider.age}")
        print(f"   Location: {rider.location}")
        
        # Check application
        try:
            app = rider.application
            print(f"   📝 Application: {app.reference_number}")
            print(f"   📅 Submitted: {app.submitted_at}")
        except RiderApplication.DoesNotExist:
            print(f"   ⚠️  No application record")
    
    # Also search by phone number
    steven_by_phone = Rider.objects.filter(phone_number='+256753109660')
    if steven_by_phone.exists():
        rider = steven_by_phone.first()
        print(f"\n📱 Found rider by phone +256753109660:")
        print(f"   Name: {rider.full_name}")
        print(f"   Status: {rider.status}")
        print(f"   Enumerator ID: {rider.enumerator_id_input}")
        print(f"   Assigned: {rider.assigned_enumerator.unique_id if rider.assigned_enumerator else 'None'}")
    
    return steven_riders

def check_phone_256777123456():
    """Check who has the test phone number"""
    
    print(f"\n🔍 Checking phone number +256777123456...")
    
    try:
        rider = Rider.objects.get(phone_number='+256777123456')
        print(f"✅ Found rider: {rider.full_name}")
        print(f"   Status: {rider.status}")
        print(f"   Enumerator ID: {rider.enumerator_id_input}")
        print(f"   Assigned: {rider.assigned_enumerator.unique_id if rider.assigned_enumerator else 'None'}")
        print(f"   Created: {rider.created_at}")
        
        # This is likely the test rider I created
        if rider.full_name == 'Test Pending':
            print(f"   🧪 This is the test rider I created earlier")
    except Rider.DoesNotExist:
        print(f"❌ No rider found with phone +256777123456")

def list_all_enumerators():
    """List all enumerators"""
    
    print(f"\n📋 All enumerators in database:")
    
    all_enums = Enumerator.objects.all()
    for enum in all_enums:
        print(f"   {enum.unique_id}: {enum.full_name} (username: {enum.user.username})")

def main():
    print("🔍 Investigating real database data...\n")
    
    # Check Mukiibi
    mukiibi_enums = check_mukiibi_enumerator()
    
    # Find Today Steven
    steven_riders = find_today_steven()
    
    # Check the test phone number
    check_phone_256777123456()
    
    # List all enumerators
    list_all_enumerators()
    
    print(f"\n🎯 Analysis:")
    if mukiibi_enums.exists() and not steven_riders.exists():
        print(f"   - Mukiibi enumerator exists but Today Steven rider not found")
        print(f"   - Need to check if Steven completed registration properly")
    elif steven_riders.exists():
        steven = steven_riders.first()
        if steven.assigned_enumerator is None:
            print(f"   - Today Steven exists but not assigned to any enumerator")
        elif steven.assigned_enumerator.unique_id != mukiibi_enums.first().unique_id:
            print(f"   - Today Steven assigned to wrong enumerator")
    
    print(f"\n✅ Investigation complete!")

if __name__ == '__main__':
    main()