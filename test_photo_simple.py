#!/usr/bin/env python3
"""
Simple Photo Verification Test
"""

import os
import django
from PIL import Image
import tempfile

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalboda_backend.settings')
django.setup()

from riders.services.photo_verification import PhotoVerificationService

def test_basic_verification():
    """Test basic photo verification functionality"""
    
    print("🔍 Testing Photo Verification Components")
    print("=" * 50)
    
    # Initialize service
    verifier = PhotoVerificationService()
    
    # Test 1: Service initialization
    print("1. Service Initialization:")
    print(f"   ✅ PhotoVerificationService created")
    print(f"   ✅ Confidence threshold: {verifier.confidence_threshold}")
    print(f"   ✅ Face match threshold: {verifier.face_match_threshold}")
    
    # Test 2: Create a simple test image
    print("\n2. Image Processing Test:")
    
    # Create a simple RGB image
    test_image = Image.new('RGB', (400, 400), color='lightblue')
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        test_image.save(tmp_file.name, 'JPEG', quality=85)
        temp_image_path = tmp_file.name
    
    try:
        # Test authenticity verification
        result = verifier.verify_photo_authenticity(temp_image_path)
        
        print(f"   ✅ Image processed successfully")
        print(f"   ✅ Authentic: {result['authentic']}")
        print(f"   ✅ Confidence: {result['confidence']:.2f}")
        print(f"   ✅ Checks: {len(result['checks'])} tests performed")
        
        # Show detailed results
        for check_name, passed in result['checks'].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"      - {check_name}: {status}")
        
        if result['warnings']:
            print(f"   ⚠️  Warnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"      - {warning}")
    
    finally:
        # Cleanup
        os.unlink(temp_image_path)
    
    # Test 3: Test individual components
    print("\n3. Component Tests:")
    
    try:
        # Test EXIF analysis
        test_img = Image.new('RGB', (200, 200), 'white')
        exif_result = verifier._analyze_exif_data(test_img)
        print(f"   ✅ EXIF analysis: Working (has_camera_data: {exif_result['has_camera_data']})")
    except Exception as e:
        print(f"   ❌ EXIF analysis failed: {e}")
    
    try:
        # Test quality analysis
        quality_result = verifier._analyze_image_quality(test_img)
        print(f"   ✅ Quality analysis: Working (good_quality: {quality_result['good_quality']})")
    except Exception as e:
        print(f"   ❌ Quality analysis failed: {e}")
    
    try:
        # Test face detection (basic)
        face_result = verifier._basic_face_detection(test_img)
        print(f"   ✅ Face detection: Working (face_found: {face_result['face_found']})")
    except Exception as e:
        print(f"   ❌ Face detection failed: {e}")
    
    # Test 4: Library availability
    print("\n4. Library Availability:")
    
    try:
        import face_recognition
        print("   ✅ face_recognition: Available")
    except ImportError:
        print("   ❌ face_recognition: Not available")
    
    try:
        import cv2
        print("   ✅ opencv-python: Available")
    except ImportError:
        print("   ❌ opencv-python: Not available")
    
    try:
        import pytesseract
        print("   ✅ pytesseract: Available")
        # Test tesseract command
        try:
            pytesseract.get_tesseract_version()
            print("   ✅ tesseract command: Working")
        except:
            print("   ❌ tesseract command: Not working")
    except ImportError:
        print("   ❌ pytesseract: Not available")
    
    print("\n" + "=" * 50)
    print("🎉 Photo Verification Component Test Complete!")

if __name__ == "__main__":
    test_basic_verification()