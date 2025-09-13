from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Rider, Enumerator
import logging

logger = logging.getLogger('riders')

@api_view(['POST'])
@permission_classes([AllowAny])
def rider_login(request):
    """Login endpoint for riders using phone number"""
    phone_number = request.data.get('phone_number')
    
    if not phone_number:
        return Response({
            'error': 'Phone number is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find rider by phone number
        rider = Rider.objects.get(phone_number=phone_number)
        
        # Check if rider is approved
        if rider.status != 'APPROVED':
            return Response({
                'error': 'Account not approved yet',
                'status': rider.status
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Create or get user account for token authentication
        user, created = User.objects.get_or_create(
            username=f"rider_{phone_number}",
            defaults={
                'first_name': rider.first_name,
                'last_name': rider.last_name,
            }
        )
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        logger.info(f"Rider login successful: {rider.unique_id}")
        
        return Response({
            'token': token.key,
            'rider_id': rider.id,
            'unique_id': rider.unique_id,
            'full_name': f"{rider.first_name} {rider.last_name}",
            'status': rider.status,
            'points': rider.points
        })
        
    except Rider.DoesNotExist:
        return Response({
            'error': 'Rider not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def enumerator_login(request):
    """Login endpoint for enumerators"""
    unique_id = request.data.get('unique_id')
    password = request.data.get('password', '')
    
    if not unique_id:
        return Response({
            'error': 'Enumerator ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find enumerator by unique_id
        enumerator = Enumerator.objects.get(unique_id=unique_id)
        
        # Check if enumerator is active
        if enumerator.status != 'ACTIVE':
            return Response({
                'error': 'Account is not active',
                'status': enumerator.status
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Simple password check (in production, use proper authentication)
        # For now, we'll use the user account if it exists
        user = enumerator.user
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        logger.info(f"Enumerator login successful: {enumerator.unique_id}")
        
        return Response({
            'token': token.key,
            'enumerator_id': enumerator.id,
            'unique_id': enumerator.unique_id,
            'full_name': f"{enumerator.first_name} {enumerator.last_name}",
            'status': enumerator.status,
            'location': enumerator.location
        })
        
    except Enumerator.DoesNotExist:
        return Response({
            'error': 'Enumerator not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """Login endpoint for admin users"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user and user.is_staff:
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        logger.info(f"Admin login successful: {username}")
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })
    else:
        return Response({
            'error': 'Invalid credentials or insufficient permissions'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout(request):
    """Logout endpoint - delete token"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})
    except:
        return Response({'message': 'Already logged out'})

@api_view(['GET'])
def verify_token(request):
    """Verify if token is valid and return user info"""
    if request.user.is_authenticated:
        # Check if user is linked to rider or enumerator
        user_info = {
            'user_id': request.user.id,
            'username': request.user.username,
            'is_staff': request.user.is_staff,
        }
        
        # Check if user has rider profile
        try:
            rider = Rider.objects.get(phone_number=request.user.username.replace('rider_', ''))
            user_info.update({
                'type': 'rider',
                'rider_id': rider.id,
                'unique_id': rider.unique_id,
                'status': rider.status
            })
        except Rider.DoesNotExist:
            pass
        
        # Check if user has enumerator profile
        try:
            enumerator = Enumerator.objects.get(user=request.user)
            user_info.update({
                'type': 'enumerator',
                'enumerator_id': enumerator.id,
                'unique_id': enumerator.unique_id,
                'status': enumerator.status
            })
        except Enumerator.DoesNotExist:
            pass
        
        return Response(user_info)
    else:
        return Response({
            'error': 'Token invalid'
        }, status=status.HTTP_401_UNAUTHORIZED)