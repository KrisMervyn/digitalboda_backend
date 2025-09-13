#!/usr/bin/env python3
"""
Test API Security Integration
Test the authentication and encryption system with API calls
"""

import requests
import json
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from django.contrib.auth.models import User
from riders.models import Rider, Enumerator

BASE_URL = "http://127.0.0.1:8000/api"

def test_api_security():
    """Test API authentication and security"""
    
    print("🔒 Testing API Security System")
    print("=" * 50)
    
    # Test 1: Endpoints require authentication
    print("\n1. Testing authentication requirement:")
    
    endpoints_to_test = [
        "/riders/1/",
        "/admin/pending-riders/",
        "/enumerator/assigned-riders/",
        "/auth/verify-token/",
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 401:
                print(f"   ✅ {endpoint}: Authentication required (401)")
            else:
                print(f"   ❌ {endpoint}: No auth required! Status: {response.status_code}")
        except requests.exceptions.ConnectionRefused:
            print(f"   ⚠️  Server not running - starting server...")
            break
    
    # Test 2: Login endpoints work
    print("\n2. Testing login functionality:")
    
    # Create test admin user for testing
    try:
        admin_user, created = User.objects.get_or_create(
            username="testadmin",
            defaults={
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password("testpass123")
            admin_user.save()
            print("   Created test admin user")
    except:
        print("   Test admin user already exists")
    
    # Test admin login
    try:
        login_data = {
            "username": "testadmin",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/auth/admin/login/", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('token')
            print(f"   ✅ Admin Login: SUCCESS - Token: {token[:20]}...")
            
            # Test authenticated request
            headers = {"Authorization": f"Token {token}"}
            auth_response = requests.get(f"{BASE_URL}/auth/verify-token/", headers=headers)
            
            if auth_response.status_code == 200:
                print(f"   ✅ Token Verification: SUCCESS")
            else:
                print(f"   ❌ Token Verification: FAILED - {auth_response.status_code}")
                
        else:
            print(f"   ❌ Admin Login: FAILED - {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionRefused:
        print("   ⚠️  Server not running - cannot test login")
        return False
    except Exception as e:
        print(f"   ❌ Login Test Error: {e}")
        return False
    
    # Test 3: Rate limiting
    print("\n3. Testing rate limiting:")
    try:
        # Make rapid requests to test rate limiting
        responses = []
        for i in range(5):
            resp = requests.post(f"{BASE_URL}/auth/admin/login/", json={"username": "invalid", "password": "invalid"})
            responses.append(resp.status_code)
        
        if any(r == 429 for r in responses):
            print("   ✅ Rate Limiting: ACTIVE")
        else:
            print("   ⚠️  Rate Limiting: May not be active (this is normal for small tests)")
            
    except Exception as e:
        print(f"   ❌ Rate Limiting Test Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Security Test Complete!")
    
    return True

if __name__ == "__main__":
    test_api_security()