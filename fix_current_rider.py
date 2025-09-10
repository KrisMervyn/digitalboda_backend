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

def fix_current_test_rider():
    print("🔧 FIXING CURRENT TEST RIDER")
    print("=" * 30)
    
    # Get the enumerator
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        print(f"✅ Found enumerator: {enumerator.full_name}")
    except Enumerator.DoesNotExist:
        print("❌ Enumerator not found!")
        return
    
    # Get pending riders
    pending_riders = Rider.objects.filter(status=Rider.PENDING_APPROVAL, assigned_enumerator__isnull=True)
    
    print(f"\n📱 UNASSIGNED PENDING RIDERS ({pending_riders.count()}):")
    for i, rider in enumerate(pending_riders, 1):
        print(f"{i}. {rider.full_name} ({rider.phone_number})")
        print(f"   Created: {rider.created_at}")
        print(f"   Reference: {rider.unique_id}")
    
    if pending_riders.exists():
        print(f"\n🔧 ASSIGNING ALL PENDING RIDERS TO {enumerator.unique_id}")
        
        for rider in pending_riders:
            # Assign to enumerator and update enumerator_id_input
            rider.assigned_enumerator = enumerator
            rider.enumerator_id_input = 'EN-2025-0002'
            rider.save()
            
            print(f"✅ Assigned: {rider.full_name} → {enumerator.full_name}")
    
    # Verify the fix
    assigned_pending = enumerator.assigned_riders.filter(status=Rider.PENDING_APPROVAL)
    print(f"\n✅ VERIFICATION:")
    print(f"Riders now pending for {enumerator.unique_id}: {assigned_pending.count()}")
    
    for rider in assigned_pending:
        print(f"• {rider.full_name} ({rider.phone_number})")
    
    return assigned_pending.count()

if __name__ == "__main__":
    count = fix_current_test_rider()
    
    print(f"\n🎯 RESULT: {count} riders now pending approval for EN-2025-0002")
    print("🔄 Refresh your admin app to see the pending riders!")