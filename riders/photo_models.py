"""
Photo Verification Models
Database models for storing photo verification results
"""

from django.db import models
from django.contrib.auth.models import User

class PhotoVerificationResult(models.Model):
    """Store results of photo verification"""
    
    PHOTO_TYPES = [
        ('PROFILE', 'Profile Photo'),
        ('ID_DOCUMENT', 'ID Document'),
    ]
    
    VERIFICATION_STATUSES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('FLAGGED', 'Flagged for Review'),
    ]
    
    # Relationships
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE, related_name='photo_verifications')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Photo details
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPES)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUSES, default='PENDING')
    
    # Verification results
    is_authentic = models.BooleanField(null=True, help_text="Overall authenticity determination")
    confidence_score = models.FloatField(null=True, help_text="Confidence score (0-1)")
    face_match_score = models.FloatField(null=True, help_text="Face matching confidence (0-1)")
    
    # Detailed results (JSON)
    verification_details = models.JSONField(default=dict, help_text="Detailed verification results")
    warnings = models.JSONField(default=list, help_text="Verification warnings")
    
    # Review information
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection")
    reviewer_notes = models.TextField(blank=True, help_text="Additional notes from reviewer")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['rider', 'photo_type']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rider', 'verification_status']),
            models.Index(fields=['verification_status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.rider.full_name} - {self.photo_type} - {self.verification_status}"


# Add photo verification methods to the Rider model
def add_photo_verification_methods():
    """Add photo verification methods to the existing Rider model"""
    
    from .models import Rider
    from .services.photo_verification import PhotoVerificationService
    from django.utils import timezone
    import logging
    
    logger = logging.getLogger('photo_verification')
    
    def verify_photos(self, verified_by=None):
        """
        Run comprehensive photo verification for rider
        
        Args:
            verified_by: User performing the verification
            
        Returns:
            dict: Verification results
        """
        if not self.profile_photo or not self.national_id_photo:
            return {
                'success': False,
                'error': 'Missing required photos (profile_photo and national_id_photo)'
            }
        
        try:
            verifier = PhotoVerificationService()
            results = {}
            
            # 1. Verify profile photo authenticity
            logger.info(f"Verifying profile photo for rider {self.id}")
            profile_result = verifier.verify_photo_authenticity(self.profile_photo.path)
            results['profile_photo'] = profile_result
            
            # 2. Verify ID document authenticity  
            logger.info(f"Verifying ID document for rider {self.id}")
            id_result = verifier.verify_photo_authenticity(self.national_id_photo.path)
            results['id_document'] = id_result
            
            # 3. Compare faces between photos
            logger.info(f"Comparing faces for rider {self.id}")
            face_comparison = verifier.compare_faces(
                self.profile_photo.path, 
                self.national_id_photo.path
            )
            results['face_match'] = face_comparison
            
            # 4. Extract information from ID document
            logger.info(f"Extracting ID information for rider {self.id}")
            id_extraction = verifier.extract_id_information(self.national_id_photo.path)
            results['id_extraction'] = id_extraction
            
            # 5. Cross-verify extracted ID with provided ID (if available)
            results['id_cross_verification'] = None
            if (id_extraction.get('success') and 
                id_extraction.get('parsed_info', {}).get('id_number') and 
                self.national_id_encrypted):
                
                try:
                    provided_id = self.get_national_id(verified_by, "Photo verification cross-check")
                    extracted_id = id_extraction['parsed_info']['id_number']
                    
                    results['id_cross_verification'] = {
                        'extracted_id': extracted_id,
                        'provided_id': provided_id,
                        'match': extracted_id == provided_id,
                        'similarity': self._calculate_id_similarity(extracted_id, provided_id)
                    }
                except:
                    results['id_cross_verification'] = {
                        'error': 'Could not access provided ID for comparison'
                    }
            
            # 6. Calculate overall verification score
            overall_score = self._calculate_photo_verification_score(results)
            
            # 7. Determine verification status
            if overall_score >= 0.8:
                verification_status = 'VERIFIED'
            elif overall_score >= 0.5:
                verification_status = 'FLAGGED'
            else:
                verification_status = 'REJECTED'
            
            # 8. Update rider photo verification status
            self.photo_verification_status = verification_status
            self.face_match_score = face_comparison.get('confidence', 0)
            self.photo_verified_at = timezone.now()
            if hasattr(verified_by, 'enumerator_profile'):
                self.photo_verified_by = verified_by.enumerator_profile
            self.save(update_fields=[
                'photo_verification_status', 
                'face_match_score', 
                'photo_verified_at',
                'photo_verified_by'
            ])
            
            # 9. Save detailed verification results
            PhotoVerificationResult.objects.update_or_create(
                rider=self,
                photo_type='PROFILE',
                defaults={
                    'verification_status': verification_status,
                    'is_authentic': profile_result.get('authentic', False),
                    'confidence_score': profile_result.get('confidence', 0),
                    'face_match_score': face_comparison.get('confidence', 0),
                    'verification_details': results,
                    'warnings': profile_result.get('warnings', []),
                    'verified_by': verified_by,
                    'verified_at': timezone.now() if verification_status == 'VERIFIED' else None
                }
            )
            
            logger.info(f"Photo verification completed for rider {self.id}: {verification_status} (score: {overall_score:.2f})")
            
            return {
                'success': True,
                'overall_score': overall_score,
                'status': verification_status,
                'results': results,
                'summary': {
                    'profile_authentic': profile_result.get('authentic', False),
                    'id_authentic': id_result.get('authentic', False),
                    'faces_match': face_comparison.get('match', False),
                    'id_extracted': id_extraction.get('success', False),
                    'cross_verified': results['id_cross_verification'].get('match', False) if results['id_cross_verification'] else None
                }
            }
            
        except Exception as e:
            logger.error(f"Photo verification failed for rider {self.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_photo_verification_score(self, results):
        """Calculate overall photo verification score"""
        score = 0.0
        
        # Profile photo authenticity (25%)
        if results.get('profile_photo', {}).get('authentic'):
            score += 0.25
        
        # ID document authenticity (25%)
        if results.get('id_document', {}).get('authentic'):
            score += 0.25
        
        # Face matching (30%)
        face_confidence = results.get('face_match', {}).get('confidence', 0)
        score += face_confidence * 0.3
        
        # ID extraction success (10%)
        if results.get('id_extraction', {}).get('success'):
            score += 0.1
        
        # ID cross-verification (10%)
        cross_verification = results.get('id_cross_verification')
        if cross_verification and cross_verification.get('match'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_id_similarity(self, id1, id2):
        """Calculate similarity between two ID numbers"""
        if not id1 or not id2:
            return 0.0
        
        # Simple character-by-character comparison
        matches = sum(c1 == c2 for c1, c2 in zip(id1, id2))
        max_length = max(len(id1), len(id2))
        
        return matches / max_length if max_length > 0 else 0.0
    
    def get_photo_verification_report(self):
        """Get comprehensive photo verification report"""
        try:
            verification = PhotoVerificationResult.objects.get(rider=self, photo_type='PROFILE')
            
            return {
                'status': self.photo_verification_status,
                'overall_authentic': verification.is_authentic,
                'confidence_score': verification.confidence_score,
                'face_match_score': verification.face_match_score,
                'verified_at': verification.verified_at,
                'verified_by': verification.verified_by.username if verification.verified_by else None,
                'warnings': verification.warnings,
                'details': verification.verification_details,
                'reviewer_notes': verification.reviewer_notes
            }
        except PhotoVerificationResult.DoesNotExist:
            return {
                'status': 'NOT_VERIFIED',
                'message': 'No verification results found'
            }
    
    # Add methods to Rider class
    Rider.verify_photos = verify_photos
    Rider._calculate_photo_verification_score = _calculate_photo_verification_score
    Rider._calculate_id_similarity = _calculate_id_similarity
    Rider.get_photo_verification_report = get_photo_verification_report

# Call the function to add methods
add_photo_verification_methods()