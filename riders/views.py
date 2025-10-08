from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import models
from datetime import timedelta
from rest_framework.authtoken.models import Token
from .models import (Rider, Lesson, RiderProgress, RiderApplication, Enumerator, 
                     DigitalLiteracyModule, SessionSchedule, SessionAttendance, 
                     DigitalLiteracyProgress, Stage, StageRiderAssignment, DigitalSkillsPoints)
from .services.notification_service import FCMService

def verify_firebase_token(request):
    """Helper function to verify Firebase ID token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    # For development, accept any Bearer token that looks valid
    # In production, you'd verify with Firebase Admin SDK
    token = auth_header.split(' ')[1]
    if len(token) > 20:  # More lenient token format check for development
        return {'phone_number': None, 'verified': True}  # Mock decoded token
    return None

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def register_rider(request):
    # Handle GET requests for testing
    if request.method == 'GET':
        return Response({
            'message': 'Registration endpoint is working. Use POST to register.',
            'required_fields': ['phoneNumber'],
            'optional_fields': ['fullName']
        })
    
    print(f"🔥 Registration request received: {request.method}")
    print(f"📱 Request data: {request.data}")
    print(f"🔐 Headers: {dict(request.headers)}")
    
    # Verify Firebase token
    decoded_token = verify_firebase_token(request)
    if not decoded_token:
        return Response(
            {'error': 'Invalid authentication token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    phone_number = request.data.get('phoneNumber')
    first_name = request.data.get('firstName', '')
    last_name = request.data.get('lastName', '')
    enumerator_id = request.data.get('enumeratorId', '')
    experience_level = request.data.get('experienceLevel', 'New Rider')
    
    if not phone_number:
        return Response(
            {'error': 'Phone number is required.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not first_name or not last_name:
        return Response(
            {'error': 'First name and last name are required.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not enumerator_id:
        return Response(
            {'error': 'Enumerator ID is required.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find enumerator by unique_id
    try:
        enumerator = Enumerator.objects.get(unique_id=enumerator_id, status=Enumerator.ACTIVE)
    except Enumerator.DoesNotExist:
        return Response(
            {'error': 'Invalid enumerator ID or enumerator is inactive.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Map experience level from UI to model
    experience_map = {
        'New Rider': Rider.NEW_RIDER,
        'Experienced Rider': Rider.EXPERIENCED_RIDER,
    }
    experience_code = experience_map.get(experience_level, Rider.NEW_RIDER)
    
    # Create or get existing rider
    rider, created = Rider.objects.get_or_create(
        phone_number=phone_number,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'experience_level': experience_code,
            'status': Rider.REGISTERED,
            'points': 0,
            'assigned_enumerator': enumerator,
            'enumerator_id_input': enumerator_id,
        }
    )
    
    if created:
        return Response({
            'message': 'Rider registered successfully!', 
            'riderId': rider.id,
            'firstName': rider.first_name,
            'lastName': rider.last_name,
            'fullName': rider.full_name,
            'points': rider.points,
            'status': rider.status,
            'experienceLevel': rider.get_experience_level_display(),
            'nextStep': 'onboarding'
        }, status=status.HTTP_201_CREATED)
    else:
        # Update existing rider info if needed
        if rider.first_name != first_name or rider.last_name != last_name:
            rider.first_name = first_name
            rider.last_name = last_name
            rider.experience_level = experience_code
            rider.save()
            
        return Response({
            'message': 'Welcome back!',
            'riderId': rider.id,
            'firstName': rider.first_name,
            'lastName': rider.last_name,
            'fullName': rider.full_name,
            'points': rider.points,
            'status': rider.status,
            'experienceLevel': rider.get_experience_level_display(),
            'uniqueId': rider.unique_id,
            'nextStep': 'training' if rider.status == Rider.APPROVED else 'pending_approval'
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_lessons(request):
    lessons = Lesson.objects.all()
    lessons_data = [
        {
            'id': lesson.id,
            'title': lesson.title,
            'description': lesson.description,
            'order': lesson.order,
            'points_reward': lesson.points_reward
        }
        for lesson in lessons
    ]
    return Response(lessons_data)

@api_view(['GET'])
@permission_classes([AllowAny])
def rider_profile(request, phone_number):
    # Verify Firebase token
    decoded_token = verify_firebase_token(request)
    if not decoded_token:
        return Response(
            {'error': 'Invalid authentication token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        rider = Rider.objects.get(phone_number=phone_number)
        
        # Get reference number if application exists
        reference_number = None
        try:
            application = rider.application
            reference_number = application.reference_number
        except RiderApplication.DoesNotExist:
            pass
        
        return Response({
            'id': rider.id,
            'phoneNumber': rider.phone_number,
            'phone_number': rider.phone_number,  # Compatibility
            'firstName': rider.first_name,
            'lastName': rider.last_name,
            'first_name': rider.first_name,  # Compatibility
            'last_name': rider.last_name,    # Compatibility
            'fullName': rider.full_name,
            'full_name': rider.full_name,    # Compatibility
            'status': rider.status,
            'experienceLevel': rider.get_experience_level_display(),
            'experience_level': rider.get_experience_level_display(),  # Compatibility
            'points': rider.points,
            'unique_id': rider.unique_id,
            'uniqueId': rider.unique_id,     # Compatibility
            'reference_number': reference_number,
            'referenceNumber': reference_number,  # Compatibility
            'rejection_reason': rider.rejection_reason,
            'rejectionReason': rider.rejection_reason,  # Compatibility
            'createdAt': rider.created_at,
            'created_at': rider.created_at   # Compatibility
        })
    except Rider.DoesNotExist:
        return Response(
            {'error': 'Rider not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_onboarding(request):
    """Submit rider onboarding information including photos"""
    print(f"📸 Onboarding submission with data: {list(request.data.keys())}")
    print(f"📁 Files: {list(request.FILES.keys())}")
    
    # Verify Firebase token
    decoded_token = verify_firebase_token(request)
    if not decoded_token:
        return Response(
            {'error': 'Invalid authentication token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    phone_number = request.data.get('phoneNumber')
    if not phone_number:
        return Response(
            {'error': 'Phone number is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rider = Rider.objects.get(phone_number=phone_number)
        
        # Update rider with onboarding information
        age_bracket = request.data.get('ageBracket')
        age = request.data.get('age')  # Keep for backward compatibility
        
        # Use age bracket if provided, otherwise convert age to bracket
        if age_bracket:
            rider.age_bracket = age_bracket
        elif age:
            # Convert exact age to bracket for backward compatibility
            age = int(age)
            if 18 <= age <= 23:
                rider.age_bracket = '18-23'
            elif 24 <= age <= 29:
                rider.age_bracket = '24-29'
            elif 30 <= age <= 35:
                rider.age_bracket = '30-35'
            elif 36 <= age <= 41:
                rider.age_bracket = '36-41'
            elif 42 <= age <= 47:
                rider.age_bracket = '42-47'
            elif 48 <= age <= 53:
                rider.age_bracket = '48-53'
            elif 54 <= age <= 59:
                rider.age_bracket = '54-59'
            elif 60 <= age <= 65:
                rider.age_bracket = '60-65'
            else:
                rider.age_bracket = '66+'
        
        rider.age = age  # Keep for migration purposes
        rider.location = request.data.get('location')
        rider.national_id_number = request.data.get('nationalIdNumber')
        
        # Handle photo uploads
        if 'profile_photo' in request.FILES:
            rider.profile_photo = request.FILES['profile_photo']
            print(f"📸 Profile photo uploaded: {rider.profile_photo.name}")
        
        if 'national_id_photo' in request.FILES:
            rider.national_id_photo = request.FILES['national_id_photo']
            print(f"🆔 ID photo uploaded: {rider.national_id_photo.name}")
        
        # Save rider first so files are available for OCR
        rider.save()
        
        # Validate ID number against uploaded ID photo using OCR
        id_validation_passed = True
        id_validation_message = ""
        if rider.national_id_photo and rider.national_id_number:
            try:
                from .services.photo_verification import PhotoVerificationService
                verification_service = PhotoVerificationService()
                
                # Extract text from ID photo
                ocr_result = verification_service.extract_id_information(rider.national_id_photo.path)
                print(f"🔍 OCR Result: {ocr_result}")
                
                if ocr_result.get('success'):
                    extracted_id = ocr_result.get('parsed_info', {}).get('id_number')
                    entered_id = rider.national_id_number.strip().upper()
                    
                    if extracted_id:
                        extracted_id = extracted_id.strip().upper()
                        
                        # Use more flexible ID matching that accounts for OCR errors
                        def calculate_similarity(str1, str2):
                            """Calculate similarity percentage between two strings"""
                            if not str1 or not str2:
                                return 0
                            # Calculate character match percentage
                            matches = sum(1 for a, b in zip(str1, str2) if a == b)
                            max_len = max(len(str1), len(str2))
                            return (matches / max_len * 100) if max_len > 0 else 0
                        
                        # Check multiple validation methods
                        exact_match = entered_id == extracted_id
                        substring_match = entered_id in extracted_id or extracted_id in entered_id
                        similarity_score = calculate_similarity(entered_id, extracted_id)
                        
                        # More lenient validation: pass if any condition is met
                        validation_passed = (
                            exact_match or 
                            substring_match or 
                            similarity_score >= 60 or  # Allow 60% similarity for OCR errors
                            len(entered_id) >= 10  # Trust user input for valid-looking IDs
                        )
                        
                        if not validation_passed:
                            # Only fail if the IDs are completely different and low similarity
                            id_validation_passed = False
                            id_validation_message = f"ID number mismatch: Entered '{entered_id}' but photo shows '{extracted_id}' (Similarity: {similarity_score:.1f}%)"
                            print(f"❌ ID validation failed: {id_validation_message}")
                        else:
                            validation_method = "exact match" if exact_match else "substring match" if substring_match else f"similarity match ({similarity_score:.1f}%)"
                            print(f"✅ ID validation passed: '{entered_id}' matches photo via {validation_method}")
                    else:
                        print(f"⚠️ Could not extract ID from photo, allowing submission")
                else:
                    print(f"⚠️ OCR failed, allowing submission: {ocr_result.get('error')}")
            except Exception as e:
                print(f"⚠️ ID validation error, allowing submission: {e}")
        
        # Return error if ID validation failed
        if not id_validation_passed:
            return Response({
                'success': False,
                'error': id_validation_message,
                'validation_error': 'id_number_mismatch'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Move rider to onboarding complete status
        rider.status = Rider.PENDING_APPROVAL
        rider.save()
        
        # Create RiderApplication for admin review
        from .models import RiderApplication
        application, created = RiderApplication.objects.get_or_create(
            rider=rider,
            defaults={'submitted_at': timezone.now()}
        )
        
        # Automatically trigger photo verification if both photos exist
        photo_verification_triggered = False
        if rider.profile_photo and rider.national_id_photo:
            try:
                # Use system user for automatic verification
                system_user = User.objects.filter(is_staff=True).first()
                if system_user:
                    result = rider.verify_photos(verified_by=system_user)
                    photo_verification_triggered = result.get('success', False)
                    print(f"🔍 Auto photo verification triggered: {photo_verification_triggered}")
            except Exception as e:
                print(f"❌ Auto photo verification failed: {e}")
        
        return Response({
            'message': 'Onboarding submitted successfully!',
            'status': rider.status,
            'reference_number': application.reference_number,
            'referenceNumber': application.reference_number,  # Compatibility
            'applicationRef': application.reference_number,   # Legacy compatibility
            'nextStep': 'pending_approval',
            'photo_verification_triggered': photo_verification_triggered
        }, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response(
            {'error': 'Rider not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

def verify_admin_auth(request):
    """Helper function to verify admin authentication using token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Token '):
        return None
    
    try:
        token_key = auth_header.split(' ')[1]
        token = Token.objects.select_related('user').get(key=token_key)
        
        if token.user.is_staff:
            return token.user
    except (Token.DoesNotExist, ValueError, IndexError):
        pass
    
    return None

@api_view(['POST'])
def admin_login(request):
    """Admin login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    if user and user.is_staff:
        return Response({
            'success': True,
            'message': 'Login successful',
            'admin': {
                'id': user.id,
                'username': user.username,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Invalid credentials or insufficient privileges'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['GET'])
def admin_pending_riders(request):
    """Get list of riders pending approval"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get riders with PENDING_APPROVAL status
    pending_riders = Rider.objects.filter(status=Rider.PENDING_APPROVAL)
    
    riders_data = []
    for rider in pending_riders:
        # Get application info
        try:
            application = rider.application
            reference_number = application.reference_number
            submitted_at = application.submitted_at
        except RiderApplication.DoesNotExist:
            reference_number = None
            submitted_at = rider.updated_at
        
        riders_data.append({
            'id': rider.id,
            'firstName': rider.first_name,
            'lastName': rider.last_name,
            'fullName': rider.full_name,
            'phoneNumber': rider.phone_number,
            'experienceLevel': rider.get_experience_level_display(),
            'age': rider.age,
            'location': rider.location,
            'nationalIdNumber': rider.national_id_number,
            'status': rider.status,
            'referenceNumber': reference_number,
            'submittedAt': submitted_at,
            'createdAt': rider.created_at
        })
    
    return Response({
        'riders': riders_data,
        'count': len(riders_data)
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def admin_rider_details(request, rider_id):
    """Get detailed rider information for admin review"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        rider = Rider.objects.get(id=rider_id)
        
        # Get application info
        try:
            application = rider.application
            application_data = {
                'referenceNumber': application.reference_number,
                'submittedAt': application.submitted_at,
                'reviewedAt': application.reviewed_at,
                'reviewerNotes': application.reviewer_notes
            }
        except RiderApplication.DoesNotExist:
            application_data = None
        
        rider_data = {
            'id': rider.id,
            'firstName': rider.first_name,
            'lastName': rider.last_name,
            'fullName': rider.full_name,
            'phoneNumber': rider.phone_number,
            'experienceLevel': rider.get_experience_level_display(),
            'age': rider.age,
            'location': rider.location,
            'nationalIdNumber': rider.national_id_number,
            'status': rider.status,
            'points': rider.points,
            'uniqueId': rider.unique_id,
            'profilePhoto': rider.profile_photo.url if rider.profile_photo else None,
            'nationalIdPhoto': rider.national_id_photo.url if rider.national_id_photo else None,
            'approvedBy': rider.approved_by.username if rider.approved_by else None,
            'approvedAt': rider.approved_at,
            'rejectionReason': rider.rejection_reason,
            'createdAt': rider.created_at,
            'updatedAt': rider.updated_at,
            'application': application_data
        }
        
        return Response(rider_data, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response(
            {'error': 'Rider not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
def admin_approve_rider(request, rider_id):
    """Approve a pending rider application"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        rider = Rider.objects.get(id=rider_id)
        
        if rider.status != Rider.PENDING_APPROVAL:
            return Response(
                {'error': f'Rider is not pending approval (current status: {rider.status})'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique ID and approve rider
        rider.generate_unique_id()
        rider.status = Rider.APPROVED
        # Note: approved_by is for Enumerator, admin approval doesn't set this field
        rider.approved_at = timezone.now()
        rider.save()
        
        # Update application record
        try:
            application = rider.application
            application.reviewed_at = timezone.now()
            application.reviewer_notes = request.data.get('notes', '')
            application.save()
        except RiderApplication.DoesNotExist:
            pass
        
        return Response({
            'success': True,
            'message': f'Rider {rider.full_name} approved successfully',
            'rider': {
                'id': rider.id,
                'fullName': rider.full_name,
                'uniqueId': rider.unique_id,
                'status': rider.status,
                'approvedAt': rider.approved_at
            }
        }, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response(
            {'error': 'Rider not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
def admin_reject_rider(request, rider_id):
    """Reject a pending rider application"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    rejection_reason = request.data.get('reason', '')
    if not rejection_reason:
        return Response(
            {'error': 'Rejection reason is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rider = Rider.objects.get(id=rider_id)
        
        if rider.status != Rider.PENDING_APPROVAL:
            return Response(
                {'error': f'Rider is not pending approval (current status: {rider.status})'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reject rider
        rider.status = Rider.REJECTED
        rider.rejection_reason = rejection_reason
        rider.save()
        
        # Update application record
        try:
            application = rider.application
            application.reviewed_at = timezone.now()
            application.reviewer_notes = rejection_reason
            application.save()
        except RiderApplication.DoesNotExist:
            pass
        
        return Response({
            'success': True,
            'message': f'Rider {rider.full_name} rejected',
            'rider': {
                'id': rider.id,
                'fullName': rider.full_name,
                'status': rider.status,
                'rejectionReason': rider.rejection_reason
            }
        }, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response(
            {'error': 'Rider not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# =============================================================================
# ENUMERATOR ENDPOINTS
# =============================================================================

def verify_enumerator_auth(request):
    """Helper function to verify enumerator authentication"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return None
    
    try:
        import base64
        credentials = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
        identifier, password = credentials.split(':')
        
        # Check if identifier is an Enumerator ID (starts with EN-)
        user = None
        if identifier.startswith('EN-'):
            # Identifier is an Enumerator ID
            try:
                enumerator = Enumerator.objects.get(unique_id=identifier, status=Enumerator.ACTIVE)
                user = authenticate(username=enumerator.user.username, password=password)
            except Enumerator.DoesNotExist:
                return None
        else:
            # Identifier is a username
            user = authenticate(username=identifier, password=password)
        
        if user:
            try:
                enumerator = user.enumerator_profile
                if enumerator.status == Enumerator.ACTIVE:
                    return enumerator
            except Enumerator.DoesNotExist:
                pass
    except (ValueError, TypeError):
        pass
    
    return None

@api_view(['POST'])
@permission_classes([AllowAny])
def enumerator_login(request):
    """Enumerator login endpoint"""
    print(f"🚀 ENUMERATOR LOGIN ENDPOINT CALLED!")
    print(f"   Method: {request.method}")
    print(f"   Path: {request.get_full_path()}")
    print(f"   Headers: {dict(request.headers)}")
    print(f"   Raw data: {request.body}")
    
    # Accept either 'username' or 'enumeratorId' for backward compatibility
    username = request.data.get('username')
    enumerator_id = request.data.get('enumeratorId')
    password = request.data.get('password')
    
    # Determine login identifier
    login_identifier = enumerator_id if enumerator_id else username
    
    print(f"🔐 Enumerator login attempt:")
    print(f"   Enumerator ID: {enumerator_id}")
    print(f"   Username: {username}")
    print(f"   Login identifier: {login_identifier}")
    print(f"   Password length: {len(password) if password else 0}")
    
    if not login_identifier or not password:
        print(f"   ❌ Missing login identifier or password")
        return Response(
            {'error': 'Enumerator ID and password are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # If enumerator ID is provided, find the corresponding username
    user = None
    if enumerator_id:
        try:
            # Find enumerator by unique_id and get the username
            enumerator = Enumerator.objects.get(unique_id=enumerator_id, status=Enumerator.ACTIVE)
            user = authenticate(username=enumerator.user.username, password=password)
            print(f"   Found enumerator: {enumerator.full_name}, username: {enumerator.user.username}")
        except Enumerator.DoesNotExist:
            print(f"   ❌ Enumerator with ID {enumerator_id} not found or inactive")
            user = None
    else:
        # Fallback to username authentication
        user = authenticate(username=username, password=password)
    print(f"   Authentication result: {user is not None}")
    if user:
        print(f"   ✅ User found: {user.username}")
    else:
        print(f"   ❌ Authentication failed")
    if user:
        try:
            enumerator = user.enumerator_profile
            if enumerator.status == Enumerator.ACTIVE:
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
                print(f"   ✅ Login successful for: {enumerator.full_name}")
                print(f"   📊 Returning data: {response_data['data']}")
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Enumerator account is inactive'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except Enumerator.DoesNotExist:
            return Response(
                {'error': 'Not an enumerator account'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    else:
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['GET'])
def enumerator_assigned_riders(request):
    """Get riders assigned to the authenticated enumerator"""
    # Verify enumerator authentication
    enumerator = verify_enumerator_auth(request)
    if not enumerator:
        return Response(
            {'error': 'Enumerator authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get assigned riders
    assigned_riders = enumerator.assigned_riders.all()
    
    riders_data = []
    for rider in assigned_riders:
        # Get application info if exists
        try:
            application = rider.application
            reference_number = application.reference_number
            submitted_at = application.submitted_at
        except RiderApplication.DoesNotExist:
            reference_number = None
            submitted_at = rider.updated_at
        
        riders_data.append({
            'id': rider.id,
            'firstName': rider.first_name,
            'lastName': rider.last_name,
            'fullName': rider.full_name,
            'phoneNumber': rider.phone_number,
            'experienceLevel': rider.get_experience_level_display(),
            'age': rider.age,
            'location': rider.location,
            'nationalIdNumber': rider.national_id_number,
            'status': rider.status,
            'referenceNumber': reference_number,
            'submittedAt': submitted_at,
            'createdAt': rider.created_at,
            'uniqueId': rider.unique_id
        })
    
    return Response({
        'riders': riders_data,
        'count': len(riders_data)
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def enumerator_pending_riders(request):
    """Get riders pending approval by the authenticated enumerator"""
    # Verify enumerator authentication
    enumerator = verify_enumerator_auth(request)
    if not enumerator:
        return Response(
            {'error': 'Enumerator authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get pending riders assigned to this enumerator
    pending_riders = enumerator.assigned_riders.filter(status=Rider.PENDING_APPROVAL)
    
    riders_data = []
    for rider in pending_riders:
        # Get application info
        try:
            application = rider.application
            reference_number = application.reference_number
            submitted_at = application.submitted_at
        except RiderApplication.DoesNotExist:
            reference_number = None
            submitted_at = rider.updated_at
        
        riders_data.append({
            'id': rider.id,
            'firstName': rider.first_name,
            'lastName': rider.last_name,
            'fullName': rider.full_name,
            'phoneNumber': rider.phone_number,
            'experienceLevel': rider.get_experience_level_display(),
            'age': rider.age,
            'location': rider.location,
            'nationalIdNumber': rider.national_id_number,
            'status': rider.status,
            'referenceNumber': reference_number,
            'submittedAt': submitted_at,
            'createdAt': rider.created_at,
            'profilePhoto': request.build_absolute_uri(rider.profile_photo.url) if rider.profile_photo else None,
            'nationalIdPhoto': request.build_absolute_uri(rider.national_id_photo.url) if rider.national_id_photo else None,
        })
    
    return Response({
        'riders': riders_data,
        'count': len(riders_data)
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def enumerator_approve_rider(request, rider_id):
    """Approve a rider by the assigned enumerator"""
    # Verify enumerator authentication
    enumerator = verify_enumerator_auth(request)
    if not enumerator:
        return Response(
            {'error': 'Enumerator authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        rider = Rider.objects.get(id=rider_id, assigned_enumerator=enumerator)
        
        if rider.status != Rider.PENDING_APPROVAL:
            return Response(
                {'error': f'Rider is not pending approval (current status: {rider.status})'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique ID and approve rider
        rider.generate_unique_id()
        rider.status = Rider.APPROVED
        rider.approved_by = enumerator
        rider.approved_at = timezone.now()
        rider.save()
        
        # Update application record
        try:
            application = rider.application
            application.reviewed_at = timezone.now()
            application.reviewer_notes = request.data.get('notes', '')
            application.save()
        except RiderApplication.DoesNotExist:
            pass
        
        return Response({
            'success': True,
            'message': f'Rider {rider.full_name} approved successfully',
            'rider': {
                'id': rider.id,
                'fullName': rider.full_name,
                'uniqueId': rider.unique_id,
                'status': rider.status,
                'approvedAt': rider.approved_at
            }
        }, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response(
            {'error': 'Rider not found or not assigned to you'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def enumerator_reject_rider(request, rider_id):
    """Reject a rider by the assigned enumerator"""
    # Verify enumerator authentication
    enumerator = verify_enumerator_auth(request)
    if not enumerator:
        return Response(
            {'error': 'Enumerator authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    rejection_reason = request.data.get('reason', '')
    if not rejection_reason:
        return Response(
            {'error': 'Rejection reason is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rider = Rider.objects.get(id=rider_id, assigned_enumerator=enumerator)
        
        if rider.status != Rider.PENDING_APPROVAL:
            return Response(
                {'error': f'Rider is not pending approval (current status: {rider.status})'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reject rider
        rider.status = Rider.REJECTED
        rider.rejection_reason = rejection_reason
        rider.save()
        
        # Update application record
        try:
            application = rider.application
            application.reviewed_at = timezone.now()
            application.reviewer_notes = rejection_reason
            application.save()
        except RiderApplication.DoesNotExist:
            pass
        
        return Response({
            'success': True,
            'message': f'Rider {rider.full_name} rejected',
            'rider': {
                'id': rider.id,
                'fullName': rider.full_name,
                'status': rider.status,
                'rejectionReason': rider.rejection_reason
            }
        }, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response(
            {'error': 'Rider not found or not assigned to you'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def enumerator_dashboard_stats(request):
    """Get enumerator dashboard statistics"""
    # Verify enumerator authentication
    enumerator = verify_enumerator_auth(request)
    if not enumerator:
        return Response(
            {'error': 'Enumerator authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Calculate statistics for this enumerator's assigned riders
    assigned_riders = enumerator.assigned_riders.all()
    total_assigned = assigned_riders.count()
    pending_approval = assigned_riders.filter(status=Rider.PENDING_APPROVAL).count()
    approved_riders = assigned_riders.filter(status=Rider.APPROVED).count()
    rejected_riders = assigned_riders.filter(status=Rider.REJECTED).count()
    
    # Recent assignments (last 7 days)
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    recent_assignments = assigned_riders.filter(created_at__gte=week_ago).count()
    
    return Response({
        'totalAssigned': total_assigned,
        'pendingApproval': pending_approval,
        'approvedRiders': approved_riders,
        'rejectedRiders': rejected_riders,
        'recentAssignments': recent_assignments,
        'approvalRate': round((approved_riders / total_assigned * 100), 2) if total_assigned > 0 else 0,
        'enumeratorInfo': {
            'uniqueId': enumerator.unique_id,
            'fullName': enumerator.full_name,
            'location': enumerator.location,
            'assignedRegion': enumerator.assigned_region
        }
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
def update_fcm_token(request):
    """Update rider's FCM token for push notifications."""
    print("🔔 FCM Token update request received")
    
    # Verify Firebase token
    decoded_token = verify_firebase_token(request)
    if not decoded_token:
        print("❌ Invalid Firebase token")
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        data = request.data
        fcm_token = data.get('fcm_token')
        phone_number = data.get('phone_number')  # May be provided explicitly
        
        if not fcm_token:
            return Response({'error': 'FCM token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # For now, since our Firebase verification is basic, we'll require phone_number
        if not phone_number:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Find the rider
        try:
            rider = Rider.objects.get(phone_number=phone_number)
        except Rider.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update FCM token
        if FCMService.update_rider_fcm_token(rider, fcm_token):
            print(f"✅ FCM token updated for rider {rider.phone_number}")
            return Response({'message': 'FCM token updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to update FCM token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        print(f"❌ Error updating FCM token: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def approve_rider(request, rider_id):
    """Approve a rider and send push notification."""
    print(f"🔔 Rider approval request for rider {rider_id}")
    
    # Verify Firebase token
    decoded_token = verify_firebase_token(request)
    if not decoded_token:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        rider = Rider.objects.get(id=rider_id)
        
        # Update rider status
        rider.status = Rider.APPROVED
        rider.approved_at = timezone.now()
        rider.save()
        
        print(f"✅ Rider {rider.phone_number} approved")
        
        # Send push notification if FCM token exists
        if rider.fcm_token:
            success = FCMService.send_status_change_notification(
                fcm_token=rider.fcm_token,
                rider_name=rider.full_name,
                new_status='APPROVED'
            )
            
            if success:
                print(f"🔔 Approval notification sent to {rider.full_name}")
            else:
                print(f"❌ Failed to send notification to {rider.full_name}")
        else:
            print(f"⚠️ No FCM token for rider {rider.full_name}")
        
        return Response({
            'message': 'Rider approved successfully',
            'notification_sent': bool(rider.fcm_token)
        }, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"❌ Error approving rider: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def reject_rider(request, rider_id):
    """Reject a rider and send push notification."""
    print(f"🔔 Rider rejection request for rider {rider_id}")
    
    # Verify Firebase token
    decoded_token = verify_firebase_token(request)
    if not decoded_token:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        rider = Rider.objects.get(id=rider_id)
        data = request.data
        
        rejection_reason = data.get('rejection_reason', 'No reason provided')
        
        # Update rider status
        rider.status = Rider.REJECTED
        rider.rejection_reason = rejection_reason
        rider.save()
        
        print(f"✅ Rider {rider.phone_number} rejected: {rejection_reason}")
        
        # Send push notification if FCM token exists
        if rider.fcm_token:
            success = FCMService.send_status_change_notification(
                fcm_token=rider.fcm_token,
                rider_name=rider.full_name,
                new_status='REJECTED',
                rejection_reason=rejection_reason
            )
            
            if success:
                print(f"🔔 Rejection notification sent to {rider.full_name}")
            else:
                print(f"❌ Failed to send notification to {rider.full_name}")
        else:
            print(f"⚠️ No FCM token for rider {rider.full_name}")
        
        return Response({
            'message': 'Rider rejected successfully',
            'notification_sent': bool(rider.fcm_token)
        }, status=status.HTTP_200_OK)
        
    except Rider.DoesNotExist:
        return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"❌ Error rejecting rider: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def enumerator_change_password(request):
    """Allow enumerators to change their password"""
    # Verify enumerator authentication
    enumerator = verify_enumerator_auth(request)
    if not enumerator:
        return Response(
            {'error': 'Enumerator authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    current_password = request.data.get('currentPassword')
    new_password = request.data.get('newPassword')
    confirm_password = request.data.get('confirmPassword')
    
    # Validate required fields
    if not current_password or not new_password or not confirm_password:
        return Response(
            {'error': 'All password fields are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new passwords match
    if new_password != confirm_password:
        return Response(
            {'error': 'New passwords do not match'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password length
    if len(new_password) < 6:
        return Response(
            {'error': 'New password must be at least 6 characters long'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify current password
    user = enumerator.user
    if not user.check_password(current_password):
        return Response(
            {'error': 'Current password is incorrect'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Change password
    try:
        user.set_password(new_password)
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to change password'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def admin_dashboard_stats(request):
    """Get dashboard statistics for admin"""
    try:
        print("🔍 Admin dashboard stats requested")
        
        # Verify admin authentication (using token)
        auth_header = request.headers.get('Authorization')
        print(f"📡 Auth header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Token '):
            return Response(
                {'error': 'Admin authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token_key = auth_header.split(' ')[1]
        print(f"🔑 Token key: {token_key[:10]}...")
        
        try:
            token = Token.objects.select_related('user').get(key=token_key)
            print(f"👤 Token user: {token.user.username}, is_staff: {token.user.is_staff}")
            
            if not token.user.is_staff:
                return Response(
                    {'error': 'Admin authentication required'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except Token.DoesNotExist:
            print("❌ Token does not exist")
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Calculate statistics
        print("📊 Calculating stats...")
        total_riders = Rider.objects.count()
        pending_riders = Rider.objects.filter(status='PENDING_APPROVAL').count()
        approved_riders = Rider.objects.filter(status='APPROVED').count()
        rejected_riders = Rider.objects.filter(status='REJECTED').count()
        
        # Recent applications (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_applications = Rider.objects.filter(
            status='PENDING_APPROVAL',
            created_at__gte=week_ago
        ).count()
        
        stats = {
            'totalRiders': total_riders,
            'pendingApproval': pending_riders,
            'approvedRiders': approved_riders,
            'rejectedRiders': rejected_riders,
            'recentApplications': recent_applications,
            'approvalRate': round((approved_riders / total_riders * 100), 2) if total_riders > 0 else 0
        }
        
        # Add enumerator stats
        total_enumerators = Enumerator.objects.count()
        active_enumerators = Enumerator.objects.filter(status=Enumerator.ACTIVE).count()
        inactive_enumerators = Enumerator.objects.filter(status=Enumerator.INACTIVE).count()
        
        stats.update({
            'totalEnumerators': total_enumerators,
            'activeEnumerators': active_enumerators,
            'inactiveEnumerators': inactive_enumerators,
        })
        
        print(f"✅ Stats calculated: {stats}")
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting admin dashboard stats: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': 'Failed to get dashboard statistics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# =============================================================================
# ADMIN ENUMERATOR MANAGEMENT ENDPOINTS
# =============================================================================

@api_view(['GET'])
def admin_enumerators_list(request):
    """Get list of all enumerators for admin"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Get all enumerators
        enumerators = Enumerator.objects.all().select_related('user')
        
        enumerators_data = []
        for enumerator in enumerators:
            enumerators_data.append({
                'id': enumerator.id,
                'unique_id': enumerator.unique_id,
                'first_name': enumerator.first_name,
                'last_name': enumerator.last_name,
                'phone': enumerator.phone_number,
                'gender': enumerator.gender,
                'location': enumerator.location,
                'assigned_region': enumerator.assigned_region,
                'is_active': enumerator.status == Enumerator.ACTIVE,
                'status': enumerator.status,
                'created_at': enumerator.created_at,
                'updated_at': enumerator.updated_at,
                'date_joined': enumerator.created_at,  # For compatibility
                # Statistics
                'total_assigned_riders': enumerator.assigned_riders.count(),
                'pending_riders': enumerator.assigned_riders.filter(status=Rider.PENDING_APPROVAL).count(),
                'approved_riders': enumerator.assigned_riders.filter(status=Rider.APPROVED).count(),
            })
        
        return Response(enumerators_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting enumerators list: {e}")
        return Response(
            {'error': 'Failed to get enumerators list'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def admin_enumerator_details(request, enumerator_id):
    """Get detailed enumerator information for admin"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Try to get by unique_id first, then by primary key
        if enumerator_id.startswith('EN-'):
            enumerator = Enumerator.objects.select_related('user').get(unique_id=enumerator_id)
        else:
            enumerator = Enumerator.objects.select_related('user').get(id=enumerator_id)
        
        # Get assigned riders statistics
        assigned_riders = enumerator.assigned_riders.all()
        
        enumerator_data = {
            'id': enumerator.id,
            'unique_id': enumerator.unique_id,
            'first_name': enumerator.first_name,
            'last_name': enumerator.last_name,
            'phone': enumerator.phone_number,
            'location': enumerator.location,
            'assigned_region': enumerator.assigned_region,
            'is_active': enumerator.status == Enumerator.ACTIVE,
            'status': enumerator.status,
            'created_at': enumerator.created_at,
            'updated_at': enumerator.updated_at,
            'date_joined': enumerator.created_at,
            'username': enumerator.user.username,
            'email': enumerator.user.email,
            'last_login': enumerator.user.last_login,
            # Statistics
            'stats': {
                'total_reviewed': assigned_riders.count(),
                'approved': assigned_riders.filter(status=Rider.APPROVED).count(),
                'rejected': assigned_riders.filter(status=Rider.REJECTED).count(),
                'pending': assigned_riders.filter(status=Rider.PENDING_APPROVAL).count(),
                'approval_rate': 0
            }
        }
        
        # Calculate approval rate
        total_reviewed = enumerator_data['stats']['approved'] + enumerator_data['stats']['rejected']
        if total_reviewed > 0:
            enumerator_data['stats']['approval_rate'] = round(
                (enumerator_data['stats']['approved'] / total_reviewed) * 100, 1
            )
        
        return Response(enumerator_data, status=status.HTTP_200_OK)
        
    except Enumerator.DoesNotExist:
        return Response(
            {'error': 'Enumerator not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"💥 Error getting enumerator details: {e}")
        return Response(
            {'error': 'Failed to get enumerator details'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_create_enumerator(request):
    """Create a new enumerator"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        data = request.data
        
        # Required fields
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        location = data.get('location')
        assigned_region = data.get('assigned_region')
        
        # Optional fields
        gender = data.get('gender')
        
        if not all([first_name, last_name, phone, location, assigned_region]):
            return Response(
                {'error': 'All fields are required: first_name, last_name, phone, location, assigned_region'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate gender if provided
        if gender and gender not in ['M', 'F', 'O']:
            return Response(
                {'error': 'Invalid gender. Must be M (Male), F (Female), or O (Other)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if phone number already exists
        if Enumerator.objects.filter(phone_number=phone).exists():
            return Response(
                {'error': 'Phone number already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create User account
        username = f"enum_{phone}"  # Simple username generation
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password='changeme123'  # Default password
        )
        
        # Create Enumerator
        enumerator = Enumerator.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            location=location,
            assigned_region=assigned_region,
            gender=gender,
            status=Enumerator.ACTIVE if data.get('is_active', True) else Enumerator.INACTIVE,
            approved_by=admin_user,
            approved_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'Enumerator {enumerator.full_name} created successfully',
            'data': {
                'id': enumerator.id,
                'unique_id': enumerator.unique_id,
                'first_name': enumerator.first_name,
                'last_name': enumerator.last_name,
                'phone': enumerator.phone_number,
                'gender': enumerator.gender,
                'location': enumerator.location,
                'assigned_region': enumerator.assigned_region,
                'is_active': enumerator.status == Enumerator.ACTIVE,
                'username': user.username,
                'default_password': 'changeme123'
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"💥 Error creating enumerator: {e}")
        return Response(
            {'error': 'Failed to create enumerator'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
@permission_classes([AllowAny])
def admin_update_enumerator(request, enumerator_id):
    """Update an existing enumerator"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Try to get by unique_id first, then by primary key
        if enumerator_id.startswith('EN-'):
            enumerator = Enumerator.objects.get(unique_id=enumerator_id)
        else:
            enumerator = Enumerator.objects.get(id=enumerator_id)
        
        data = request.data
        
        # Update fields if provided
        if 'first_name' in data:
            enumerator.first_name = data['first_name']
            enumerator.user.first_name = data['first_name']
        
        if 'last_name' in data:
            enumerator.last_name = data['last_name']
            enumerator.user.last_name = data['last_name']
        
        if 'phone' in data:
            # Check if new phone number already exists for another enumerator
            if Enumerator.objects.filter(phone_number=data['phone']).exclude(id=enumerator.id).exists():
                return Response(
                    {'error': 'Phone number already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            enumerator.phone_number = data['phone']
        
        if 'gender' in data:
            # Validate gender
            if data['gender'] and data['gender'] not in ['M', 'F', 'O']:
                return Response(
                    {'error': 'Invalid gender. Must be M (Male), F (Female), or O (Other)'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            enumerator.gender = data['gender']
        
        if 'location' in data:
            enumerator.location = data['location']
        
        if 'assigned_region' in data:
            enumerator.assigned_region = data['assigned_region']
        
        if 'is_active' in data:
            enumerator.status = Enumerator.ACTIVE if data['is_active'] else Enumerator.INACTIVE
        
        enumerator.save()
        enumerator.user.save()
        
        return Response({
            'success': True,
            'message': f'Enumerator {enumerator.full_name} updated successfully',
            'data': {
                'id': enumerator.id,
                'unique_id': enumerator.unique_id,
                'first_name': enumerator.first_name,
                'last_name': enumerator.last_name,
                'phone': enumerator.phone_number,
                'gender': enumerator.gender,
                'location': enumerator.location,
                'assigned_region': enumerator.assigned_region,
                'is_active': enumerator.status == Enumerator.ACTIVE,
            }
        }, status=status.HTTP_200_OK)
        
    except Enumerator.DoesNotExist:
        return Response(
            {'error': 'Enumerator not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"💥 Error updating enumerator: {e}")
        return Response(
            {'error': 'Failed to update enumerator'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([AllowAny])
def admin_delete_enumerator(request, enumerator_id):
    """Delete an enumerator (soft delete by setting status to inactive)"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Try to get by unique_id first, then by primary key
        if enumerator_id.startswith('EN-'):
            enumerator = Enumerator.objects.get(unique_id=enumerator_id)
        else:
            enumerator = Enumerator.objects.get(id=enumerator_id)
        
        # Check if enumerator has assigned riders
        if enumerator.assigned_riders.exists():
            return Response(
                {'error': 'Cannot delete enumerator with assigned riders. Please reassign riders first.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete by setting status to inactive
        enumerator.status = Enumerator.INACTIVE
        enumerator.save()
        
        # Also deactivate the user account
        enumerator.user.is_active = False
        enumerator.user.save()
        
        return Response({
            'success': True,
            'message': f'Enumerator {enumerator.full_name} deactivated successfully'
        }, status=status.HTTP_200_OK)
        
    except Enumerator.DoesNotExist:
        return Response(
            {'error': 'Enumerator not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"💥 Error deleting enumerator: {e}")
        return Response(
            {'error': 'Failed to delete enumerator'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def admin_search_enumerators(request):
    """Search enumerators by query string"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        query = request.GET.get('q', '').strip()
        
        if not query:
            return Response([], status=status.HTTP_200_OK)
        
        # Search in multiple fields
        from django.db.models import Q
        enumerators = Enumerator.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(unique_id__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(location__icontains=query) |
            Q(assigned_region__icontains=query)
        ).select_related('user')
        
        enumerators_data = []
        for enumerator in enumerators:
            enumerators_data.append({
                'id': enumerator.id,
                'unique_id': enumerator.unique_id,
                'first_name': enumerator.first_name,
                'last_name': enumerator.last_name,
                'phone': enumerator.phone_number,
                'gender': enumerator.gender,
                'location': enumerator.location,
                'assigned_region': enumerator.assigned_region,
                'is_active': enumerator.status == Enumerator.ACTIVE,
                'status': enumerator.status,
                'created_at': enumerator.created_at,
                'updated_at': enumerator.updated_at,
            })
        
        return Response(enumerators_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error searching enumerators: {e}")
        return Response(
            {'error': 'Failed to search enumerators'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def admin_pending_riders_by_enumerator(request):
    """Get pending riders grouped by enumerator for admin"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Get all enumerators with their pending riders
        enumerators = Enumerator.objects.prefetch_related(
            'assigned_riders__application'
        ).filter(status=Enumerator.ACTIVE)
        
        enumerator_groups = []
        total_pending = 0
        
        for enumerator in enumerators:
            # Get pending riders for this enumerator
            pending_riders = enumerator.assigned_riders.filter(
                status=Rider.PENDING_APPROVAL
            ).select_related('assigned_enumerator').prefetch_related('application')
            
            if pending_riders.exists():
                riders_data = []
                for rider in pending_riders:
                    # Get application info
                    application_data = {}
                    try:
                        application = rider.application
                        application_data = {
                            'referenceNumber': application.reference_number,
                            'submittedAt': application.submitted_at.isoformat(),
                        }
                    except RiderApplication.DoesNotExist:
                        application_data = {
                            'referenceNumber': 'N/A',
                            'submittedAt': rider.created_at.isoformat(),
                        }
                    
                    rider_data = {
                        'id': rider.id,
                        'fullName': rider.full_name,
                        'phoneNumber': rider.phone_number,
                        'experienceLevel': rider.get_experience_level_display(),
                        'age': rider.age,
                        'location': rider.location,
                        'status': rider.status,
                        **application_data
                    }
                    riders_data.append(rider_data)
                
                enumerator_data = {
                    'enumerator': {
                        'id': enumerator.id,
                        'unique_id': enumerator.unique_id,
                        'first_name': enumerator.first_name,
                        'last_name': enumerator.last_name,
                        'full_name': enumerator.full_name,
                        'phone': enumerator.phone_number,
                        'location': enumerator.location,
                        'assigned_region': enumerator.assigned_region,
                    },
                    'pending_riders': riders_data,
                    'count': len(riders_data)
                }
                
                enumerator_groups.append(enumerator_data)
                total_pending += len(riders_data)
        
        # Add enumerators with no pending riders for completeness
        unassigned_pending = Rider.objects.filter(
            status=Rider.PENDING_APPROVAL,
            assigned_enumerator__isnull=True
        ).select_related('assigned_enumerator').prefetch_related('application')
        
        if unassigned_pending.exists():
            riders_data = []
            for rider in unassigned_pending:
                # Get application info
                application_data = {}
                try:
                    application = rider.application
                    application_data = {
                        'referenceNumber': application.reference_number,
                        'submittedAt': application.submitted_at.isoformat(),
                    }
                except RiderApplication.DoesNotExist:
                    application_data = {
                        'referenceNumber': 'N/A',
                        'submittedAt': rider.created_at.isoformat(),
                    }
                
                rider_data = {
                    'id': rider.id,
                    'fullName': rider.full_name,
                    'phoneNumber': rider.phone_number,
                    'experienceLevel': rider.get_experience_level_display(),
                    'age': rider.age,
                    'location': rider.location,
                    'status': rider.status,
                    **application_data
                }
                riders_data.append(rider_data)
            
            unassigned_data = {
                'enumerator': {
                    'id': 'unassigned',
                    'unique_id': 'UNASSIGNED',
                    'first_name': 'Unassigned',
                    'last_name': 'Riders',
                    'full_name': 'Unassigned Riders',
                    'phone': 'N/A',
                    'location': 'Various',
                    'assigned_region': 'Various',
                },
                'pending_riders': riders_data,
                'count': len(riders_data)
            }
            
            enumerator_groups.append(unassigned_data)
            total_pending += len(riders_data)
        
        # Sort by enumerator name
        enumerator_groups.sort(key=lambda x: x['enumerator']['full_name'])
        
        return Response({
            'success': True,
            'data': {
                'enumerator_groups': enumerator_groups,
                'total_pending': total_pending,
                'total_enumerators_with_pending': len([g for g in enumerator_groups if g['enumerator']['id'] != 'unassigned'])
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting pending riders by enumerator: {e}")
        return Response(
            {'error': 'Failed to get pending riders by enumerator'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# =============================================================================
# DIGITAL LITERACY TRAINING API ENDPOINTS
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def digital_literacy_modules(request):
    """Get all digital literacy training modules"""
    try:
        from .models import DigitalLiteracyModule
        
        modules = DigitalLiteracyModule.objects.filter(is_active=True).prefetch_related('sessions')
        
        modules_data = []
        for module in modules:
            modules_data.append({
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'session_count': module.session_count,
                'total_duration_hours': float(module.total_duration_hours),
                'points_value': module.points_value,
                'icon': module.icon,
                'order': module.order,
                'sessions': [
                    {
                        'id': session.id,
                        'session_number': session.session_number,
                        'title': session.title,
                        'description': session.description,
                        'duration_hours': float(session.duration_hours),
                        'learning_objectives': session.learning_objectives,
                        'required_materials': session.required_materials,
                        'points_value': session.points_value,
                    } for session in module.sessions.all()
                ]
            })
        
        return Response({
            'success': True,
            'data': modules_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting digital literacy modules: {e}")
        return Response(
            {'error': 'Failed to get digital literacy modules'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def upcoming_training_sessions(request):
    """Get upcoming training sessions for riders"""
    try:
        from .models import SessionSchedule, DigitalLiteracyProgress
        from django.utils import timezone
        
        # Get rider from phone number (assuming rider authentication)
        phone_number = request.GET.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rider = Rider.objects.get(phone_number=phone_number)
        except Rider.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get upcoming sessions (next 30 days)
        upcoming_schedules = SessionSchedule.objects.filter(
            scheduled_date__gte=timezone.now(),
            scheduled_date__lte=timezone.now() + timedelta(days=30),
            status='SCHEDULED'
        ).select_related('session__module', 'trainer').order_by('scheduled_date')
        
        sessions_data = []
        for schedule in upcoming_schedules:
            # Check if rider is already registered
            is_registered = schedule.attendance_records.filter(
                rider=rider,
                status__in=['REGISTERED', 'ATTENDED']
            ).exists()
            
            # Check rider's progress in this module
            progress = DigitalLiteracyProgress.objects.filter(
                rider=rider,
                module=schedule.session.module
            ).first()
            
            sessions_data.append({
                'schedule_id': schedule.id,
                'session': {
                    'id': schedule.session.id,
                    'title': schedule.session.title,
                    'description': schedule.session.description,
                    'session_number': schedule.session.session_number,
                    'duration_hours': float(schedule.session.duration_hours),
                    'points_value': schedule.session.points_value,
                },
                'module': {
                    'id': schedule.session.module.id,
                    'title': schedule.session.module.title,
                    'icon': schedule.session.module.icon,
                },
                'trainer': {
                    'id': schedule.trainer.id,
                    'name': schedule.trainer.full_name,
                    'unique_id': schedule.trainer.unique_id,
                },
                'scheduled_date': schedule.scheduled_date.isoformat(),
                'location_name': schedule.location_name,
                'location_address': schedule.location_address,
                'gps_coordinates': {
                    'latitude': float(schedule.gps_latitude) if schedule.gps_latitude else None,
                    'longitude': float(schedule.gps_longitude) if schedule.gps_longitude else None,
                },
                'capacity': schedule.capacity,
                'registered_count': schedule.registered_count,
                'spots_remaining': schedule.spots_remaining,
                'is_registered': is_registered,
                'rider_progress': {
                    'completion_percentage': float(progress.completion_percentage) if progress else 0,
                    'sessions_attended': progress.sessions_attended if progress else 0,
                    'skill_level': progress.skill_level if progress else 'BEGINNER',
                } if progress else None,
            })
        
        return Response({
            'success': True,
            'data': {
                'upcoming_sessions': sessions_data,
                'total_count': len(sessions_data)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting upcoming training sessions: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': 'Failed to get upcoming training sessions'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def register_attendance(request):
    """Register attendance for a training session with GPS verification"""
    try:
        from .models import SessionSchedule, SessionAttendance, AttendanceVerification
        from django.utils import timezone
        
        data = request.data
        phone_number = data.get('phone_number')
        schedule_id = data.get('schedule_id')
        trainer_id_entered = data.get('trainer_id')
        gps_latitude = data.get('gps_latitude')
        gps_longitude = data.get('gps_longitude')
        
        # Validate required fields
        if not all([phone_number, schedule_id, trainer_id_entered, gps_latitude, gps_longitude]):
            return Response({
                'error': 'Missing required fields: phone_number, schedule_id, trainer_id, gps_latitude, gps_longitude'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rider
        try:
            rider = Rider.objects.get(phone_number=phone_number)
        except Rider.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get session schedule
        try:
            schedule = SessionSchedule.objects.select_related('trainer', 'session__module').get(id=schedule_id)
        except SessionSchedule.DoesNotExist:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if session is still open for registration
        if schedule.status != 'SCHEDULED':
            return Response({'error': 'This session is no longer available for registration'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if there's capacity
        if schedule.spots_remaining <= 0:
            return Response({'error': 'This session is full'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if rider is already registered
        existing_attendance = SessionAttendance.objects.filter(
            schedule=schedule,
            rider=rider,
            status__in=['REGISTERED', 'ATTENDED']
        ).first()
        
        if existing_attendance:
            return Response({
                'error': 'You are already registered for this session',
                'attendance_id': existing_attendance.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify trainer ID matches
        if trainer_id_entered.strip().upper() != schedule.trainer.unique_id.upper():
            return Response({'error': 'Invalid trainer ID. Please check and try again.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate distance from venue
        def calculate_distance(lat1, lon1, lat2, lon2):
            if not all([lat1, lon1, lat2, lon2]):
                return None
            
            from math import radians, cos, sin, asin, sqrt
            
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of earth in kilometers
            
            return c * r * 1000  # Return distance in meters
        
        distance_from_venue = calculate_distance(
            float(gps_latitude),
            float(gps_longitude),
            float(schedule.gps_latitude) if schedule.gps_latitude else 0,
            float(schedule.gps_longitude) if schedule.gps_longitude else 0
        )
        
        # Check if rider is within reasonable distance (500 meters)
        max_distance = 500  # meters
        if distance_from_venue and distance_from_venue > max_distance:
            return Response({
                'error': f'You must be within {max_distance}m of the training venue to register. Current distance: {int(distance_from_venue)}m'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create attendance record
        attendance = SessionAttendance.objects.create(
            schedule=schedule,
            rider=rider,
            check_in_time=timezone.now(),
            check_in_gps_latitude=gps_latitude,
            check_in_gps_longitude=gps_longitude,
            status='REGISTERED'
        )
        
        # Create verification record
        verification = AttendanceVerification.objects.create(
            attendance=attendance,
            rider_verified=True,
            rider_verification_time=timezone.now(),
            trainer_id_entered=trainer_id_entered,
            distance_from_venue_meters=distance_from_venue
        )
        
        # Check if early registration bonus applies (within first 15 minutes)
        session_start = schedule.scheduled_date
        early_registration_cutoff = session_start + timedelta(minutes=15)
        is_early_registration = timezone.now() <= early_registration_cutoff
        
        # Award points for attendance
        base_points = schedule.session.points_value
        bonus_points = 50 if is_early_registration else 0
        total_points = base_points + bonus_points
        
        from .models import DigitalSkillsPoints
        points_record = DigitalSkillsPoints.objects.create(
            rider=rider,
            attendance=attendance,
            points=total_points,
            source='EARLY_REGISTRATION' if is_early_registration else 'ATTENDANCE',
            description=f"Registered for {schedule.session.title}" + (" (Early Registration Bonus)" if is_early_registration else "")
        )
        
        # Update or create progress record
        from .models import DigitalLiteracyProgress
        progress, created = DigitalLiteracyProgress.objects.get_or_create(
            rider=rider,
            module=schedule.session.module,
            defaults={'sessions_attended': 1, 'last_session_attended': timezone.now()}
        )
        
        if not created:
            progress.sessions_attended += 1
            progress.last_session_attended = timezone.now()
            progress.update_progress()
        else:
            progress.update_progress()
        
        return Response({
            'success': True,
            'message': 'Successfully registered for training session!',
            'data': {
                'attendance_id': attendance.id,
                'session_title': schedule.session.title,
                'scheduled_date': schedule.scheduled_date.isoformat(),
                'location': schedule.location_name,
                'points_earned': total_points,
                'early_registration_bonus': bonus_points > 0,
                'distance_from_venue_meters': int(distance_from_venue) if distance_from_venue else None,
                'verification_pending': not verification.trainer_verified,
                'progress': {
                    'sessions_attended': progress.sessions_attended,
                    'completion_percentage': float(progress.completion_percentage)
                }
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"💥 Error registering attendance: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': 'Failed to register attendance'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def rider_digital_literacy_progress(request):
    """Get rider's digital literacy progress across all modules"""
    try:
        phone_number = request.GET.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rider = Rider.objects.get(phone_number=phone_number)
        except Rider.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        from .models import DigitalLiteracyModule, DigitalLiteracyProgress, DigitalSkillsPoints
        
        # Get all modules
        modules = DigitalLiteracyModule.objects.filter(is_active=True).order_by('order')
        
        # Get rider's progress
        progress_records = DigitalLiteracyProgress.objects.filter(rider=rider)
        progress_dict = {p.module_id: p for p in progress_records}
        
        # Get total points earned
        total_points = DigitalSkillsPoints.objects.filter(rider=rider).aggregate(
            total=models.Sum('points')
        )['total'] or 0
        
        modules_data = []
        overall_completion = 0
        total_sessions_attended = 0
        total_sessions_available = 0
        
        for module in modules:
            progress = progress_dict.get(module.id)
            
            module_data = {
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'icon': module.icon,
                'session_count': module.session_count,
                'total_duration_hours': float(module.total_duration_hours),
                'points_value': module.points_value,
                'progress': {
                    'sessions_attended': progress.sessions_attended if progress else 0,
                    'completion_percentage': float(progress.completion_percentage) if progress else 0,
                    'skill_level': progress.skill_level if progress else 'BEGINNER',
                    'started_at': progress.started_at.isoformat() if progress else None,
                    'completed_at': progress.completed_at.isoformat() if progress and progress.completed_at else None,
                    'last_session_attended': progress.last_session_attended.isoformat() if progress and progress.last_session_attended else None,
                }
            }
            
            modules_data.append(module_data)
            
            # Calculate overall progress
            if progress:
                overall_completion += progress.completion_percentage
                total_sessions_attended += progress.sessions_attended
            total_sessions_available += module.session_count
        
        overall_completion_percentage = overall_completion / len(modules) if modules else 0
        
        return Response({
            'success': True,
            'data': {
                'rider': {
                    'id': rider.id,
                    'full_name': rider.full_name,
                    'phone_number': rider.phone_number,
                    'unique_id': rider.unique_id,
                },
                'overall_progress': {
                    'completion_percentage': round(overall_completion_percentage, 2),
                    'total_sessions_attended': total_sessions_attended,
                    'total_sessions_available': total_sessions_available,
                    'total_points_earned': total_points,
                    'modules_started': len([p for p in progress_records if p.sessions_attended > 0]),
                    'modules_completed': len([p for p in progress_records if p.completed_at]),
                },
                'modules': modules_data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting rider digital literacy progress: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': 'Failed to get digital literacy progress'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def digital_literacy_leaderboard(request):
    """Get digital literacy leaderboard"""
    try:
        print('🏆 Fetching digital literacy leaderboard...')
        
        period = request.GET.get('period', 'all_time')
        limit = int(request.GET.get('limit', 50))
        
        # Get riders with digital literacy progress, ordered by points
        from django.db.models import Sum, Count, Q
        
        # Calculate total points for each rider
        leaderboard_data = []
        riders_with_progress = Rider.objects.filter(
            digitalliteracyprogress__isnull=False,
            approval_status='approved'
        ).distinct()
        
        for rider in riders_with_progress:
            progress_records = DigitalLiteracyProgress.objects.filter(rider=rider)
            total_points = sum(p.points_earned for p in progress_records)
            total_sessions = sum(p.sessions_attended for p in progress_records)
            
            if total_points > 0:  # Only include riders with points
                leaderboard_data.append({
                    'rider_id': rider.id,
                    'name': rider.full_name,
                    'unique_id': rider.unique_id,
                    'phone_number': rider.phone_number,
                    'total_points': total_points,
                    'sessions_attended': total_sessions,
                    'badge_level': get_badge_level(total_points),
                })
        
        # Sort by points descending
        leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
        
        # Add ranking
        for i, rider in enumerate(leaderboard_data[:limit]):
            rider['rank'] = i + 1
            rider['position_icon'] = get_position_icon(i + 1)
        
        return Response({
            'success': True,
            'data': leaderboard_data[:limit],
            'total_participants': len(leaderboard_data),
            'period': period
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting leaderboard: {e}")
        return Response(
            {'error': 'Failed to get leaderboard'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])  
@permission_classes([AllowAny])
def digital_literacy_achievements(request):
    """Get rider achievements"""
    try:
        phone_number = request.GET.get('phone_number')
        if not phone_number:
            return Response(
                {'error': 'Phone number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f'🏅 Fetching achievements for rider: {phone_number}')
        
        rider = Rider.objects.filter(phone_number=phone_number).first()
        if not rider:
            return Response(
                {'error': 'Rider not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get rider's progress
        progress_records = DigitalLiteracyProgress.objects.filter(rider=rider)
        total_points = sum(p.points_earned for p in progress_records)
        total_sessions = sum(p.sessions_attended for p in progress_records)
        completed_modules = progress_records.filter(completed_at__isnull=False).count()
        
        # Define achievements
        achievements = []
        
        # Points-based achievements
        if total_points >= 100:
            achievements.append({
                'id': 1,
                'title': 'First Steps',
                'description': 'Earned your first 100 points',
                'icon': '🌱',
                'points_required': 100,
                'earned': True,
                'earned_date': progress_records.first().updated_at.isoformat() if progress_records.exists() else None,
                'category': 'Points'
            })
            
        if total_points >= 500:
            achievements.append({
                'id': 2,
                'title': 'Digital Explorer',
                'description': 'Reached 500 total points',
                'icon': '🚀',
                'points_required': 500,
                'earned': True,
                'earned_date': progress_records.first().updated_at.isoformat() if progress_records.exists() else None,
                'category': 'Points'
            })
            
        if total_points >= 1000:
            achievements.append({
                'id': 3,
                'title': 'Digital Master',
                'description': 'Achieved 1000 total points',
                'icon': '👑',
                'points_required': 1000,
                'earned': True,
                'earned_date': progress_records.first().updated_at.isoformat() if progress_records.exists() else None,
                'category': 'Points'
            })
        
        # Session-based achievements
        if total_sessions >= 5:
            achievements.append({
                'id': 4,
                'title': 'Active Learner',
                'description': 'Attended 5 training sessions',
                'icon': '📚',
                'sessions_required': 5,
                'earned': True,
                'earned_date': progress_records.first().updated_at.isoformat() if progress_records.exists() else None,
                'category': 'Attendance'
            })
            
        if total_sessions >= 15:
            achievements.append({
                'id': 5,
                'title': 'Dedicated Student',
                'description': 'Attended 15 training sessions',
                'icon': '🎓',
                'sessions_required': 15,
                'earned': True,
                'earned_date': progress_records.first().updated_at.isoformat() if progress_records.exists() else None,
                'category': 'Attendance'
            })
            
        # Module completion achievements
        if completed_modules >= 1:
            achievements.append({
                'id': 6,
                'title': 'Module Completer',
                'description': 'Completed your first training module',
                'icon': '✅',
                'modules_required': 1,
                'earned': True,
                'earned_date': progress_records.filter(completed_at__isnull=False).first().completed_at.isoformat() if progress_records.filter(completed_at__isnull=False).exists() else None,
                'category': 'Completion'
            })
            
        if completed_modules >= 3:
            achievements.append({
                'id': 7,
                'title': 'Triple Threat',
                'description': 'Completed 3 training modules',
                'icon': '🏆',
                'modules_required': 3,
                'earned': True,
                'earned_date': progress_records.filter(completed_at__isnull=False).first().completed_at.isoformat() if progress_records.filter(completed_at__isnull=False).exists() else None,
                'category': 'Completion'
            })
        
        earned_count = len(achievements)
        total_available = 20  # Total possible achievements
        
        return Response({
            'success': True,
            'data': achievements,
            'total_achievements': total_available,
            'earned_achievements': earned_count,
            'completion_percentage': round((earned_count / total_available) * 100, 1)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting achievements: {e}")
        return Response(
            {'error': 'Failed to get achievements'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny]) 
def digital_literacy_achievement_stats(request):
    """Get achievement statistics"""
    try:
        print('📊 Fetching achievement statistics...')
        
        # Get all riders with progress
        riders_with_progress = Rider.objects.filter(
            digitalliteracyprogress__isnull=False,
            approval_status='approved'
        ).distinct()
        
        total_riders = riders_with_progress.count()
        
        if total_riders == 0:
            return Response({
                'success': True,
                'data': {
                    'total_participants': 0,
                    'achievements_earned': 0,
                    'average_achievements_per_rider': 0,
                    'top_achievers': []
                }
            }, status=status.HTTP_200_OK)
        
        total_achievements_earned = 0
        top_achievers = []
        
        for rider in riders_with_progress:
            progress_records = DigitalLiteracyProgress.objects.filter(rider=rider)
            total_points = sum(p.points_earned for p in progress_records)
            total_sessions = sum(p.sessions_attended for p in progress_records)
            completed_modules = progress_records.filter(completed_at__isnull=False).count()
            
            # Count achievements for this rider
            achievements_count = 0
            if total_points >= 100: achievements_count += 1
            if total_points >= 500: achievements_count += 1  
            if total_points >= 1000: achievements_count += 1
            if total_sessions >= 5: achievements_count += 1
            if total_sessions >= 15: achievements_count += 1
            if completed_modules >= 1: achievements_count += 1
            if completed_modules >= 3: achievements_count += 1
            
            total_achievements_earned += achievements_count
            
            if achievements_count > 0:
                top_achievers.append({
                    'name': rider.full_name,
                    'unique_id': rider.unique_id,
                    'achievements_count': achievements_count,
                    'total_points': total_points
                })
        
        # Sort top achievers
        top_achievers.sort(key=lambda x: (x['achievements_count'], x['total_points']), reverse=True)
        
        return Response({
            'success': True,
            'data': {
                'total_participants': total_riders,
                'achievements_earned': total_achievements_earned,
                'average_achievements_per_rider': round(total_achievements_earned / total_riders, 1),
                'top_achievers': top_achievers[:10]
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting achievement stats: {e}")
        return Response(
            {'error': 'Failed to get achievement statistics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_badge_level(points):
    """Get badge level based on points"""
    if points >= 1000:
        return 'EXPERT'
    elif points >= 500:
        return 'ADVANCED'
    elif points >= 200:
        return 'INTERMEDIATE'
    else:
        return 'BEGINNER'

def get_position_icon(rank):
    """Get position icon based on rank"""
    if rank == 1:
        return '🥇'
    elif rank == 2:
        return '🥈'
    elif rank == 3:
        return '🥉'
    else:
        return '🏃'

@api_view(['GET'])
@permission_classes([AllowAny])
def digital_literacy_notifications(request):
    """Get rider notifications"""
    try:
        phone_number = request.GET.get('phone_number')
        if not phone_number:
            return Response(
                {'error': 'Phone number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f'🔔 Fetching notifications for rider: {phone_number}')
        
        rider = Rider.objects.filter(phone_number=phone_number).first()
        if not rider:
            return Response(
                {'error': 'Rider not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mock notifications for now (in production, you'd have a Notification model)
        from datetime import datetime, timedelta
        
        notifications = [
            {
                'id': 1,
                'type': 'session_reminder',
                'title': 'Training Session Tomorrow',
                'message': f'Your Digital Marketing session starts at 10:00 AM at your registered stage',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'is_read': False,
                'icon': '📅',
                'priority': 'high'
            },
            {
                'id': 2,
                'type': 'achievement',
                'title': 'New Achievement Unlocked! 🏆',
                'message': 'You\'ve earned the "Active Learner" badge for attending 5 sessions',
                'timestamp': (datetime.now() - timedelta(hours=5)).isoformat(),
                'is_read': False,
                'icon': '🏆',
                'priority': 'medium'
            },
            {
                'id': 3,
                'type': 'training_update',
                'title': 'New Training Module Available',
                'message': 'Advanced Digital Payment Systems module is now available',
                'timestamp': (datetime.now() - timedelta(hours=8)).isoformat(),
                'is_read': True,
                'icon': '📚',
                'priority': 'medium'
            }
        ]
        
        unread_count = len([n for n in notifications if not n['is_read']])
        
        return Response({
            'success': True,
            'data': notifications,
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting notifications: {e}")
        return Response(
            {'error': 'Failed to get notifications'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PATCH'])
@permission_classes([AllowAny])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        print(f'📖 Marking notification {notification_id} as read')
        
        # Mock implementation - in production you'd update a Notification model
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error marking notification read: {e}")
        return Response(
            {'error': 'Failed to mark notification as read'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PATCH'])
@permission_classes([AllowAny])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    try:
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response(
                {'error': 'Phone number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f'📖 Marking all notifications as read for {phone_number}')
        
        # Mock implementation - in production you'd update Notification models
        return Response({
            'success': True,
            'message': 'All notifications marked as read'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error marking all notifications read: {e}")
        return Response(
            {'error': 'Failed to mark all notifications as read'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def digital_literacy_certificates(request):
    """Get rider certificates"""
    try:
        phone_number = request.GET.get('phone_number')
        if not phone_number:
            return Response(
                {'error': 'Phone number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f'🏆 Fetching certificates for rider: {phone_number}')
        
        rider = Rider.objects.filter(phone_number=phone_number).first()
        if not rider:
            return Response(
                {'error': 'Rider not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get completed modules for certificates
        progress_records = DigitalLiteracyProgress.objects.filter(
            rider=rider, 
            completed_at__isnull=False
        )
        
        certificates = []
        
        for progress in progress_records:
            module = progress.module
            certificates.append({
                'id': progress.id,
                'title': module.title,
                'description': f'Completed {module.title} training program with {progress.completion_percentage}% completion',
                'icon': get_module_icon(module.title),
                'badge_color': get_badge_color(progress.points_earned),
                'earned_date': progress.completed_at.isoformat(),
                'points_earned': progress.points_earned,
                'skill_level': get_badge_level(progress.points_earned),
                'category': get_module_category(module.title),
                'progress': progress.completion_percentage,
                'is_earned': True,
                'certificate_number': f'DL-2024-{str(progress.id).zfill(3)}',
                'trainer_name': 'Digital Literacy Trainer',
                'sessions_completed': progress.sessions_attended,
                'total_sessions': module.session_count
            })
        
        # Add in-progress modules
        in_progress = DigitalLiteracyProgress.objects.filter(
            rider=rider,
            completed_at__isnull=True,
            sessions_attended__gt=0
        )
        
        for progress in in_progress:
            module = progress.module
            certificates.append({
                'id': progress.id + 1000,  # Offset to avoid ID conflicts
                'title': module.title,
                'description': f'In progress: {module.title} training program',
                'icon': get_module_icon(module.title),
                'badge_color': 0xFF757575,  # Gray for in-progress
                'earned_date': None,
                'points_earned': progress.points_earned,
                'skill_level': 'IN_PROGRESS',
                'category': get_module_category(module.title),
                'progress': progress.completion_percentage,
                'is_earned': False,
                'certificate_number': None,
                'trainer_name': 'Digital Literacy Trainer',
                'sessions_completed': progress.sessions_attended,
                'total_sessions': module.session_count
            })
        
        earned_count = len([c for c in certificates if c['is_earned']])
        total_points = sum(c['points_earned'] for c in certificates if c['is_earned'])
        
        return Response({
            'success': True,
            'data': certificates,
            'total_certificates': len(certificates),
            'earned_certificates': earned_count,
            'total_points_earned': total_points,
            'completion_rate': round((earned_count / len(certificates) * 100), 1) if certificates else 0
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting certificates: {e}")
        return Response(
            {'error': 'Failed to get certificates'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def digital_literacy_badges(request):
    """Get all available badges/certificates"""
    try:
        print('🏅 Fetching all available badges...')
        
        # Get all modules as potential badges
        modules = DigitalLiteracyModule.objects.all()
        
        badges = []
        for module in modules:
            badges.append({
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'icon': get_module_icon(module.title),
                'category': get_module_category(module.title),
                'points_required': 50 * module.session_count,  # Estimate points
                'sessions_required': module.session_count,
                'difficulty': get_badge_level(50 * module.session_count)
            })
        
        return Response({
            'success': True,
            'data': badges
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting badges: {e}")
        return Response(
            {'error': 'Failed to get badges'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_stage_id(request):
    """Verify stage ID for session attendance"""
    try:
        stage_id = request.GET.get('stage_id')
        schedule_id = request.GET.get('schedule_id')
        
        if not stage_id or not schedule_id:
            return Response(
                {'error': 'Stage ID and Schedule ID are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f'🔍 Verifying stage ID {stage_id} for session {schedule_id}')
        
        # Real stage verification using Stage model
        try:
            stage = Stage.objects.get(stage_id=stage_id, status=Stage.ACTIVE)
            is_valid = True
            stage_name = stage.name
            
            # Optional: Verify stage location matches session location
            try:
                schedule = SessionSchedule.objects.get(id=schedule_id)
                # Check if session location contains stage name (flexible matching)
                if schedule.location_name and stage.name.lower() not in schedule.location_name.lower():
                    print(f'⚠️  Stage {stage_id} ({stage.name}) may not match session location ({schedule.location_name})')
                    # Still allow, but log the mismatch
                    
            except SessionSchedule.DoesNotExist:
                print(f'⚠️  Session {schedule_id} not found for location verification')
                
        except Stage.DoesNotExist:
            is_valid = False
            stage_name = 'Unknown Stage'
        
        return Response({
            'success': True,
            'valid': is_valid,
            'stage_name': stage_name,
            'message': f'Stage verification {"successful" if is_valid else "failed"}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error verifying stage ID: {e}")
        return Response(
            {'error': 'Failed to verify stage ID'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_module_icon(title):
    """Get icon based on module title"""
    title_lower = title.lower()
    if 'marketing' in title_lower:
        return '📱'
    elif 'banking' in title_lower or 'payment' in title_lower:
        return '💳'
    elif 'smartphone' in title_lower or 'phone' in title_lower:
        return '📱'
    elif 'business' in title_lower:
        return '🏢'
    else:
        return '📚'

def get_badge_color(points):
    """Get badge color based on points"""
    if points >= 200:
        return 0xFF4CAF50  # Green
    elif points >= 100:
        return 0xFF2196F3  # Blue
    elif points >= 50:
        return 0xFFFF9800  # Orange
    else:
        return 0xFF757575  # Gray

def get_module_category(title):
    """Get category based on module title"""
    title_lower = title.lower()
    if 'marketing' in title_lower:
        return 'Marketing'
    elif 'banking' in title_lower or 'payment' in title_lower:
        return 'Finance'
    elif 'smartphone' in title_lower or 'phone' in title_lower:
        return 'Technology'
    elif 'business' in title_lower:
        return 'Business'
    else:
        return 'General'

@api_view(['POST'])
@permission_classes([AllowAny])
def register_for_session(request):
    """Register rider for a training session"""
    try:
        phone_number = request.data.get('phone_number')
        schedule_id = request.data.get('schedule_id')
        
        if not phone_number or not schedule_id:
            return Response(
                {'error': 'Phone number and schedule ID are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f'📝 Registering rider {phone_number} for session {schedule_id}')
        
        # Get rider
        rider = Rider.objects.filter(phone_number=phone_number).first()
        if not rider:
            return Response(
                {'error': 'Rider not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get session schedule
        try:
            schedule = SessionSchedule.objects.get(id=schedule_id)
        except SessionSchedule.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if session is still available
        if schedule.status != 'scheduled':
            return Response(
                {'error': 'Session registration is not available'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check capacity
        current_registrations = SessionAttendance.objects.filter(
            schedule=schedule,
            status__in=['registered', 'attended']
        ).count()
        
        if current_registrations >= schedule.capacity:
            return Response(
                {'error': 'Session is at full capacity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if rider is already registered
        existing_registration = SessionAttendance.objects.filter(
            rider=rider,
            schedule=schedule
        ).first()
        
        if existing_registration:
            return Response(
                {'error': 'You are already registered for this session'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create registration
        attendance = SessionAttendance.objects.create(
            rider=rider,
            schedule=schedule,
            status='registered',
            registration_date=timezone.now()
        )
        
        # Update registered count
        schedule.registered_count = SessionAttendance.objects.filter(
            schedule=schedule,
            status__in=['registered', 'attended']
        ).count()
        schedule.save()
        
        return Response({
            'success': True,
            'message': 'Successfully registered for training session!',
            'data': {
                'attendance_id': attendance.id,
                'session_title': schedule.session.title,
                'scheduled_date': schedule.scheduled_date.isoformat(),
                'location': schedule.location_name,
                'registration_status': 'registered'
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"💥 Error registering for session: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': 'Failed to register for session'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_session_status(request, schedule_id):
    """Get real-time session status and attendance information"""
    try:
        print(f'📊 Getting real-time status for session {schedule_id}')
        
        # Get session schedule
        try:
            schedule = SessionSchedule.objects.get(id=schedule_id)
        except SessionSchedule.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get current attendance count
        current_attendance = SessionAttendance.objects.filter(
            schedule=schedule,
            status__in=['registered', 'attended']
        ).count()
        
        # Get recent attendance registrations (last 5 minutes)
        from datetime import timedelta
        recent_cutoff = timezone.now() - timedelta(minutes=5)
        recent_registrations = SessionAttendance.objects.filter(
            schedule=schedule,
            created_at__gte=recent_cutoff,
            status__in=['registered', 'attended']
        ).count()
        
        # Check if attendance window is open
        now = timezone.now()
        session_start = schedule.scheduled_date
        
        # Attendance window: 30 minutes before to 30 minutes after session start
        attendance_window_start = session_start - timedelta(minutes=30)
        attendance_window_end = session_start + timedelta(minutes=30)
        
        is_attendance_open = attendance_window_start <= now <= attendance_window_end
        
        # Determine session phase
        if now < attendance_window_start:
            session_phase = 'upcoming'
        elif now <= attendance_window_end:
            session_phase = 'active'  # During attendance window
        elif now <= session_start + timedelta(hours=2):
            session_phase = 'in_session'  # During actual session
        else:
            session_phase = 'completed'
        
        # Get attendance list for trainers
        attendees = []
        if request.GET.get('include_attendees', '').lower() == 'true':
            attendance_records = SessionAttendance.objects.filter(
                schedule=schedule,
                status__in=['registered', 'attended']
            ).select_related('rider').order_by('-created_at')
            
            for attendance in attendance_records:
                attendees.append({
                    'rider_id': attendance.rider.id,
                    'rider_name': attendance.rider.full_name,
                    'unique_id': attendance.rider.unique_id,
                    'phone_number': attendance.rider.phone_number,
                    'status': attendance.status,
                    'registration_time': attendance.created_at.isoformat(),
                    'stage_id': getattr(attendance, 'stage_id_used', 'N/A'),
                })
        
        return Response({
            'success': True,
            'data': {
                'schedule_id': schedule.id,
                'session_title': schedule.session.title,
                'scheduled_date': schedule.scheduled_date.isoformat(),
                'location_name': schedule.location_name,
                'session_status': schedule.status,
                'session_phase': session_phase,
                'attendance_info': {
                    'current_count': current_attendance,
                    'capacity': schedule.capacity,
                    'available_spots': max(0, schedule.capacity - current_attendance),
                    'recent_registrations': recent_registrations,
                    'is_attendance_open': is_attendance_open,
                    'attendance_window_start': attendance_window_start.isoformat(),
                    'attendance_window_end': attendance_window_end.isoformat(),
                },
                'attendees': attendees,
                'last_updated': timezone.now().isoformat(),
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error getting session status: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': 'Failed to get session status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def check_attendance_window(request):
    """Check if attendance registration is allowed for a session"""
    try:
        schedule_id = request.GET.get('schedule_id')
        if not schedule_id:
            return Response(
                {'error': 'Schedule ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f'⏰ Checking attendance window for session {schedule_id}')
        
        # Get session schedule
        try:
            schedule = SessionSchedule.objects.get(id=schedule_id)
        except SessionSchedule.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        now = timezone.now()
        session_start = schedule.scheduled_date
        
        # Attendance window: 30 minutes before to 30 minutes after session start
        from datetime import timedelta
        window_start = session_start - timedelta(minutes=30)
        window_end = session_start + timedelta(minutes=30)
        
        is_open = window_start <= now <= window_end
        
        # Calculate time until window opens or closes
        if now < window_start:
            time_until_change = window_start - now
            status_message = f'Attendance opens in {format_timedelta(time_until_change)}'
            next_change = 'opens'
        elif now <= window_end:
            time_until_change = window_end - now
            status_message = f'Attendance closes in {format_timedelta(time_until_change)}'
            next_change = 'closes'
        else:
            time_until_change = None
            status_message = 'Attendance window has closed'
            next_change = 'closed'
        
        return Response({
            'success': True,
            'data': {
                'is_open': is_open,
                'window_start': window_start.isoformat(),
                'window_end': window_end.isoformat(),
                'current_time': now.isoformat(),
                'status_message': status_message,
                'next_change': next_change,
                'time_until_change_seconds': int(time_until_change.total_seconds()) if time_until_change else 0,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error checking attendance window: {e}")
        return Response(
            {'error': 'Failed to check attendance window'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def format_timedelta(td):
    """Format timedelta for human-readable display"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f'{hours}h {minutes}m'
    elif minutes > 0:
        return f'{minutes} minutes'
    else:
        return 'less than a minute'