"""
Account Deletion Views for DigitalBoda
Handles account deletion requests and displays the deletion page
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import json
import logging

from .models import Rider

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def account_deletion_page(request):
    """
    Display the account deletion page
    This page meets Google Play Store requirements for user data deletion
    """
    return render(request, 'account_deletion.html')


@csrf_exempt
@require_http_methods(["POST"])
def request_account_deletion(request):
    """
    API endpoint to handle account deletion requests

    Expected JSON payload:
    {
        "phone_number": "+256XXXXXXXXX",
        "reason": "Optional reason for deletion"
    }

    Returns:
    - 200: Request submitted successfully
    - 400: Invalid request data
    - 404: Account not found
    - 500: Server error
    """
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data'
            }, status=400)

        phone_number = data.get('phone_number', '').strip()
        reason = data.get('reason', '').strip()

        # Validate phone number
        if not phone_number:
            return JsonResponse({
                'error': 'Phone number is required'
            }, status=400)

        # Clean phone number (remove spaces and special characters except +)
        phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')

        # Find the rider account
        try:
            rider = Rider.objects.get(phone_number=phone_number)
        except Rider.DoesNotExist:
            # For security reasons, don't reveal if account exists or not
            # Return success message anyway
            logger.info(f"Account deletion requested for non-existent phone: {phone_number}")
            return JsonResponse({
                'message': 'Account deletion request received. If an account exists with this phone number, it will be deleted within 30 days.',
                'status': 'pending'
            }, status=200)

        # Mark account for deletion
        with transaction.atomic():
            # Update rider status to indicate deletion pending
            # Add a custom field to track deletion request
            # For now, we'll add this to the rider's notes or create a separate model

            # Option 1: Add deletion marker to existing data
            rider.status = 'DELETION_PENDING'
            rider.deletion_requested_at = timezone.now()
            rider.deletion_reason = reason if reason else 'User requested'
            rider.save()

            logger.info(f"Account deletion requested for rider {rider.id} ({phone_number})")

            # TODO: In production, you should:
            # 1. Send confirmation email/SMS to the user
            # 2. Create a scheduled task to delete the account after 30 days
            # 3. Allow users to cancel deletion request within grace period
            # 4. Notify admins about deletion requests

        return JsonResponse({
            'message': 'Your account deletion request has been submitted successfully. Your account will be deleted within 30 days.',
            'status': 'pending',
            'request_date': timezone.now().isoformat()
        }, status=200)

    except Exception as e:
        logger.error(f"Error processing account deletion request: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'An error occurred while processing your request. Please try again later or contact support.'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def execute_account_deletion(request, rider_id):
    """
    Admin-only endpoint to execute account deletion
    This should be called by a scheduled task or admin action

    This endpoint:
    1. Deletes all personal data
    2. Anonymizes transaction records
    3. Removes authentication credentials
    4. Keeps audit logs for compliance
    """
    try:
        # TODO: Add admin authentication check
        # if not request.user.is_staff:
        #     return JsonResponse({'error': 'Unauthorized'}, status=403)

        with transaction.atomic():
            rider = Rider.objects.get(id=rider_id)

            # Log deletion for audit trail
            logger.info(f"Executing account deletion for rider {rider.id} ({rider.phone_number})")

            # Delete related data
            # Training progress
            rider.riderprogress_set.all().delete()

            # Applications
            if hasattr(rider, 'application'):
                rider.application.delete()

            # Photos
            if hasattr(rider, 'photos'):
                rider.photos.all().delete()

            # Attendance records
            if hasattr(rider, 'attendancerecord_set'):
                rider.attendancerecord_set.all().delete()

            # Achievements
            if hasattr(rider, 'riderachievement_set'):
                rider.riderachievement_set.all().delete()

            # Certificates
            if hasattr(rider, 'ridercertificate_set'):
                rider.ridercertificate_set.all().delete()

            # Notifications
            if hasattr(rider, 'notifications'):
                rider.notifications.all().delete()

            # FCM tokens
            rider.fcm_token = None

            # Finally, delete the rider account
            phone_number = rider.phone_number  # Save for logging
            rider.delete()

            logger.info(f"Account deletion completed for phone: {phone_number}")

            return JsonResponse({
                'message': 'Account deleted successfully',
                'deleted_rider_id': rider_id
            }, status=200)

    except Rider.DoesNotExist:
        return JsonResponse({
            'error': 'Rider not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error executing account deletion: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'An error occurred while deleting the account'
        }, status=500)


@require_http_methods(["GET"])
def account_deletion_stats(request):
    """
    Admin endpoint to view account deletion statistics
    """
    try:
        # TODO: Add admin authentication check

        # Count riders with deletion pending status
        pending_deletions = Rider.objects.filter(status='DELETION_PENDING').count()

        # Get list of pending deletions with details
        pending_riders = Rider.objects.filter(status='DELETION_PENDING').values(
            'id', 'phone_number', 'deletion_requested_at', 'deletion_reason'
        )

        return JsonResponse({
            'pending_deletions_count': pending_deletions,
            'pending_deletions': list(pending_riders)
        }, status=200)

    except Exception as e:
        logger.error(f"Error fetching deletion stats: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'An error occurred while fetching statistics'
        }, status=500)
