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
from riders.services.notification_service import FCMService

# API Configuration
API_BASE_URL = "http://192.168.1.25:8000/api"
MOCK_FIREBASE_TOKEN = "mock_firebase_token_for_testing_" + "x" * 100

def create_test_scenario():
    """Create a complete test scenario with one device"""
    print("🎬 Creating Single Device Test Scenario")
    print("=" * 50)
    
    # Step 1: Create/Get test rider
    phone_number = "+256700000999"
    test_fcm_token = f"test_device_token_{int(time.time())}"
    
    try:
        rider = Rider.objects.get(phone_number=phone_number)
        print(f"📱 Using existing test rider: {rider.full_name}")
    except Rider.DoesNotExist:
        # Create new test rider
        enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
        rider = Rider.objects.create(
            phone_number=phone_number,
            first_name="Test",
            last_name="SingleDevice",
            status=Rider.PENDING_APPROVAL,
            assigned_enumerator=enumerator,
            fcm_token=test_fcm_token
        )
        print(f"📱 Created test rider: {rider.full_name}")
    
    # Ensure rider has FCM token and is pending
    rider.fcm_token = test_fcm_token
    rider.status = Rider.PENDING_APPROVAL
    rider.save()
    
    return rider, test_fcm_token

def simulate_rider_registration():
    """Simulate what happens when rider reaches pending approval screen"""
    print("\n📱 SIMULATION: Rider App Reaches Pending Approval Screen")
    print("-" * 50)
    
    rider, fcm_token = create_test_scenario()
    
    # Simulate FCM token update from rider app
    url = f"{API_BASE_URL}/fcm/update-token/"
    payload = {
        "fcm_token": fcm_token,
        "phone_number": rider.phone_number
    }
    headers = {
        "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ FCM token registered for {rider.full_name}")
        print(f"📱 Token: {fcm_token[:30]}...")
        return rider
    else:
        print(f"❌ Failed to register FCM token: {response.text}")
        return None

def simulate_enumerator_approval(rider):
    """Simulate what happens when enumerator approves rider"""
    print(f"\n👨‍💼 SIMULATION: Enumerator Approves {rider.full_name}")
    print("-" * 50)
    
    # Direct API call to approve rider
    url = f"{API_BASE_URL}/riders/{rider.id}/approve/"
    headers = {
        "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Rider approved successfully!")
        print(f"🔔 Notification sent: {data.get('notification_sent', False)}")
        
        # Verify database update
        rider.refresh_from_db()
        print(f"📊 Updated status: {rider.status}")
        print(f"⏰ Approved at: {rider.approved_at}")
        
        return True
    else:
        print(f"❌ Failed to approve rider: {response.text}")
        return False

def simulate_enumerator_rejection(rider):
    """Simulate what happens when enumerator rejects rider"""
    print(f"\n👨‍💼 SIMULATION: Enumerator Rejects {rider.full_name}")
    print("-" * 50)
    
    # First reset rider to pending
    rider.status = Rider.PENDING_APPROVAL
    rider.save()
    
    # Direct API call to reject rider
    url = f"{API_BASE_URL}/riders/{rider.id}/reject/"
    payload = {
        "rejection_reason": "Test rejection - missing documentation"
    }
    headers = {
        "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Rider rejected successfully!")
        print(f"🔔 Notification sent: {data.get('notification_sent', False)}")
        
        # Verify database update
        rider.refresh_from_db()
        print(f"📊 Updated status: {rider.status}")
        print(f"❌ Rejection reason: {rider.rejection_reason}")
        
        return True
    else:
        print(f"❌ Failed to reject rider: {response.text}")
        return False

def test_direct_notification(rider):
    """Test direct notification sending"""
    print(f"\n🔔 SIMULATION: Direct Notification Test")
    print("-" * 50)
    
    # Test approval notification
    print("Testing APPROVAL notification...")
    success = FCMService.send_status_change_notification(
        fcm_token=rider.fcm_token,
        rider_name=rider.full_name,
        new_status='APPROVED'
    )
    print(f"✅ Approval notification: {'Sent' if success else 'Failed'}")
    
    time.sleep(2)  # Small delay
    
    # Test rejection notification
    print("Testing REJECTION notification...")
    success = FCMService.send_status_change_notification(
        fcm_token=rider.fcm_token,
        rider_name=rider.full_name,
        new_status='REJECTED',
        rejection_reason='Test rejection for notification testing'
    )
    print(f"✅ Rejection notification: {'Sent' if success else 'Failed'}")

def show_testing_guide():
    """Show what to do on the device"""
    print("\n📋 SINGLE DEVICE TESTING GUIDE")
    print("=" * 50)
    print("1. 📱 RIDER APP TEST:")
    print("   • Open DigitalBoda Rider App")
    print("   • Register with phone: +256700000999")
    print("   • Complete onboarding → reach pending approval screen")
    print("   • Look for FCM token in console logs")
    print("")
    print("2. 🖥️  BACKEND SIMULATION:")
    print("   • Run this script to simulate enumerator actions")
    print("   • Watch for push notifications on your device")
    print("")
    print("3. 👨‍💼 ADMIN APP VERIFICATION:")
    print("   • Open DigitalBoda Admin App")  
    print("   • Login as enumerator to verify rider appears in pending list")
    print("   • Use script to approve/reject and check UI updates")

def main():
    print("🧪 SINGLE DEVICE FCM TESTING SYSTEM")
    print("🎯 This simulates the complete notification flow")
    print("=" * 60)
    
    # Show initial setup guide
    show_testing_guide()
    
    input("\n⏯️  Press Enter when you've opened the RIDER APP and reached pending approval screen...")
    
    # Step 1: Simulate rider registration
    rider = simulate_rider_registration()
    if not rider:
        print("❌ Failed to set up test rider")
        return
    
    print(f"\n✅ Test rider ready: {rider.full_name} ({rider.phone_number})")
    print(f"📱 FCM Token: {rider.fcm_token[:30]}...")
    
    # Step 2: Test different scenarios
    while True:
        print("\n🎮 CHOOSE TEST SCENARIO:")
        print("1. 👍 Simulate APPROVAL (with notification)")
        print("2. 👎 Simulate REJECTION (with notification)")
        print("3. 🔔 Test DIRECT notification sending")
        print("4. 📊 Show current rider status")
        print("5. 🔄 Reset rider to PENDING")
        print("6. ❌ Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            simulate_enumerator_approval(rider)
            print("\n📱 Check your device for approval notification!")
            
        elif choice == "2":
            simulate_enumerator_rejection(rider)
            print("\n📱 Check your device for rejection notification!")
            
        elif choice == "3":
            test_direct_notification(rider)
            print("\n📱 Check your device for test notifications!")
            
        elif choice == "4":
            rider.refresh_from_db()
            print(f"\n📊 Current Status:")
            print(f"   Name: {rider.full_name}")
            print(f"   Status: {rider.status}")
            print(f"   FCM Token: {rider.fcm_token[:30] if rider.fcm_token else 'None'}...")
            print(f"   Rejection Reason: {rider.rejection_reason or 'None'}")
            
        elif choice == "5":
            rider.status = Rider.PENDING_APPROVAL
            rider.rejection_reason = ""
            rider.save()
            print(f"✅ Reset {rider.full_name} to PENDING status")
            
        elif choice == "6":
            print("👋 Exiting FCM testing system")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()