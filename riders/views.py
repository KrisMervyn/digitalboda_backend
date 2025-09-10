from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Rider, Lesson, RiderProgress, RiderApplication, Enumerator
from .services.notification_service import FCMService

def verify_firebase_token(request):
    """Helper function to verify Firebase ID token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    # For now, we'll do basic token validation
    # In production, you'd verify with Firebase Admin SDK
    token = auth_header.split(' ')[1]
    if len(token) > 50:  # Basic token format check
        return {'phone_number': None}  # Mock decoded token
    return None

@api_view(['POST', 'GET'])
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
def submit_onboarding(request):
    """Submit rider onboarding information"""
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
        rider.age = request.data.get('age')
        rider.location = request.data.get('location')
        rider.national_id_number = request.data.get('nationalIdNumber')
        
        # Move rider to onboarding complete status
        rider.status = Rider.PENDING_APPROVAL
        rider.save()
        
        # Create RiderApplication for admin review
        from .models import RiderApplication
        application, created = RiderApplication.objects.get_or_create(
            rider=rider,
            defaults={'submitted_at': timezone.now()}
        )
        
        return Response({
            'message': 'Onboarding submitted successfully!',
            'status': rider.status,
            'reference_number': application.reference_number,
            'referenceNumber': application.reference_number,  # Compatibility
            'applicationRef': application.reference_number,   # Legacy compatibility
            'nextStep': 'pending_approval'
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
    """Helper function to verify admin authentication"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return None
    
    try:
        import base64
        credentials = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
        username, password = credentials.split(':')
        
        # Authenticate admin user
        user = authenticate(username=username, password=password)
        if user and user.is_staff:
            return user
    except (ValueError, TypeError):
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
        rider.approved_by = admin_user
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

@api_view(['GET'])
def admin_dashboard_stats(request):
    """Get admin dashboard statistics"""
    # Verify admin authentication
    admin_user = verify_admin_auth(request)
    if not admin_user:
        return Response(
            {'error': 'Admin authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Calculate statistics
    total_riders = Rider.objects.count()
    pending_approval = Rider.objects.filter(status=Rider.PENDING_APPROVAL).count()
    approved_riders = Rider.objects.filter(status=Rider.APPROVED).count()
    rejected_riders = Rider.objects.filter(status=Rider.REJECTED).count()
    registered_riders = Rider.objects.filter(status=Rider.REGISTERED).count()
    
    # Recent applications (last 7 days)
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    recent_applications = Rider.objects.filter(
        status=Rider.PENDING_APPROVAL,
        updated_at__gte=week_ago
    ).count()
    
    return Response({
        'totalRiders': total_riders,
        'pendingApproval': pending_approval,
        'approvedRiders': approved_riders,
        'rejectedRiders': rejected_riders,
        'registeredRiders': registered_riders,
        'recentApplications': recent_applications,
        'approvalRate': round((approved_riders / total_riders * 100), 2) if total_riders > 0 else 0
    }, status=status.HTTP_200_OK)


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
            'createdAt': rider.created_at
        })
    
    return Response({
        'riders': riders_data,
        'count': len(riders_data)
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
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