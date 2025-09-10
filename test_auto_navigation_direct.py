#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
import requests
import time

# Add the project directory to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from riders.models import Rider, Enumerator

# API Configuration
API_BASE_URL = "http://192.168.1.19:8000/api"
MOCK_FIREBASE_TOKEN = "mock_firebase_token_for_testing_" + "x" * 100

def test_auto_navigation_direct():
    print("🧪 AUTO-NAVIGATION TEST - DIRECT MODE")
    print("=" * 40)
    
    # Get one of the existing pending riders
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        pending_riders = enumerator.assigned_riders.filter(status=Rider.PENDING_APPROVAL)
        
        if not pending_riders.exists():
            print("❌ No pending riders found.")
            return False
        
        # Use the first pending rider
        rider = pending_riders.first()
        print(f"📱 Test rider: {rider.full_name} ({rider.phone_number})")
        
        # Set a test FCM token for this rider
        test_fcm_token = f"test_auto_nav_token_{int(time.time())}"
        rider.fcm_token = test_fcm_token
        rider.save()
        
        print(f"🔑 FCM token set: {test_fcm_token[:30]}...")
        
    except Exception as e:
        print(f"❌ Error setting up test rider: {e}")
        return False
    
    print(f"\n🎯 TESTING AUTO-NAVIGATION FLOW:")
    print("1. ✅ Test rider prepared")
    print("2. 📡 Updating FCM token via API...")
    
    # Step 1: Update FCM token via API
    url = f"{API_BASE_URL}/fcm/update-token/"
    payload = {
        "fcm_token": test_fcm_token,
        "phone_number": rider.phone_number
    }
    headers = {
        "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("   ✅ FCM token updated successfully")
    else:
        print(f"   ❌ FCM token update failed: {response.status_code}")
        return False
    
    print("3. 👍 Approving rider (triggering auto-navigation)...")
    
    # Step 2: Approve rider
    url = f"{API_BASE_URL}/riders/{rider.id}/approve/"
    headers = {"Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}"}
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Rider approved successfully!")
        print(f"   🔔 Notification sent: {'Yes' if data.get('notification_sent') else 'No'}")
        
        # Verify database update
        rider.refresh_from_db()
        print(f"   📊 Database status: {rider.status}")
        
        print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print(f"📱 IF RIDER APP WAS OPEN ON PENDING SCREEN:")
        print(f"   ✅ Green snackbar should appear with approval message")
        print(f"   ✅ After 2 seconds, auto-navigate to home screen")
        print(f"   ✅ No manual button tapping required!")
        
        return True
        
    else:
        print(f"   ❌ Approval failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    success = test_auto_navigation_direct()
    
    if success:
        print(f"\n🚀 AUTO-NAVIGATION TEST PASSED!")
        print("📲 To test this manually:")
        print("1. Open rider app with phone +256777345678")
        print("2. Login and navigate to pending approval screen")
        print("3. Run this script")
        print("4. Watch for automatic navigation after approval!")
    else:
        print(f"\n❌ AUTO-NAVIGATION TEST FAILED!")