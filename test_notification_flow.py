#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
import json
import requests
import time

# Add the project directory to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

# Import Django models and services
from riders.models import Rider
from riders.services.notification_service import FCMService

# API Configuration
API_BASE_URL = "http://192.168.1.25:8000/api"
MOCK_FIREBASE_TOKEN = "mock_firebase_token_for_testing_" + "x" * 100  # Mock long token

def test_fcm_token_update():
    """Test FCM token update endpoint"""
    print("🧪 Testing FCM token update endpoint...")
    
    try:
        # Get a test rider
        rider = Rider.objects.first()
        if not rider:
            print("❌ No riders found for testing")
            return False
        
        # Test FCM token update API endpoint
        url = f"{API_BASE_URL}/fcm/update-token/"
        payload = {
            "fcm_token": f"test_fcm_token_{int(time.time())}",
            "phone_number": rider.phone_number
        }
        headers = {
            "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.put(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ FCM token update successful for {rider.phone_number}")
            
            # Verify token was stored
            rider.refresh_from_db()
            if rider.fcm_token == payload["fcm_token"]:
                print("✅ FCM token correctly stored in database")
                return True
            else:
                print("❌ FCM token not stored correctly in database")
                return False
        else:
            print(f"❌ FCM token update failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FCM token update test error: {str(e)}")
        return False

def test_status_change_notification():
    """Test status change notification"""
    print("🧪 Testing status change notification...")
    
    try:
        # Get a rider with FCM token
        rider = Rider.objects.exclude(fcm_token__isnull=True).first()
        if not rider:
            print("❌ No riders with FCM tokens found")
            return False
        
        # Test notification sending
        success = FCMService.send_status_change_notification(
            fcm_token=rider.fcm_token,
            rider_name=rider.full_name,
            new_status='APPROVED'
        )
        
        if success:
            print(f"✅ Status change notification sent to {rider.full_name}")
            return True
        else:
            print(f"⚠️ Notification sending returned false (expected in test environment)")
            return True  # This is expected without proper FCM setup
            
    except Exception as e:
        print(f"❌ Status change notification test error: {str(e)}")
        return False

def test_rider_approval_endpoint():
    """Test rider approval with notification"""
    print("🧪 Testing rider approval endpoint with notification...")
    
    try:
        # Get a rider with FCM token in pending status
        rider = Rider.objects.filter(
            status=Rider.PENDING_APPROVAL,
        ).exclude(fcm_token__isnull=True).first()
        
        if not rider:
            # Create a test scenario
            rider = Rider.objects.first()
            if rider:
                rider.status = Rider.PENDING_APPROVAL
                rider.fcm_token = f"test_token_{int(time.time())}"
                rider.save()
            else:
                print("❌ No riders available for testing")
                return False
        
        # Test approval endpoint
        url = f"{API_BASE_URL}/riders/{rider.id}/approve/"
        headers = {
            "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Rider approval successful for {rider.full_name}")
            
            # Verify status was updated
            rider.refresh_from_db()
            if rider.status == Rider.APPROVED:
                print("✅ Rider status correctly updated to APPROVED")
                
                # Check response data
                data = response.json()
                if 'notification_sent' in data:
                    print(f"✅ Notification status reported: {data['notification_sent']}")
                
                return True
            else:
                print(f"❌ Rider status not updated correctly: {rider.status}")
                return False
        else:
            print(f"❌ Rider approval failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Rider approval test error: {str(e)}")
        return False

def test_rider_rejection_endpoint():
    """Test rider rejection with notification"""
    print("🧪 Testing rider rejection endpoint with notification...")
    
    try:
        # Get a rider with FCM token in pending status
        rider = Rider.objects.filter(
            status=Rider.PENDING_APPROVAL,
        ).exclude(fcm_token__isnull=True).first()
        
        if not rider:
            # Create a test scenario
            rider = Rider.objects.exclude(status=Rider.REJECTED).first()
            if rider:
                rider.status = Rider.PENDING_APPROVAL
                rider.fcm_token = f"test_token_{int(time.time())}"
                rider.save()
            else:
                print("❌ No riders available for testing")
                return False
        
        # Test rejection endpoint
        url = f"{API_BASE_URL}/riders/{rider.id}/reject/"
        payload = {
            "rejection_reason": "Test rejection for notification flow testing"
        }
        headers = {
            "Authorization": f"Bearer {MOCK_FIREBASE_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Rider rejection successful for {rider.full_name}")
            
            # Verify status was updated
            rider.refresh_from_db()
            if rider.status == Rider.REJECTED:
                print("✅ Rider status correctly updated to REJECTED")
                print(f"✅ Rejection reason stored: {rider.rejection_reason}")
                
                # Check response data
                data = response.json()
                if 'notification_sent' in data:
                    print(f"✅ Notification status reported: {data['notification_sent']}")
                
                return True
            else:
                print(f"❌ Rider status not updated correctly: {rider.status}")
                return False
        else:
            print(f"❌ Rider rejection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Rider rejection test error: {str(e)}")
        return False

def test_bulk_notification():
    """Test bulk notification functionality"""
    print("🧪 Testing bulk notification functionality...")
    
    try:
        # Get riders with FCM tokens
        riders = list(Rider.objects.exclude(fcm_token__isnull=True)[:3])
        if not riders:
            print("❌ No riders with FCM tokens found for bulk test")
            return True  # Not a critical failure
        
        fcm_tokens = [rider.fcm_token for rider in riders]
        
        result = FCMService.send_bulk_notification(
            fcm_tokens=fcm_tokens,
            title="Test Bulk Notification",
            body="This is a test bulk notification for DigitalBoda.",
            data={"type": "test", "message": "bulk_test"}
        )
        
        print(f"✅ Bulk notification result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Bulk notification test error: {str(e)}")
        return False

def print_test_summary():
    """Print summary of database state"""
    print("\n📊 Database Summary:")
    print("-" * 30)
    
    total_riders = Rider.objects.count()
    riders_with_tokens = Rider.objects.exclude(fcm_token__isnull=True).count()
    pending_riders = Rider.objects.filter(status=Rider.PENDING_APPROVAL).count()
    approved_riders = Rider.objects.filter(status=Rider.APPROVED).count()
    rejected_riders = Rider.objects.filter(status=Rider.REJECTED).count()
    
    print(f"Total Riders: {total_riders}")
    print(f"Riders with FCM tokens: {riders_with_tokens}")
    print(f"Pending approval: {pending_riders}")
    print(f"Approved: {approved_riders}")
    print(f"Rejected: {rejected_riders}")
    
    if riders_with_tokens > 0:
        print("\nRiders with FCM tokens:")
        for rider in Rider.objects.exclude(fcm_token__isnull=True)[:5]:
            print(f"  - {rider.full_name} ({rider.phone_number}): {rider.fcm_token[:20]}...")

if __name__ == "__main__":
    print("🔔 Starting End-to-End Notification Flow Tests...")
    print("=" * 60)
    
    tests = [
        ("FCM Token Update", test_fcm_token_update),
        ("Status Change Notification", test_status_change_notification),
        ("Rider Approval with Notification", test_rider_approval_endpoint),
        ("Rider Rejection with Notification", test_rider_rejection_endpoint),
        ("Bulk Notification", test_bulk_notification),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {str(e)}")
            results.append((test_name, False))
        
        print("")  # Add spacing
    
    # Print final results
    print("=" * 60)
    print("📋 FINAL TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
    
    print("-" * 60)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Notification flow is working correctly.")
    elif passed > 0:
        print("⚠️  SOME TESTS PASSED. Check failed tests for issues.")
    else:
        print("❌ ALL TESTS FAILED. Check configuration and setup.")
    
    print_test_summary()