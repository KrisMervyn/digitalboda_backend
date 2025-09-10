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
API_BASE_URL = "http://192.168.1.19:8000/api"
MOCK_FIREBASE_TOKEN = "mock_firebase_token_for_testing_" + "x" * 100

def setup_test_rider():
    """Set up or get test rider"""
    phone_number = "+256700000999"
    test_fcm_token = f"test_device_token_{int(time.time())}"
    
    try:
        rider = Rider.objects.get(phone_number=phone_number)
        print(f"📱 Found existing test rider: {rider.full_name}")
    except Rider.DoesNotExist:
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
    
    # Update FCM token and status
    rider.fcm_token = test_fcm_token
    rider.status = Rider.PENDING_APPROVAL
    rider.save()
    
    return rider

def test_approval_flow(rider):
    """Test approval notification flow"""
    print(f"\n🧪 Testing APPROVAL flow for {rider.full_name}")
    print("-" * 50)
    
    # Update FCM token via API
    print("1. Updating FCM token...")
    url = f"{API_BASE_URL}/fcm/update-token/"
    payload = {
        "fcm_token": rider.fcm_token,
        "phone_number": rider.phone_number
    }
    headers = {
        "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(url, json=payload, headers=headers)
    print(f"   Status: {response.status_code} - {'✅ Success' if response.status_code == 200 else '❌ Failed'}")
    
    # Approve rider via API
    print("2. Approving rider...")
    url = f"{API_BASE_URL}/riders/{rider.id}/approve/"
    response = requests.post(url, headers={"Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}"})
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: ✅ Approved successfully")
        print(f"   Notification sent: {'✅ Yes' if data.get('notification_sent') else '❌ No'}")
        
        # Verify database
        rider.refresh_from_db()
        print(f"   Database status: {rider.status}")
        return True
    else:
        print(f"   Status: ❌ Failed ({response.status_code})")
        return False

def test_rejection_flow(rider):
    """Test rejection notification flow"""
    print(f"\n🧪 Testing REJECTION flow for {rider.full_name}")
    print("-" * 50)
    
    # Reset to pending
    rider.status = Rider.PENDING_APPROVAL
    rider.save()
    
    # Reject rider via API
    print("1. Rejecting rider...")
    url = f"{API_BASE_URL}/riders/{rider.id}/reject/"
    payload = {"rejection_reason": "Test rejection - single device testing"}
    headers = {
        "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: ✅ Rejected successfully")
        print(f"   Notification sent: {'✅ Yes' if data.get('notification_sent') else '❌ No'}")
        
        # Verify database
        rider.refresh_from_db()
        print(f"   Database status: {rider.status}")
        print(f"   Rejection reason: {rider.rejection_reason}")
        return True
    else:
        print(f"   Status: ❌ Failed ({response.status_code})")
        return False

def test_direct_notifications(rider):
    """Test direct FCM notifications"""
    print(f"\n🧪 Testing DIRECT notifications for {rider.full_name}")
    print("-" * 50)
    
    print("1. Sending approval notification...")
    success1 = FCMService.send_status_change_notification(
        fcm_token=rider.fcm_token,
        rider_name=rider.full_name,
        new_status='APPROVED'
    )
    print(f"   Result: {'✅ Sent' if success1 else '❌ Failed'}")
    
    time.sleep(2)
    
    print("2. Sending rejection notification...")
    success2 = FCMService.send_status_change_notification(
        fcm_token=rider.fcm_token,
        rider_name=rider.full_name,
        new_status='REJECTED',
        rejection_reason='Direct notification test'
    )
    print(f"   Result: {'✅ Sent' if success2 else '❌ Failed'}")
    
    return success1 and success2

def main():
    print("🚀 QUICK FCM TEST - Single Device")
    print("This will test notifications without needing multiple devices")
    print("=" * 60)
    
    # Setup
    rider = setup_test_rider()
    print(f"✅ Test setup complete")
    print(f"📱 Rider: {rider.full_name} ({rider.phone_number})")
    print(f"🔑 FCM Token: {rider.fcm_token[:30]}...")
    
    # Run all tests
    results = []
    
    print("\n🧪 RUNNING ALL FCM TESTS...")
    print("=" * 40)
    
    # Test 1: Approval flow
    results.append(("Approval Flow", test_approval_flow(rider)))
    
    # Test 2: Rejection flow  
    results.append(("Rejection Flow", test_rejection_flow(rider)))
    
    # Test 3: Direct notifications
    results.append(("Direct Notifications", test_direct_notifications(rider)))
    
    # Results summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! FCM notifications are working!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    print(f"\n📱 If you have the rider app open with phone {rider.phone_number},")
    print(f"   you should have seen push notifications during this test!")

if __name__ == "__main__":
    main()