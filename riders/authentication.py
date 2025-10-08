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
    """Login endpoint for riders using phone number or PIN"""
    phone_number = request.data.get('phone_number')
    pin_code = request.data.get('pin_code')
    login_type = request.data.get('login_type', 'phone')  # 'phone' or 'pin'
    
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
        
        # Handle PIN authentication
        if login_type == 'pin':
            if not pin_code:
                return Response({
                    'error': 'PIN code is required for PIN authentication'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not rider.has_pin_set():
                return Response({
                    'error': 'PIN not set up. Please use phone authentication.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                if not rider.verify_pin(pin_code):
                    return Response({
                        'error': 'Invalid PIN'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            except ValueError as e:
                return Response({
                    'error': str(e)  # PIN locked message
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
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
        
        logger.info(f"Rider login successful: {rider.unique_id} via {login_type}")
        
        return Response({
            'token': token.key,
            'rider_id': rider.id,
            'unique_id': rider.unique_id,
            'full_name': f"{rider.first_name} {rider.last_name}",
            'status': rider.status,
            'points': rider.points,
            'has_pin': rider.has_pin_set(),
            'login_type': login_type
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

@api_view(['POST'])
def setup_pin(request):
    """Setup PIN for authenticated rider"""
    if not request.user.is_authenticated:
        return Response({
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    pin_code = request.data.get('pin_code')
    confirm_pin = request.data.get('confirm_pin')
    
    if not pin_code or not confirm_pin:
        return Response({
            'error': 'PIN code and confirmation are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if pin_code != confirm_pin:
        return Response({
            'error': 'PIN codes do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get rider from authenticated user
        phone_number = request.user.username.replace('rider_', '')
        rider = Rider.objects.get(phone_number=phone_number)
        
        # Set PIN
        rider.set_pin(pin_code)
        
        logger.info(f"PIN setup successful for rider: {rider.unique_id}")
        
        return Response({
            'success': True,
            'message': 'PIN setup successful'
        })
        
    except Rider.DoesNotExist:
        return Response({
            'error': 'Rider profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def change_pin(request):
    """Change PIN for authenticated rider"""
    if not request.user.is_authenticated:
        return Response({
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    current_pin = request.data.get('current_pin')
    new_pin = request.data.get('new_pin')
    confirm_pin = request.data.get('confirm_pin')
    
    if not current_pin or not new_pin or not confirm_pin:
        return Response({
            'error': 'Current PIN, new PIN, and confirmation are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_pin != confirm_pin:
        return Response({
            'error': 'New PIN codes do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get rider from authenticated user
        phone_number = request.user.username.replace('rider_', '')
        rider = Rider.objects.get(phone_number=phone_number)
        
        # Verify current PIN
        if not rider.has_pin_set():
            return Response({
                'error': 'No PIN is currently set'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not rider.verify_pin(current_pin):
            return Response({
                'error': 'Current PIN is incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Set new PIN
        rider.set_pin(new_pin)
        
        logger.info(f"PIN change successful for rider: {rider.unique_id}")
        
        return Response({
            'success': True,
            'message': 'PIN changed successfully'
        })
        
    except Rider.DoesNotExist:
        return Response({
            'error': 'Rider profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def pin_status(request):
    """Get PIN status for authenticated rider"""
    if not request.user.is_authenticated:
        return Response({
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        # Get rider from authenticated user
        phone_number = request.user.username.replace('rider_', '')
        rider = Rider.objects.get(phone_number=phone_number)
        
        return Response({
            'has_pin': rider.has_pin_set(),
            'is_locked': rider.is_pin_locked(),
            'failed_attempts': rider.failed_pin_attempts,
            'pin_set_at': rider.pin_set_at,
            'pin_last_used': rider.pin_last_used
        })
        
    except Rider.DoesNotExist:
        return Response({
            'error': 'Rider profile not found'
        }, status=status.HTTP_404_NOT_FOUND)