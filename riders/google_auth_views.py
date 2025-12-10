"""
Google Sign-In Authentication Views for DigitalBoda Backend
Handles Google OAuth authentication for rider registration and login
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from riders.models import Rider
import logging

logger = logging.getLogger(__name__)

def verify_google_token(firebase_token):
    """
    Verify Google ID token from Firebase

    Args:
        firebase_token (str): Firebase ID token to verify

    Returns:
        dict: Verification result with success status and user info
    """
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            firebase_token,
            requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID
        )

        # Token is valid - extract user information
        return {
            'success': True,
            'email': idinfo.get('email'),
            'email_verified': idinfo.get('email_verified'),
            'google_user_id': idinfo.get('sub'),
            'name': idinfo.get('name'),
            'picture': idinfo.get('picture'),
        }
    except Exception as e:
        logger.error(f"❌ Token verification failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@api_view(['POST'])
def google_login(request):
    """
    Login existing rider with Google Sign-In

    Endpoint: POST /api/auth/login/google/
    Headers: Authorization: Bearer {firebaseToken}
    Body: {
        "email": "user@gmail.com"
    }

    Returns:
        200: Success with user profile data
        404: User not found
        401: Invalid token
        400: Missing/invalid data
    """
    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response({
                'success': False,
                'error': 'Missing or invalid authorization token'
            }, status=401)

        firebase_token = auth_header.split('Bearer ')[1]
        email = request.data.get('email')

        if not email:
            return Response({
                'success': False,
                'error': 'Email is required'
            }, status=400)

        logger.info(f"🔵 Google login attempt for: {email}")

        # Verify the Firebase token
        verification = verify_google_token(firebase_token)
        if not verification['success']:
            logger.error(f"❌ Token verification failed for {email}")
            return Response({
                'success': False,
                'error': 'Invalid authentication token'
            }, status=401)

        # Check if email matches token email
        if verification['email'] != email:
            logger.error(f"❌ Email mismatch: {email} vs {verification['email']}")
            return Response({
                'success': False,
                'error': 'Email mismatch'
            }, status=400)

        # Find user by email
        try:
            rider = Rider.objects.get(email=email)

            logger.info(f"✅ Login successful for: {email}")

            # Return user profile
            return Response({
                'success': True,
                'data': {
                    'id': rider.id,
                    'email': rider.email,
                    'firstName': rider.first_name,
                    'lastName': rider.last_name,
                    'phoneNumber': rider.phone_number or '',
                    'profilePhotoUrl': rider.profile_photo_url or '',
                    'authProvider': rider.auth_provider,
                    'enumeratorId': rider.enumerator_id_input or '',
                    'status': rider.status,
                    'points': rider.points,
                    'uniqueId': rider.unique_id or '',
                }
            }, status=200)

        except Rider.DoesNotExist:
            logger.warning(f"⚠️ Account not found for: {email}")
            return Response({
                'success': False,
                'error': 'Account not found. Please register first.'
            }, status=404)

    except Exception as e:
        logger.error(f"💥 Google login error: {e}")
        return Response({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }, status=500)

@api_view(['POST'])
def google_register(request):
    """
    Register new rider with Google Sign-In

    Endpoint: POST /api/register/google/
    Headers: Authorization: Bearer {firebaseToken}
    Body: {
        "email": "user@gmail.com",
        "firstName": "John",
        "lastName": "Doe",
        "enumeratorId": "EN-2025-0001",
        "profilePhotoUrl": "https://..." (optional)
    }

    Returns:
        201: Success with created user profile
        409: Email already registered
        401: Invalid token
        400: Missing/invalid data
    """
    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response({
                'success': False,
                'error': 'Missing or invalid authorization token'
            }, status=401)

        firebase_token = auth_header.split('Bearer ')[1]

        # Get data from request
        email = request.data.get('email')
        first_name = request.data.get('firstName')
        last_name = request.data.get('lastName')
        enumerator_id = request.data.get('enumeratorId')
        profile_photo_url = request.data.get('profilePhotoUrl')

        # Validate required fields
        if not all([email, first_name, last_name, enumerator_id]):
            return Response({
                'success': False,
                'error': 'Email, first name, last name, and enumerator ID are required'
            }, status=400)

        logger.info(f"🔵 Google registration attempt for: {email}")

        # Verify the Firebase token
        verification = verify_google_token(firebase_token)
        if not verification['success']:
            logger.error(f"❌ Token verification failed for {email}")
            return Response({
                'success': False,
                'error': 'Invalid authentication token'
            }, status=401)

        # Check if email matches token email
        if verification['email'] != email:
            logger.error(f"❌ Email mismatch: {email} vs {verification['email']}")
            return Response({
                'success': False,
                'error': 'Email mismatch'
            }, status=400)

        # Check if email already exists
        if Rider.objects.filter(email=email).exists():
            logger.warning(f"⚠️ Email already registered: {email}")
            return Response({
                'success': False,
                'error': 'This email is already registered'
            }, status=409)

        # Create new rider
        rider = Rider.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            enumerator_id_input=enumerator_id,
            google_user_id=verification['google_user_id'],
            profile_photo_url=profile_photo_url or verification.get('picture', ''),
            is_email_verified=verification.get('email_verified', False),
            auth_provider='google',
            status=Rider.REGISTERED
        )

        # Generate unique ID
        rider.generate_unique_id()

        logger.info(f"✅ New rider registered via Google: {email} (ID: {rider.unique_id})")

        # Return user profile
        return Response({
            'success': True,
            'data': {
                'id': rider.id,
                'email': rider.email,
                'firstName': rider.first_name,
                'lastName': rider.last_name,
                'phoneNumber': rider.phone_number or '',
                'profilePhotoUrl': rider.profile_photo_url or '',
                'authProvider': rider.auth_provider,
                'enumeratorId': rider.enumerator_id_input,
                'status': rider.status,
                'points': rider.points,
                'uniqueId': rider.unique_id or '',
            }
        }, status=201)

    except Exception as e:
        logger.error(f"💥 Google registration error: {e}")
        return Response({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }, status=500)
