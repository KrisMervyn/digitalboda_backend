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

# Now test the FCM service
from riders.services.notification_service import FCMService

def test_fcm_initialization():
    """Test FCM service initialization"""
    print("🧪 Testing FCM Service initialization...")
    
    try:
        FCMService.initialize()
        print("✅ FCM Service initialization test passed")
        return True
    except Exception as e:
        print(f"❌ FCM Service initialization failed: {str(e)}")
        return False

def test_token_update():
    """Test FCM token update functionality"""
    print("🧪 Testing FCM token update...")
    
    try:
        # Get a test rider
        from riders.models import Rider
        rider = Rider.objects.first()
        
        if rider:
            success = FCMService.update_rider_fcm_token(rider, "test_token_123")
            print(f"✅ FCM token update test: {'passed' if success else 'failed'}")
            return success
        else:
            print("⚠️ No riders found for testing")
            return True
    except Exception as e:
        print(f"❌ FCM token update test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔔 Starting FCM Service Tests...")
    print("-" * 50)
    
    # Test 1: Initialization
    init_success = test_fcm_initialization()
    
    # Test 2: Token update
    token_success = test_token_update()
    
    print("-" * 50)
    if init_success and token_success:
        print("🎉 All FCM tests passed!")
    else:
        print("❌ Some FCM tests failed")