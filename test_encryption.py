#!/usr/bin/env python3
"""
Test script for ID encryption system
"""

import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from riders.models import Rider, Enumerator
from riders.encryption import IDEncryption
from django.contrib.auth.models import User

def test_encryption_system():
    """Test the ID encryption and security system"""
    
    print("🔐 Testing ID Encryption System")
    print("=" * 50)
    
    # Test 1: Basic encryption/decryption
    print("\n1. Testing basic encryption/decryption:")
    encryptor = IDEncryption()
    
    test_id = "CF1234567890123"
    encrypted = encryptor.encrypt_id(test_id)
    decrypted = encryptor.decrypt_id(encrypted)
    
    print(f"Original ID:  {test_id}")
    print(f"Encrypted:    {encrypted[:20]}...")
    print(f"Decrypted:    {decrypted}")
    print(f"✅ Encryption/Decryption: {'PASS' if test_id == decrypted else 'FAIL'}")
    
    # Test 2: ID validation
    print("\n2. Testing ID validation:")
    valid_ids = ["CF1234567890123", "CM9876543210987"]
    invalid_ids = ["CF123456789012", "XY1234567890123", "CF123456789012A", ""]
    
    for id_num in valid_ids:
        result = encryptor.validate_id_format(id_num)
        print(f"   {id_num}: {'✅ VALID' if result else '❌ INVALID'}")
    
    for id_num in invalid_ids:
        result = encryptor.validate_id_format(id_num)
        print(f"   {id_num}: {'❌ INVALID' if not result else '✅ VALID'} (Expected INVALID)")
    
    # Test 3: Hash generation for duplicate detection
    print("\n3. Testing hash generation:")
    hash1 = encryptor.hash_id_for_verification("CF1234567890123")
    hash2 = encryptor.hash_id_for_verification("CF1234567890123")  # Same ID
    hash3 = encryptor.hash_id_for_verification("CF9876543210987")  # Different ID
    
    print(f"Hash 1:       {hash1}")
    print(f"Hash 2 (same): {hash2}")
    print(f"Hash 3 (diff): {hash3}")
    print(f"✅ Same ID same hash: {'PASS' if hash1 == hash2 else 'FAIL'}")
    print(f"✅ Diff ID diff hash: {'PASS' if hash1 != hash3 else 'FAIL'}")
    
    # Test 4: Model integration with EncryptedIDField
    print("\n4. Testing model integration:")
    
    # Create a test rider
    rider = Rider.objects.create(
        phone_number="256700000001",
        first_name="Test",
        last_name="Rider",
        experience_level="NEW_RIDER",
        status="REGISTERED"
    )
    
    # Create a test admin user
    admin_user = User.objects.create_user(
        username="testadmin",
        is_staff=True
    )
    
    # Test secure ID setting
    try:
        success = rider.set_national_id("CF1234567890123", admin_user, "Testing encryption")
        print(f"✅ ID Setting: {'PASS' if success else 'FAIL'}")
        
        # Verify ID is encrypted in database
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT national_id_encrypted FROM riders_rider WHERE id = %s", [rider.id])
            encrypted_in_db = cursor.fetchone()[0]
            
        print(f"   Encrypted in DB: {encrypted_in_db[:30]}...")
        print(f"   Is encrypted: {'✅ YES' if len(encrypted_in_db) > 50 else '❌ NO'}")
        
        # Test secure ID retrieval
        retrieved_id = rider.get_national_id(admin_user, "Testing decryption")
        print(f"   Retrieved ID: {retrieved_id}")
        print(f"✅ ID Retrieval: {'PASS' if retrieved_id == 'CF1234567890123' else 'FAIL'}")
        
        # Test masked ID display
        masked_id = rider.get_masked_id()
        print(f"   Masked ID: {masked_id}")
        print(f"✅ ID Masking: {'PASS' if masked_id == 'CF12******123' else 'FAIL'}")
        
    except Exception as e:
        print(f"❌ ID Setting/Retrieval: FAIL - {e}")
    
    # Test 5: Duplicate detection
    print("\n5. Testing duplicate detection:")
    try:
        duplicate_rider = Rider.objects.create(
            phone_number="256700000002",
            first_name="Duplicate",
            last_name="Test",
            experience_level="NEW_RIDER",
            status="REGISTERED"
        )
        
        # Try to set the same ID - should fail
        try:
            duplicate_rider.set_national_id("CF1234567890123", admin_user, "Testing duplicate")
            print("❌ Duplicate Detection: FAIL - Duplicate was allowed")
        except ValueError as e:
            print(f"✅ Duplicate Detection: PASS - {e}")
            
    except Exception as e:
        print(f"❌ Duplicate Test Setup: FAIL - {e}")
    
    # Test 6: Authorization
    print("\n6. Testing authorization:")
    
    # Create non-admin user
    regular_user = User.objects.create_user(username="regularuser")
    
    try:
        # Should fail for non-authorized user
        rider.get_national_id(regular_user, "Unauthorized access")
        print("❌ Authorization: FAIL - Unauthorized access was allowed")
    except PermissionError:
        print("✅ Authorization: PASS - Unauthorized access blocked")
    except Exception as e:
        print(f"❌ Authorization: FAIL - Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 ID Encryption System Test Complete!")
    
    # Cleanup
    try:
        rider.delete()
        duplicate_rider.delete()
        admin_user.delete()
        regular_user.delete()
    except:
        pass

if __name__ == "__main__":
    test_encryption_system()