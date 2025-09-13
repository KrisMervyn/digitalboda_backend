from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import hashlib
from .encryption import EncryptedIDField, IDEncryption, log_id_access


class Enumerator(models.Model):
    """Field agents who conduct training and verify riders"""
    
    # Status choices
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    SUSPENDED = 'SUSPENDED'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (SUSPENDED, 'Suspended'),
    ]

    # Basic Info
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='enumerator_profile')
    unique_id = models.CharField(max_length=20, unique=True)  # EN-YYYY-NNNN
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, unique=True)
    
    # Gender
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )
    
    # Assignment Info
    location = models.CharField(max_length=100)
    assigned_region = models.CharField(max_length=100)
    
    # Approval & Admin
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_enumerators'
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.unique_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate unique ID if not provided"""
        if not self.unique_id:
            self.generate_unique_id()
        super().save(*args, **kwargs)

    def generate_unique_id(self):
        """Generate a unique enumerator ID in format EN-YYYY-NNNN"""
        from django.utils import timezone
        current_year = timezone.now().year
        
        # Count existing enumerators with unique IDs this year
        existing_count = Enumerator.objects.filter(
            unique_id__startswith=f'EN-{current_year}-',
            unique_id__isnull=False
        ).exclude(unique_id='').count()
        
        # Generate next sequential number
        next_number = existing_count + 1
        unique_id = f'EN-{current_year}-{next_number:04d}'
        
        # Ensure uniqueness
        while Enumerator.objects.filter(unique_id=unique_id).exists():
            next_number += 1
            unique_id = f'EN-{current_year}-{next_number:04d}'
            
        self.unique_id = unique_id

    def get_assigned_riders(self):
        """Get all riders assigned to this enumerator"""
        return self.assigned_riders.all()

    def get_pending_riders(self):
        """Get riders pending approval by this enumerator"""
        return self.assigned_riders.filter(status=Rider.PENDING_APPROVAL)

class Rider(models.Model):
    # Status choices for the enhanced workflow
    REGISTERED = 'REGISTERED'
    ONBOARDING = 'ONBOARDING'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    SUSPENDED = 'SUSPENDED'
    
    STATUS_CHOICES = [
        (REGISTERED, 'Registered'),
        (ONBOARDING, 'In Onboarding'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (SUSPENDED, 'Suspended'),
    ]

    # Experience level choices
    NEW_RIDER = 'NEW'
    EXPERIENCED_RIDER = 'EXPERIENCED'
    
    EXPERIENCE_CHOICES = [
        (NEW_RIDER, 'New Rider'),
        (EXPERIENCED_RIDER, 'Experienced Rider'),
    ]

    # Basic Info
    phone_number = models.CharField(max_length=15, unique=True)
    first_name = models.CharField(max_length=50, default='')
    last_name = models.CharField(max_length=50, default='')
    fcm_token = models.TextField(blank=True, null=True)  # For push notifications
    
    # Enumerator Assignment
    assigned_enumerator = models.ForeignKey(
        Enumerator, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_riders'
    )
    enumerator_id_input = models.CharField(max_length=20, blank=True)  # ID provided during registration
    
    # Status & Approval
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=REGISTERED
    )
    
    # Profile & ID
    unique_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Personal Details
    age = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    experience_level = models.CharField(
        max_length=20, 
        choices=EXPERIENCE_CHOICES,
        default=NEW_RIDER
    )
    
    # Documents
    national_id_photo = models.ImageField(upload_to='documents/', blank=True, null=True)
    national_id_number = models.CharField(max_length=20, blank=True)  # DEPRECATED: Will be removed
    
    # SECURITY: Encrypted ID storage
    # national_id_encrypted = EncryptedIDField(blank=True, null=True, help_text="Encrypted ID number")
    national_id_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, 
                                       help_text="Hash for duplicate detection")
    
    # ID verification status
    id_verification_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('FLAGGED', 'Flagged for Review'),
    ], default='PENDING')
    
    id_verified_at = models.DateTimeField(blank=True, null=True)
    id_verified_by = models.ForeignKey('Enumerator', on_delete=models.SET_NULL, 
                                      null=True, blank=True, related_name='verified_ids')
    
    # Access tracking
    id_last_accessed = models.DateTimeField(blank=True, null=True)
    id_access_count = models.IntegerField(default=0)
    
    # SECURITY: Photo verification status
    photo_verification_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Photos Verified'),
        ('REJECTED', 'Photos Rejected'),
        ('FLAGGED', 'Flagged for Review'),
    ], default='PENDING')
    
    face_match_score = models.FloatField(null=True, blank=True, help_text="Face matching confidence score")
    photo_verified_at = models.DateTimeField(null=True, blank=True)
    photo_verified_by = models.ForeignKey('Enumerator', on_delete=models.SET_NULL, 
                                         null=True, blank=True, related_name='verified_photos')
    
    # Enumerator & Approval
    approved_by = models.ForeignKey(
        Enumerator, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='approved_riders'
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)
    
    # Training
    points = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def generate_unique_id(self):
        """Generate a unique profile ID in format DB-YYYY-NNNN"""
        from django.utils import timezone
        current_year = timezone.now().year
        
        # Count existing riders with unique IDs this year
        existing_count = Rider.objects.filter(
            unique_id__startswith=f'DB-{current_year}-',
            unique_id__isnull=False
        ).count()
        
        # Generate next sequential number
        next_number = existing_count + 1
        unique_id = f'DB-{current_year}-{next_number:04d}'
        
        # Ensure uniqueness
        while Rider.objects.filter(unique_id=unique_id).exists():
            next_number += 1
            unique_id = f'DB-{current_year}-{next_number:04d}'
            
        self.unique_id = unique_id
        self.save()
    
    def set_national_id(self, id_number, accessed_by=None, reason=None, request=None):
        """
        Securely set national ID with encryption and audit logging
        
        Args:
            id_number (str): Plain text ID number
            accessed_by (User): User setting the ID
            reason (str): Reason for setting ID
            request: HTTP request object for IP/user agent
        """
        if not id_number:
            return False
            
        # Validate ID format
        encryptor = IDEncryption()
        if not encryptor.validate_id_format(id_number):
            log_id_access(self, accessed_by, 'SET_ID', f"{reason} - INVALID FORMAT", 
                         success=False, 
                         ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR'),
                         user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT'))
            raise ValueError("Invalid Uganda National ID format")
        
        # Check for duplicates using hash
        id_hash = encryptor.hash_id_for_verification(id_number)
        if Rider.objects.filter(national_id_hash=id_hash).exclude(pk=self.pk).exists():
            log_id_access(self, accessed_by, 'SET_ID', f"{reason} - DUPLICATE", 
                         success=False,
                         ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR'),
                         user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT'))
            raise ValueError("This ID number is already registered")
        
        # Set encrypted ID and hash
        self.national_id_encrypted = id_number  # Will be encrypted by EncryptedIDField
        self.national_id_hash = id_hash
        self.id_verification_status = 'PENDING'
        self.save(update_fields=['national_id_encrypted', 'national_id_hash', 'id_verification_status'])
        
        # Log successful access
        log_id_access(self, accessed_by, 'SET_ID', reason,
                     ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR'),
                     user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT'))
        
        return True
    
    def get_national_id(self, accessed_by=None, reason=None, request=None):
        """
        Securely get national ID with authorization and audit logging
        
        Args:
            accessed_by (User): User requesting the ID
            reason (str): Reason for accessing ID
            request: HTTP request object for IP/user agent
            
        Returns:
            str: Plain text ID number or None
        """
        if not self.national_id_encrypted:
            return None
            
        # Check authorization
        if not self._authorize_id_access(accessed_by, reason):
            log_id_access(self, accessed_by, 'UNAUTHORIZED_ACCESS', reason, 
                         success=False,
                         ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR'),
                         user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT'))
            raise PermissionError("Unauthorized access to ID data")
        
        # Update access tracking
        self.id_last_accessed = timezone.now()
        self.id_access_count += 1
        self.save(update_fields=['id_last_accessed', 'id_access_count'])
        
        # Log access
        log_id_access(self, accessed_by, 'VIEW_ID', reason,
                     ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR'),
                     user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT'))
        
        # Return decrypted ID (EncryptedIDField handles decryption)
        return self.national_id_encrypted
    
    def get_masked_id(self):
        """
        Get masked version of ID for display purposes (CF12****7890)
        No authorization required for masked display
        """
        if not self.national_id_encrypted:
            return None
            
        try:
            full_id = self.national_id_encrypted  # Gets decrypted version
            if len(full_id) >= 8:
                # For 15-char IDs like CF1234567890123, show CF12******0123
                stars_count = len(full_id) - 8  # 15 - 8 = 7 stars
                return full_id[:4] + '*' * stars_count + full_id[-4:]
            else:
                return '***masked***'
        except:
            return '***masked***'
    
    def _authorize_id_access(self, accessed_by, reason):
        """
        Check if user is authorized to access ID data
        
        Args:
            accessed_by (User): User requesting access
            reason (str): Reason for access
            
        Returns:
            bool: True if authorized
        """
        if not accessed_by:
            return False
            
        # Admin users can always access
        if accessed_by.is_staff or accessed_by.is_superuser:
            return True
            
        # Enumerators can access IDs of their assigned riders
        try:
            enumerator = accessed_by.enumerator_profile
            if self.assigned_enumerator == enumerator:
                return True
        except:
            pass
            
        # User accessing their own ID
        rider_username = f"rider_{self.phone_number}"
        if accessed_by.username == rider_username:
            return True
            
        return False
    
    def check_duplicate_id(self, id_number):
        """
        Check for duplicate ID without exposing other IDs
        
        Args:
            id_number (str): Plain text ID to check
            
        Returns:
            bool: True if duplicate exists
        """
        if not id_number:
            return False
            
        encryptor = IDEncryption()
        id_hash = encryptor.hash_id_for_verification(id_number)
        
        return Rider.objects.filter(
            national_id_hash=id_hash
        ).exclude(pk=self.pk).exists()

# Import photo verification models and methods
try:
    from .photo_models import PhotoVerificationResult, add_photo_verification_methods
    # The methods will be added to Rider class automatically
except ImportError as e:
    import logging
    logging.getLogger('riders').warning(f"Photo verification not available: {e}")

class Lesson(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField()
    points_reward = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class RiderProgress(models.Model):
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['rider', 'lesson']


class RiderApplication(models.Model):
    """Track rider applications for enumerator review"""
    rider = models.OneToOneField(Rider, on_delete=models.CASCADE, related_name='application')
    reference_number = models.CharField(max_length=20, unique=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewer_notes = models.TextField(blank=True)
    assigned_enumerator_notified = models.BooleanField(default=False)

    def __str__(self):
        return f"Application {self.reference_number} - {self.rider.full_name}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            # Generate reference number: REF + timestamp
            import time
            self.reference_number = f"REF{int(time.time())}"
        super().save(*args, **kwargs)