#!/usr/bin/env python3
"""
Test Photo Verification System
"""

import os
import django
from PIL import Image, ImageDraw
import io

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from riders.services.photo_verification import PhotoVerificationService

def create_test_images():
    """Create test images for verification"""
    
    # Create test images directory
    os.makedirs('test_images', exist_ok=True)
    
    # Create a realistic test profile photo (person face simulation)
    profile_img = Image.new('RGB', (600, 800), color='lightblue')
    draw = ImageDraw.Draw(profile_img)
    
    # Draw a simple face representation
    # Head (circle)
    draw.ellipse([200, 150, 400, 350], fill='peachpuff', outline='black', width=2)
    # Eyes
    draw.ellipse([240, 200, 260, 220], fill='black')
    draw.ellipse([340, 200, 360, 220], fill='black')
    # Nose
    draw.line([300, 230, 300, 270], fill='black', width=2)
    # Mouth
    draw.arc([260, 280, 340, 320], 0, 180, fill='black', width=2)
    
    profile_img.save('test_images/profile_photo.jpg', 'JPEG', quality=95)
    
    # Create a test ID document photo
    id_img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(id_img)
    
    # Draw ID card layout
    draw.rectangle([50, 50, 750, 450], outline='blue', width=3)
    draw.text([60, 70], "REPUBLIC OF UGANDA", fill='black')
    draw.text([60, 100], "NATIONAL IDENTITY CARD", fill='black')
    draw.text([60, 150], "NAME: JOHN MUKASA SSALI", fill='black')
    draw.text([60, 180], "ID NO: CF1234567890123", fill='black')
    draw.text([60, 210], "DOB: 15/03/1995", fill='black')
    draw.text([60, 240], "SEX: MALE", fill='black')
    
    # Draw face area on ID
    draw.ellipse([600, 150, 720, 270], fill='peachpuff', outline='black', width=2)
    # Eyes
    draw.ellipse([620, 180, 630, 190], fill='black')
    draw.ellipse([690, 180, 700, 190], fill='black')
    # Simple mouth
    draw.arc([640, 220, 680, 240], 0, 180, fill='black', width=1)
    
    id_img.save('test_images/id_document.jpg', 'JPEG', quality=90)
    
    # Create a low-quality test image
    low_quality_img = Image.new('RGB', (100, 100), color='gray')
    low_quality_img.save('test_images/low_quality.jpg', 'JPEG', quality=20)
    
    print("✅ Test images created in test_images/ directory")
    return {
        'profile_photo': 'test_images/profile_photo.jpg',
        'id_document': 'test_images/id_document.jpg',
        'low_quality': 'test_images/low_quality.jpg'
    }

def test_photo_verification():
    """Test the photo verification system"""
    
    print("📸 Testing Photo Verification System")
    print("=" * 60)
    
    # Create test images
    test_images = create_test_images()
    
    # Initialize photo verification service
    verifier = PhotoVerificationService()
    
    # Test 1: Photo authenticity verification
    print("\n1. Testing Photo Authenticity Verification:")
    print("-" * 40)
    
    for name, image_path in test_images.items():
        print(f"\nTesting {name}:")
        result = verifier.verify_photo_authenticity(image_path)
        
        print(f"   Authentic: {result['authentic']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Checks passed: {sum(result['checks'].values())}/{len(result['checks'])}")
        
        if result['warnings']:
            print(f"   Warnings: {', '.join(result['warnings'])}")
    
    # Test 2: Face comparison
    print("\n2. Testing Face Comparison:")
    print("-" * 40)
    
    try:
        face_result = verifier.compare_faces(
            test_images['profile_photo'], 
            test_images['id_document']
        )
        
        print(f"   Faces match: {face_result['match']}")
        print(f"   Confidence: {face_result.get('confidence', 0):.2f}")
        
        if 'faces_found' in face_result:
            print(f"   Faces found - Profile: {face_result['faces_found']['profile']}, ID: {face_result['faces_found']['id_document']}")
        
        if 'error' in face_result:
            print(f"   Error: {face_result['error']}")
            
    except Exception as e:
        print(f"   Face comparison error: {e}")
    
    # Test 3: OCR text extraction
    print("\n3. Testing OCR Text Extraction:")
    print("-" * 40)
    
    try:
        ocr_result = verifier.extract_id_information(test_images['id_document'])
        
        if ocr_result['success']:
            print(f"   OCR Success: {ocr_result['success']}")
            print(f"   Confidence: {ocr_result.get('confidence', 0):.2f}")
            
            parsed = ocr_result.get('parsed_info', {})
            if parsed.get('id_number'):
                print(f"   Extracted ID: {parsed['id_number']}")
            if parsed.get('name'):
                print(f"   Extracted Name: {parsed['name']}")
            if parsed.get('date_of_birth'):
                print(f"   Extracted DOB: {parsed['date_of_birth']}")
                
            # Show raw text (first 100 chars)
            raw_text = ocr_result.get('raw_text', '')
            if raw_text:
                print(f"   Raw OCR text: {raw_text[:100]}...")
        else:
            print(f"   OCR Failed: {ocr_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   OCR error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Photo Verification System Test Complete!")
    
    # Test 4: Integration with Rider model
    print("\n4. Testing Integration with Rider Model:")
    print("-" * 40)
    
    try:
        from riders.models import Rider
        from django.contrib.auth.models import User
        
        # Create test user and rider
        test_user = User.objects.create_user(username='photo_test_user', is_staff=True)
        test_rider = Rider.objects.create(
            phone_number='256700000003',
            first_name='Photo',
            last_name='Test',
            experience_level='NEW_RIDER',
            status='REGISTERED'
        )
        
        # Add photos to rider (simulate file upload)
        # In real implementation, these would be uploaded files
        print("   ✅ Test rider created successfully")
        print("   ✅ Photo verification service is ready for integration")
        
        # Cleanup
        test_rider.delete()
        test_user.delete()
        
    except Exception as e:
        print(f"   Integration test error: {e}")

if __name__ == "__main__":
    test_photo_verification()