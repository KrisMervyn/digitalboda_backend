"""
ID Number Encryption and Protection System
This module provides secure encryption and hashing for sensitive ID numbers.
"""

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
import base64
import hashlib
import logging

logger = logging.getLogger('riders')

class IDEncryption:
    """Service for encrypting/decrypting ID numbers and creating verification hashes"""
    
    def __init__(self):
        """Initialize encryption service with keys from settings"""
        if not settings.ID_ENCRYPTION_KEY:
            raise ValueError("ID_ENCRYPTION_KEY must be set in settings")
        
        try:
            # Ensure the key is properly formatted
            key = settings.ID_ENCRYPTION_KEY.encode() if isinstance(settings.ID_ENCRYPTION_KEY, str) else settings.ID_ENCRYPTION_KEY
            self.cipher_suite = Fernet(key)
        except Exception as e:
            raise ValueError(f"Invalid ID_ENCRYPTION_KEY: {e}")
    
    def encrypt_id(self, id_number):
        """
        Encrypt ID number for secure database storage
        
        Args:
            id_number (str): Plain text ID number
            
        Returns:
            str: Encrypted ID number (base64 encoded)
        """
        if not id_number:
            return None
            
        try:
            encrypted = self.cipher_suite.encrypt(id_number.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"ID encryption failed: {e}")
            raise ValueError(f"Failed to encrypt ID: {e}")
    
    def decrypt_id(self, encrypted_id):
        """
        Decrypt ID number for authorized access only
        
        Args:
            encrypted_id (str): Encrypted ID number
            
        Returns:
            str: Plain text ID number
        """
        if not encrypted_id:
            return None
            
        try:
            decrypted = self.cipher_suite.decrypt(encrypted_id.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"ID decryption failed: {e}")
            return None
    
    def hash_id_for_verification(self, id_number):
        """
        Create hash for duplicate checking without storing actual ID
        
        Args:
            id_number (str): Plain text ID number
            
        Returns:
            str: SHA256 hash for duplicate detection
        """
        if not id_number:
            return None
            
        # Combine ID with salt to prevent rainbow table attacks
        salted_id = f"{id_number}{settings.ID_HASH_SALT}"
        return hashlib.sha256(salted_id.encode()).hexdigest()
    
    def validate_id_format(self, id_number):
        """
        Validate Uganda National ID format
        
        Args:
            id_number (str): ID number to validate
            
        Returns:
            bool: True if valid format
        """
        if not id_number:
            return False
            
        # Remove any whitespace
        id_number = id_number.strip()
        
        # Uganda National ID is typically 14-15 characters (CF/CM + 12-13 digits)
        if len(id_number) < 14 or len(id_number) > 15:
            return False
        
        # Uganda ID format: CF + 11-12 digits OR CM + 11-12 digits
        if not (id_number.startswith('CF') or id_number.startswith('CM')):
            return False
        
        # Check if remaining characters are digits
        return id_number[2:].isdigit()


class EncryptedIDField(models.TextField):
    """
    Custom Django model field that automatically encrypts/decrypts ID numbers
    """
    
    def __init__(self, *args, **kwargs):
        self.encryptor = IDEncryption()
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Encrypt value before saving to database"""
        if value is None:
            return value
        # If it's already encrypted (long string), don't encrypt again
        if isinstance(value, str) and len(value) > 50:
            return value
        return self.encryptor.encrypt_id(str(value))
    
    def from_db_value(self, value, expression, connection):
        """Decrypt value when loading from database"""
        if value is None:
            return value
        # If it looks encrypted, decrypt it
        if isinstance(value, str) and len(value) > 50:
            return self.encryptor.decrypt_id(value)
        return value
    
    def to_python(self, value):
        """Convert value to Python representation"""
        if value is None:
            return value
        if isinstance(value, str) and len(value) > 50:  # Likely encrypted
            return self.encryptor.decrypt_id(value)
        return str(value)


class IDAccessLog(models.Model):
    """
    Audit trail for all ID number access
    """
    
    ACTION_CHOICES = [
        ('VIEW_ID', 'Viewed ID'),
        ('SET_ID', 'Set ID'),
        ('VERIFY_ID', 'Verified ID'),
        ('UPDATE_ID', 'Updated ID'),
        ('EXPORT_ID', 'Exported ID'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
    ]
    
    # Foreign keys
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE, related_name='id_access_logs')
    accessed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Access details
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    reason = models.CharField(max_length=200, blank=True, help_text="Reason for accessing ID")
    success = models.BooleanField(default=True)
    
    # Security information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['rider', '-timestamp']),
            models.Index(fields=['accessed_by', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} on Rider {self.rider_id} by {self.accessed_by} at {self.timestamp}"


def log_id_access(rider, user, action, reason=None, success=True, ip_address=None, user_agent=None):
    """
    Utility function to log ID access attempts
    
    Args:
        rider: Rider instance
        user: User who accessed the ID
        action: Action performed (from ACTION_CHOICES)
        reason: Reason for access
        success: Whether access was successful
        ip_address: IP address of accessor
        user_agent: User agent string
    """
    try:
        IDAccessLog.objects.create(
            rider=rider,
            accessed_by=user,
            action=action,
            reason=reason or '',
            success=success,
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        
        # Log security events
        if not success:
            logger.warning(f"Unauthorized ID access attempt: {action} on Rider {rider.id} by {user}")
        else:
            logger.info(f"ID access: {action} on Rider {rider.id} by {user}")
            
    except Exception as e:
        logger.error(f"Failed to log ID access: {e}")