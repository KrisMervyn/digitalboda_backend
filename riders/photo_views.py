"""
Photo Verification API Views
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Rider, Enumerator
from .photo_models import PhotoVerificationResult
import logging

logger = logging.getLogger('photo_verification')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_rider_photos(request, rider_id):
    """
    Run comprehensive photo verification for a rider
    
    POST /api/riders/{rider_id}/verify-photos/
    """
    try:
        rider = Rider.objects.get(pk=rider_id)
        
        # Check authorization - only enumerators and admins can verify
        if not (request.user.is_staff or hasattr(request.user, 'enumerator_profile')):
            return Response({
                'error': 'Only enumerators and admins can verify photos'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if rider has required photos
        if not rider.profile_photo or not rider.national_id_photo:
            return Response({
                'error': 'Rider must have both profile photo and ID document photo uploaded',
                'missing': {
                    'profile_photo': not bool(rider.profile_photo),
                    'id_document_photo': not bool(rider.national_id_photo)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run verification
        logger.info(f"Starting photo verification for rider {rider_id} by user {request.user.id}")
        result = rider.verify_photos(verified_by=request.user)
        
        if result['success']:
            # Send notification to rider about verification result
            # send_photo_verification_notification.delay(rider.id, result['status'])
            
            return Response({
                'success': True,
                'message': 'Photo verification completed',
                'rider_id': rider.id,
                'status': result['status'],
                'overall_score': result['overall_score'],
                'summary': result['summary'],
                'details': {
                    'profile_photo': {
                        'authentic': result['results']['profile_photo'].get('authentic'),
                        'confidence': result['results']['profile_photo'].get('confidence'),
                        'warnings': result['results']['profile_photo'].get('warnings', [])
                    },
                    'id_document': {
                        'authentic': result['results']['id_document'].get('authentic'),
                        'confidence': result['results']['id_document'].get('confidence'),
                        'warnings': result['results']['id_document'].get('warnings', [])
                    },
                    'face_match': {
                        'match': result['results']['face_match'].get('match'),
                        'confidence': result['results']['face_match'].get('confidence'),
                        'error': result['results']['face_match'].get('error')
                    },
                    'id_extraction': {
                        'success': result['results']['id_extraction'].get('success'),
                        'extracted_info': result['results']['id_extraction'].get('parsed_info', {})
                    }
                }
            })
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Rider.DoesNotExist:
        return Response({
            'error': 'Rider not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Photo verification failed for rider {rider_id}: {e}")
        return Response({
            'error': 'Photo verification failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_photo_verification_report(request, rider_id):
    """
    Get detailed photo verification report
    
    GET /api/riders/{rider_id}/photo-verification-report/
    """
    try:
        rider = Rider.objects.get(pk=rider_id)
        
        # Check authorization
        if not (request.user.is_staff or 
                hasattr(request.user, 'enumerator_profile') or
                request.user.username == f"rider_{rider.phone_number}"):
            return Response({
                'error': 'Unauthorized access to photo verification report'
            }, status=status.HTTP_403_FORBIDDEN)
        
        report = rider.get_photo_verification_report()
        
        return Response({
            'rider_id': rider.id,
            'rider_name': rider.full_name,
            'phone_number': rider.phone_number,
            'verification_report': report
        })
        
    except Rider.DoesNotExist:
        return Response({
            'error': 'Rider not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_photo_verification(request, rider_id):
    """
    Manually approve/reject photo verification
    
    POST /api/riders/{rider_id}/approve-photos/
    Body: {
        "action": "approve" | "reject" | "flag",
        "notes": "Optional reviewer notes"
    }
    """
    try:
        rider = Rider.objects.get(pk=rider_id)
        
        # Check authorization - only enumerators and admins
        if not (request.user.is_staff or hasattr(request.user, 'enumerator_profile')):
            return Response({
                'error': 'Only enumerators and admins can approve photo verification'
            }, status=status.HTTP_403_FORBIDDEN)
        
        action = request.data.get('action')
        notes = request.data.get('notes', '')
        
        if action not in ['approve', 'reject', 'flag']:
            return Response({
                'error': 'Invalid action. Must be: approve, reject, or flag'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Map actions to status
        status_map = {
            'approve': 'VERIFIED',
            'reject': 'REJECTED',
            'flag': 'FLAGGED'
        }
        
        new_status = status_map[action]
        
        # Update rider photo verification status
        rider.photo_verification_status = new_status
        rider.photo_verified_at = timezone.now()
        if hasattr(request.user, 'enumerator_profile'):
            rider.photo_verified_by = request.user.enumerator_profile
        rider.save(update_fields=['photo_verification_status', 'photo_verified_at', 'photo_verified_by'])
        
        # Update verification result
        try:
            verification_result = PhotoVerificationResult.objects.get(
                rider=rider, 
                photo_type='PROFILE'
            )
            verification_result.verification_status = new_status
            verification_result.reviewer_notes = notes
            verification_result.verified_by = request.user
            verification_result.verified_at = timezone.now() if action == 'approve' else None
            verification_result.save()
        except PhotoVerificationResult.DoesNotExist:
            # Create new verification result if none exists
            PhotoVerificationResult.objects.create(
                rider=rider,
                photo_type='PROFILE',
                verification_status=new_status,
                reviewer_notes=notes,
                verified_by=request.user,
                verified_at=timezone.now() if action == 'approve' else None
            )
        
        logger.info(f"Photo verification {action}d for rider {rider_id} by user {request.user.id}")
        
        return Response({
            'success': True,
            'message': f'Photo verification {action}d successfully',
            'rider_id': rider.id,
            'new_status': new_status,
            'notes': notes
        })
        
    except Rider.DoesNotExist:
        return Response({
            'error': 'Rider not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_riders_pending_photo_verification(request):
    """
    Get list of riders pending photo verification
    
    GET /api/enumerator/pending-photo-verification/
    """
    try:
        # Check authorization - only enumerators and admins
        if not (request.user.is_staff or hasattr(request.user, 'enumerator_profile')):
            return Response({
                'error': 'Only enumerators and admins can view pending verifications'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Filter based on user type
        if hasattr(request.user, 'enumerator_profile'):
            # Enumerator sees only their assigned riders
            enumerator = request.user.enumerator_profile
            riders = Rider.objects.filter(
                assigned_enumerator=enumerator,
                photo_verification_status__in=['PENDING', 'FLAGGED'],
                profile_photo__isnull=False,
                national_id_photo__isnull=False
            )
        else:
            # Admin sees all pending
            riders = Rider.objects.filter(
                photo_verification_status__in=['PENDING', 'FLAGGED'],
                profile_photo__isnull=False,
                national_id_photo__isnull=False
            )
        
        riders_data = []
        for rider in riders:
            riders_data.append({
                'id': rider.id,
                'full_name': rider.full_name,
                'phone_number': rider.phone_number,
                'unique_id': rider.unique_id,
                'photo_verification_status': rider.photo_verification_status,
                'face_match_score': rider.face_match_score,
                'status': rider.status,
                'assigned_enumerator': {
                    'id': rider.assigned_enumerator.id,
                    'unique_id': rider.assigned_enumerator.unique_id,
                    'name': f"{rider.assigned_enumerator.first_name} {rider.assigned_enumerator.last_name}"
                } if rider.assigned_enumerator else None,
                'created_at': rider.created_at.isoformat(),
                'has_photos': {
                    'profile_photo': bool(rider.profile_photo),
                    'id_document_photo': bool(rider.national_id_photo)
                }
            })
        
        return Response({
            'count': len(riders_data),
            'riders': riders_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching pending photo verifications: {e}")
        return Response({
            'error': 'Failed to fetch pending verifications',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def photo_verification_statistics(request):
    """
    Get photo verification statistics
    
    GET /api/admin/photo-verification-stats/
    """
    try:
        if not request.user.is_staff:
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from django.db.models import Count, Avg
        
        # Overall statistics
        total_riders = Rider.objects.count()
        riders_with_photos = Rider.objects.filter(
            profile_photo__isnull=False,
            national_id_photo__isnull=False
        ).count()
        
        # Verification status breakdown
        status_breakdown = Rider.objects.values('photo_verification_status').annotate(
            count=Count('id')
        )
        
        # Average face match scores
        avg_face_match = Rider.objects.filter(
            face_match_score__isnull=False
        ).aggregate(Avg('face_match_score'))
        
        # Recent verification results
        recent_verifications = PhotoVerificationResult.objects.filter(
            verified_at__isnull=False
        ).order_by('-verified_at')[:10]
        
        recent_data = []
        for verification in recent_verifications:
            recent_data.append({
                'rider_name': verification.rider.full_name,
                'status': verification.verification_status,
                'confidence_score': verification.confidence_score,
                'verified_at': verification.verified_at.isoformat(),
                'verified_by': verification.verified_by.username if verification.verified_by else None
            })
        
        return Response({
            'overview': {
                'total_riders': total_riders,
                'riders_with_photos': riders_with_photos,
                'photo_coverage_percentage': round((riders_with_photos / total_riders * 100), 2) if total_riders > 0 else 0
            },
            'verification_status': {item['photo_verification_status']: item['count'] for item in status_breakdown},
            'performance': {
                'average_face_match_score': round(avg_face_match['face_match_score__avg'] or 0, 3)
            },
            'recent_verifications': recent_data
        })
        
    except Exception as e:
        logger.error(f"Error generating photo verification statistics: {e}")
        return Response({
            'error': 'Failed to generate statistics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)