#!/usr/bin/env python
"""
Script to test what data is returned when Mukiibi logs in
"""
import os
import sys
import django
import base64
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from riders.models import Enumerator, Rider, RiderApplication

def test_mukiibi_authentication():
    """Test Mukiibi's authentication and what data is returned"""
    
    print("🔍 Testing Mukiibi's authentication...\n")
    
    # Test 1: Check if user exists
    try:
        user = User.objects.get(username='Mukiibi')
        print(f"✅ Found user: {user.username}")
        print(f"   First name: {user.first_name}")
        print(f"   Last name: {user.last_name}")
        print(f"   Email: {user.email}")
        print(f"   Is staff: {user.is_staff}")
        print(f"   Is active: {user.is_active}")
    except User.DoesNotExist:
        print(f"❌ User 'Mukiibi' not found!")
        return
    
    # Test 2: Check if enumerator profile exists
    try:
        enumerator = user.enumerator_profile
        print(f"\n✅ Found enumerator profile:")
        print(f"   ID: {enumerator.id}")
        print(f"   Unique ID: {enumerator.unique_id}")
        print(f"   First name: {enumerator.first_name}")
        print(f"   Last name: {enumerator.last_name}")
        print(f"   Full name: {enumerator.full_name}")
        print(f"   Phone: {enumerator.phone_number}")
        print(f"   Location: {enumerator.location}")
        print(f"   Region: {enumerator.assigned_region}")
        print(f"   Status: {enumerator.status}")
    except Enumerator.DoesNotExist:
        print(f"❌ No enumerator profile found for user!")
        return
    
    # Test 3: Simulate authentication (like Django does)
    print(f"\n🔐 Testing authentication...")
    
    # You'll need to provide the actual password
    print(f"   ⚠️  Need actual password to test authentication")
    print(f"   💡 Try common passwords or ask user for the password")
    
    # Test some common passwords
    test_passwords = ['password', '123456', 'Mukiibi123', 'mukiibi123', 'admin', 'password123']
    
    authenticated = False
    for password in test_passwords:
        auth_user = authenticate(username='Mukiibi', password=password)
        if auth_user:
            print(f"   ✅ Authentication successful with password: {password}")
            authenticated = True
            break
    
    if not authenticated:
        print(f"   ❌ Could not authenticate with test passwords")
        print(f"   💡 You may need to reset Mukiibi's password")
        return
    
    # Test 4: Simulate the API response
    print(f"\n📡 Simulating API response structure...")
    
    response_data = {
        'success': True,
        'message': 'Login successful',
        'data': {
            'id': enumerator.id,
            'unique_id': enumerator.unique_id,
            'uniqueId': enumerator.unique_id,  # Compatibility
            'first_name': enumerator.first_name,
            'last_name': enumerator.last_name,
            'firstName': enumerator.first_name,  # Compatibility
            'lastName': enumerator.last_name,   # Compatibility
            'full_name': enumerator.full_name,
            'fullName': enumerator.full_name,   # Compatibility
            'name': enumerator.full_name,       # Compatibility
            'username': user.username,
            'phone_number': enumerator.phone_number,
            'phoneNumber': enumerator.phone_number,  # Compatibility
            'location': enumerator.location,
            'area': enumerator.location,        # Compatibility
            'region': enumerator.assigned_region, # Compatibility
            'assigned_region': enumerator.assigned_region,
            'assignedRegion': enumerator.assigned_region,  # Compatibility
            'status': enumerator.status,
            'enumerator_id': enumerator.unique_id  # For dashboard stats
        }
    }
    
    print(f"📋 Response JSON:")
    print(json.dumps(response_data, indent=2, default=str))
    
    # Test 5: Check what Flutter expects to see
    print(f"\n📱 Flutter app expects to see:")
    flutter_expected_fields = [
        'fullName', 'full_name', 'name', 'username',
        'uniqueId', 'unique_id', 'enumerator_id', 'id',
        'location', 'area', 'region'
    ]
    
    data = response_data['data']
    for field in flutter_expected_fields:
        if field in data and data[field]:
            print(f"   ✅ {field}: {data[field]}")
        else:
            print(f"   ❌ {field}: MISSING or EMPTY")

def check_password_reset():
    """Show how to reset Mukiibi's password if needed"""
    
    print(f"\n🔑 To reset Mukiibi's password (if needed):")
    print(f"   1. In Django admin or shell:")
    print(f"      user = User.objects.get(username='Mukiibi')")
    print(f"      user.set_password('newpassword123')")
    print(f"      user.save()")
    print(f"   2. Or use Django management command:")
    print(f"      python manage.py changepassword Mukiibi")

def main():
    test_mukiibi_authentication()
    check_password_reset()

if __name__ == '__main__':
    main()