"""
Comprehensive Photo Verification Service
Handles photo authenticity, face matching, and ID document verification
"""

import logging
import hashlib
import numpy as np
from PIL import Image, ImageFilter, ImageStat, ExifTags
from django.core.files.storage import default_storage
from django.conf import settings
import io
import os

logger = logging.getLogger('photo_verification')

class PhotoVerificationService:
    """
    Service for comprehensive photo verification including:
    - Photo authenticity detection
    - Face matching between profile and ID photos
    - OCR text extraction from ID documents
    - Anti-fraud measures
    """
    
    def __init__(self):
        self.confidence_threshold = 0.6
        self.face_match_threshold = 0.4  # Lower = more strict
        self.min_image_size = (300, 300)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
    def verify_photo_authenticity(self, image_path):
        """
        Comprehensive photo authenticity verification
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            dict: Authenticity results with confidence score
        """
        try:
            if isinstance(image_path, str):
                image = Image.open(image_path)
            else:
                # Handle Django file objects
                image = Image.open(image_path)
            
            results = {
                'authentic': False,
                'confidence': 0.0,
                'checks': {},
                'warnings': [],
                'details': {}
            }
            
            # Check 1: Basic image properties
            width, height = image.size
            results['details']['resolution'] = f"{width}x{height}"
            
            if width < self.min_image_size[0] or height < self.min_image_size[1]:
                results['warnings'].append(f"Low resolution: {width}x{height}")
                results['checks']['resolution'] = False
            else:
                results['checks']['resolution'] = True
            
            # Check 2: File format and compression
            results['details']['format'] = image.format
            results['details']['mode'] = image.mode
            
            # Check 3: EXIF data analysis
            exif_check = self._analyze_exif_data(image)
            results['checks']['exif'] = exif_check['has_camera_data']
            results['details']['exif'] = exif_check
            
            if not exif_check['has_camera_data']:
                results['warnings'].append("No camera metadata found")
            
            # Check 4: Image quality analysis
            quality_check = self._analyze_image_quality(image)
            results['checks']['quality'] = quality_check['good_quality']
            results['details']['quality'] = quality_check
            
            # Check 5: Detect obvious manipulations
            manipulation_check = self._detect_basic_manipulations(image)
            results['checks']['manipulation'] = not manipulation_check['suspicious']
            results['details']['manipulation'] = manipulation_check
            
            if manipulation_check['suspicious']:
                results['warnings'].extend(manipulation_check['reasons'])
            
            # Check 6: Face detection (basic)
            face_check = self._basic_face_detection(image)
            results['checks']['face_detected'] = face_check['face_found']
            results['details']['face'] = face_check
            
            # Calculate overall authenticity score
            authenticity_score = self._calculate_authenticity_score(results['checks'])
            results['confidence'] = authenticity_score
            results['authentic'] = authenticity_score >= self.confidence_threshold
            
            return results
            
        except Exception as e:
            logger.error(f"Photo authenticity check failed: {e}")
            return {
                'authentic': False,
                'confidence': 0.0,
                'error': str(e),
                'checks': {},
                'warnings': ['Verification failed'],
                'details': {}
            }
    
    def compare_faces(self, profile_photo_path, id_photo_path):
        """
        Compare faces between profile photo and ID document
        
        Args:
            profile_photo_path: Path to profile photo
            id_photo_path: Path to ID document photo
            
        Returns:
            dict: Face comparison results
        """
        try:
            # Try to import face_recognition
            import face_recognition
            
            # Load images
            profile_image = face_recognition.load_image_file(profile_photo_path)
            id_image = face_recognition.load_image_file(id_photo_path)
            
            # Find faces
            profile_encodings = face_recognition.face_encodings(profile_image)
            id_encodings = face_recognition.face_encodings(id_image)
            
            if not profile_encodings:
                return {
                    'match': False,
                    'confidence': 0.0,
                    'error': 'No face detected in profile photo'
                }
            
            if not id_encodings:
                return {
                    'match': False,
                    'confidence': 0.0,
                    'error': 'No face detected in ID photo'
                }
            
            # Compare faces
            matches = face_recognition.compare_faces(
                profile_encodings, 
                id_encodings[0], 
                tolerance=self.face_match_threshold
            )
            
            # Calculate distances (lower = more similar)
            face_distances = face_recognition.face_distance(
                profile_encodings, 
                id_encodings[0]
            )
            
            is_match = any(matches)
            confidence = 1 - min(face_distances) if len(face_distances) > 0 else 0
            
            return {
                'match': is_match,
                'confidence': float(confidence),
                'face_distance': float(min(face_distances)) if len(face_distances) > 0 else 1.0,
                'faces_found': {
                    'profile': len(profile_encodings),
                    'id_document': len(id_encodings)
                }
            }
            
        except ImportError:
            logger.warning("face_recognition not available, using basic comparison")
            return self._basic_face_comparison(profile_photo_path, id_photo_path)
        except Exception as e:
            logger.error(f"Face comparison failed: {e}")
            return {
                'match': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def extract_id_information(self, id_photo_path):
        """
        Extract text information from ID document using OCR
        
        Args:
            id_photo_path: Path to ID document image
            
        Returns:
            dict: Extracted information
        """
        try:
            import pytesseract
            
            image = Image.open(id_photo_path)
            
            # Preprocess image for better OCR
            image = image.convert('L')  # Grayscale
            image = image.filter(ImageFilter.MedianFilter())  # Reduce noise
            
            # Apply sharpening
            image = image.filter(ImageFilter.UnsharpMask())
            
            # Extract text
            extracted_text = pytesseract.image_to_string(
                image, 
                config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            
            # Parse Uganda-specific patterns
            parsed_info = self._parse_uganda_id_text(extracted_text)
            
            return {
                'success': True,
                'raw_text': extracted_text,
                'parsed_info': parsed_info,
                'confidence': self._calculate_ocr_confidence(extracted_text, parsed_info)
            }
            
        except ImportError:
            logger.warning("pytesseract not available")
            return {
                'success': False,
                'error': 'OCR not available - install pytesseract'
            }
        except Exception as e:
            logger.error(f"ID information extraction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_exif_data(self, image):
        """Analyze EXIF data for authenticity indicators"""
        try:
            exif = image._getexif()
            
            if not exif:
                return {
                    'has_camera_data': False,
                    'camera_make': None,
                    'camera_model': None,
                    'datetime': None,
                    'gps_info': False
                }
            
            # Extract relevant EXIF tags
            exif_dict = {}
            for tag, value in exif.items():
                if tag in ExifTags.TAGS:
                    exif_dict[ExifTags.TAGS[tag]] = value
            
            return {
                'has_camera_data': True,
                'camera_make': exif_dict.get('Make'),
                'camera_model': exif_dict.get('Model'),
                'datetime': exif_dict.get('DateTime'),
                'gps_info': 'GPSInfo' in exif_dict,
                'software': exif_dict.get('Software'),
                'flash': exif_dict.get('Flash') is not None
            }
            
        except Exception:
            return {
                'has_camera_data': False,
                'error': 'EXIF analysis failed'
            }
    
    def _analyze_image_quality(self, image):
        """Analyze image quality metrics"""
        try:
            # Convert to grayscale for analysis
            gray = image.convert('L')
            array = np.array(gray)
            
            # Calculate sharpness using Laplacian variance
            laplacian = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]])
            convolved = np.absolute(np.convolve(array.flatten(), laplacian.flatten(), mode='same'))
            sharpness = convolved.var()
            
            # Normalize sharpness score (0-1)
            sharpness_score = min(sharpness / 1000, 1.0)
            
            # Calculate brightness and contrast
            stat = ImageStat.Stat(gray)
            brightness = stat.mean[0] / 255.0
            contrast = stat.stddev[0] / 255.0
            
            # Overall quality score
            quality_score = (sharpness_score * 0.5) + (contrast * 0.3) + ((1 - abs(brightness - 0.5)) * 0.2)
            
            return {
                'good_quality': quality_score > 0.4,
                'sharpness': sharpness_score,
                'brightness': brightness,
                'contrast': contrast,
                'overall_score': quality_score
            }
            
        except Exception as e:
            logger.error(f"Image quality analysis failed: {e}")
            return {
                'good_quality': False,
                'error': str(e)
            }
    
    def _detect_basic_manipulations(self, image):
        """Detect obvious image manipulations"""
        warnings = []
        suspicious = False
        
        try:
            # Check for unusual aspect ratios (indicating cropping/resizing)
            width, height = image.size
            aspect_ratio = width / height
            
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                warnings.append("Unusual aspect ratio detected")
                suspicious = True
            
            # Check for low quality/compression artifacts
            if image.format == 'JPEG':
                # Basic JPEG quality estimation
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=95)
                high_quality_size = buffer.tell()
                
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=50)
                low_quality_size = buffer.tell()
                
                # If the image is closer to low quality, it may be re-compressed
                if abs(high_quality_size - len(image.tobytes())) > abs(low_quality_size - len(image.tobytes())):
                    warnings.append("Possible re-compression detected")
            
            return {
                'suspicious': suspicious,
                'reasons': warnings,
                'aspect_ratio': aspect_ratio
            }
            
        except Exception as e:
            logger.error(f"Manipulation detection failed: {e}")
            return {
                'suspicious': False,
                'reasons': ['Analysis failed'],
                'error': str(e)
            }
    
    def _basic_face_detection(self, image):
        """Basic face detection without face_recognition library"""
        try:
            import cv2
            
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Use Haar cascade for face detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            return {
                'face_found': len(faces) > 0,
                'face_count': len(faces),
                'faces': faces.tolist() if len(faces) > 0 else []
            }
            
        except ImportError:
            # Fallback: very basic face detection using image analysis
            return self._fallback_face_detection(image)
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return {
                'face_found': False,
                'error': str(e)
            }
    
    def _fallback_face_detection(self, image):
        """Fallback face detection using basic image analysis"""
        try:
            # Very basic heuristic: look for skin-colored regions
            width, height = image.size
            
            # Sample pixels from center region where face would likely be
            center_x, center_y = width // 2, height // 2
            sample_size = min(width, height) // 4
            
            region = image.crop((
                center_x - sample_size // 2,
                center_y - sample_size // 2,
                center_x + sample_size // 2,
                center_y + sample_size // 2
            ))
            
            # Simple skin tone detection
            pixels = list(region.getdata())
            skin_pixels = 0
            
            for r, g, b in pixels:
                # Basic skin tone range (very rough)
                if 95 <= r <= 255 and 40 <= g <= 195 and 20 <= b <= 155:
                    if r > g and r > b:  # More red than green/blue
                        skin_pixels += 1
            
            skin_ratio = skin_pixels / len(pixels)
            
            return {
                'face_found': skin_ratio > 0.1,  # At least 10% skin-like pixels
                'confidence': skin_ratio,
                'method': 'fallback_skin_detection'
            }
            
        except Exception:
            return {
                'face_found': False,
                'method': 'fallback_failed'
            }
    
    def _basic_face_comparison(self, profile_photo_path, id_photo_path):
        """Basic face comparison without face_recognition"""
        try:
            # Load and analyze both images
            profile_img = Image.open(profile_photo_path)
            id_img = Image.open(id_photo_path)
            
            # Basic comparison using image histograms
            profile_hist = profile_img.histogram()
            id_hist = id_img.histogram()
            
            # Calculate histogram similarity (very basic)
            similarity = sum((a - b) ** 2 for a, b in zip(profile_hist, id_hist))
            similarity = 1 / (1 + similarity / 1000000)  # Normalize
            
            return {
                'match': similarity > 0.5,
                'confidence': similarity,
                'method': 'basic_histogram_comparison',
                'warning': 'This is a basic comparison - install face_recognition for accurate matching'
            }
            
        except Exception as e:
            return {
                'match': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _parse_uganda_id_text(self, text):
        """Parse Uganda-specific patterns from OCR text"""
        import re
        
        parsed = {
            'id_number': None,
            'name': None,
            'date_of_birth': None,
            'sex': None
        }
        
        # Clean text and handle multiline
        text = text.upper().strip()
        # Replace line breaks with spaces for better pattern matching
        text_single_line = ' '.join(text.split())
        
        # Uganda ID number pattern (more flexible)
        # Try various ID patterns for Uganda National IDs
        id_patterns = [
            r'(CF|CM|CS)\d{2}[A-Z0-9]{8,12}',  # Standard pattern with CF/CM/CS prefix
            r'[A-Z]{2}\d{2}[A-Z0-9]{8,12}',     # Two letters, two digits, then alphanumeric  
            r'\b[A-Z]{2}[0-9A-Z]{12,16}\b',     # Any pattern starting with 2 letters
        ]
        
        # Search in both original multiline and single line versions
        for text_version in [text, text_single_line]:
            for pattern in id_patterns:
                id_match = re.search(pattern, text_version)
                if id_match:
                    candidate_id = id_match.group(0)
                    # Validate it's not just common words
                    if (len(candidate_id) >= 10 and 
                        not any(word in candidate_id for word in ['NATIONAL', 'CARD', 'REPUBLIC', 'UGANDA', 'IDCARD'])):
                        parsed['id_number'] = candidate_id
                        break
            if parsed['id_number']:  # If found, stop searching
                break
        
        # Name patterns
        name_patterns = [
            r'NAME[S]?\s*[:]\s*([A-Z\s]+)',
            r'NAMES\s+([A-Z\s]+)',
            r'([A-Z]+\s+[A-Z]+)'  # Two capitalized words
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 50:  # Reasonable name length
                    parsed['name'] = name
                    break
        
        # Date of birth patterns
        dob_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'DOB\s*[:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text)
            if match:
                parsed['date_of_birth'] = match.group(1)
                break
        
        # Sex
        if re.search(r'\bMALE\b', text):
            parsed['sex'] = 'MALE'
        elif re.search(r'\bFEMALE\b', text):
            parsed['sex'] = 'FEMALE'
        
        return parsed
    
    def _calculate_ocr_confidence(self, raw_text, parsed_info):
        """Calculate confidence in OCR results"""
        if not raw_text:
            return 0.0
        
        confidence = 0.0
        
        # Points for finding key information
        if parsed_info.get('id_number'):
            confidence += 0.4
        if parsed_info.get('name'):
            confidence += 0.3
        if parsed_info.get('date_of_birth'):
            confidence += 0.2
        if parsed_info.get('sex'):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_authenticity_score(self, checks):
        """Calculate overall authenticity score from individual checks"""
        weights = {
            'resolution': 0.15,
            'exif': 0.25,
            'quality': 0.25,
            'manipulation': 0.20,
            'face_detected': 0.15
        }
        
        score = 0.0
        total_weight = 0.0
        
        for check_name, passed in checks.items():
            if check_name in weights:
                weight = weights[check_name]
                score += weight if passed else 0
                total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.0