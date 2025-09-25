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
API_BASE_URL = "http://192.168.1.25:8000/api"
MOCK_FIREBASE_TOKEN = "mock_firebase_token_for_testing_" + "x" * 100

def test_auto_navigation_flow():
    print("🧪 TESTING AUTO-NAVIGATION AFTER APPROVAL")
    print("=" * 45)
    
    # Get one of the existing pending riders
    try:
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        pending_riders = enumerator.assigned_riders.filter(status=Rider.PENDING_APPROVAL)
        
        if not pending_riders.exists():
            print("❌ No pending riders found. Please register a rider first.")
            return
        
        # Use the first pending rider
        rider = pending_riders.first()
        print(f"📱 Using test rider: {rider.full_name} ({rider.phone_number})")
        
        # Set a test FCM token for this rider
        test_fcm_token = f"test_auto_nav_token_{int(time.time())}"
        rider.fcm_token = test_fcm_token
        rider.save()
        
        print(f"🔑 Set FCM token: {test_fcm_token[:30]}...")
        
    except Exception as e:
        print(f"❌ Error setting up test rider: {e}")
        return
    
    print(f"\n🎯 TEST SCENARIO:")
    print("1. Rider app should be open on pending approval screen")
    print("2. Enumerator approves the rider via API")
    print("3. Push notification sent to rider")
    print("4. Rider app should automatically show success message")
    print("5. After 2 seconds, auto-navigate to home screen")
    
    input(f"\n⏯️  Open rider app with phone {rider.phone_number} and press Enter to continue...")
    
    # Step 1: Update FCM token via API
    print("\n1. 📡 Updating FCM token...")
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
        return
    
    # Step 2: Approve rider
    print("\n2. 👍 Approving rider (this should trigger auto-navigation)...")
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
        
        print(f"\n📱 EXPECTED BEHAVIOR ON RIDER APP:")
        print("   1. Green snackbar appears: '🎉 Congratulations! Your application has been approved!'")
        print("   2. After 2 seconds, automatically navigates to home screen")
        print("   3. No need to tap any buttons - it's fully automatic!")
        
        return True
        
    else:
        print(f"   ❌ Approval failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    success = test_auto_navigation_flow()
    
    if success:
        print(f"\n🎉 TEST COMPLETED!")
        print("If your rider app was open, you should have seen:")
        print("  ✅ Automatic approval message")
        print("  ✅ Auto-navigation to home screen")
        print("  ✅ No manual button tapping required")
    else:
        print(f"\n❌ TEST FAILED!")
        print("Check the error messages above for details.")