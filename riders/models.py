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
    # Age brackets instead of exact age
    AGE_BRACKET_CHOICES = [
        ('18-23', '18-23 (Young Adult)'),
        ('24-29', '24-29 (Early Career)'),
        ('30-35', '30-35 (Mid Career)'),
        ('36-41', '36-41 (Experienced)'),
        ('42-47', '42-47 (Senior)'),
        ('48-53', '48-53 (Veteran)'),
        ('54-59', '54-59 (Pre-retirement)'),
        ('60-65', '60-65 (Senior Citizen)'),
        ('66+', '66+ (Elder)'),
    ]
    
    age = models.IntegerField(blank=True, null=True)  # DEPRECATED: Keep for migration
    age_bracket = models.CharField(
        max_length=10,
        choices=AGE_BRACKET_CHOICES,
        blank=True,
        null=True,
        help_text="Age bracket instead of exact age for privacy"
    )
    location = models.CharField(max_length=100, blank=True)
    experience_level = models.CharField(
        max_length=20, 
        choices=EXPERIENCE_CHOICES,
        default=NEW_RIDER
    )
    
    # PIN Authentication
    pin_hash = models.CharField(
        max_length=128, 
        blank=True, 
        null=True,
        help_text="Hashed PIN for quick authentication"
    )
    pin_set_at = models.DateTimeField(blank=True, null=True)
    pin_last_used = models.DateTimeField(blank=True, null=True)
    failed_pin_attempts = models.IntegerField(default=0)
    pin_locked_until = models.DateTimeField(blank=True, null=True)
    
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
    
    def set_pin(self, pin_code):
        """
        Set PIN for quick authentication
        
        Args:
            pin_code (str): 4-6 digit PIN code
            
        Returns:
            bool: True if PIN was set successfully
        """
        import bcrypt
        from django.utils import timezone
        
        # Validate PIN format (4-6 digits)
        if not pin_code or not pin_code.isdigit() or len(pin_code) < 4 or len(pin_code) > 6:
            raise ValueError("PIN must be 4-6 digits")
        
        # Hash the PIN
        pin_bytes = pin_code.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_pin = bcrypt.hashpw(pin_bytes, salt)
        
        # Save to database
        self.pin_hash = hashed_pin.decode('utf-8')
        self.pin_set_at = timezone.now()
        self.failed_pin_attempts = 0
        self.pin_locked_until = None
        self.save(update_fields=['pin_hash', 'pin_set_at', 'failed_pin_attempts', 'pin_locked_until'])
        
        return True
    
    def verify_pin(self, pin_code):
        """
        Verify PIN for authentication
        
        Args:
            pin_code (str): PIN code to verify
            
        Returns:
            bool: True if PIN is correct
        """
        import bcrypt
        from django.utils import timezone
        
        # Check if PIN is set
        if not self.pin_hash:
            return False
            
        # Check if PIN is locked
        if self.pin_locked_until and timezone.now() < self.pin_locked_until:
            raise ValueError("PIN is temporarily locked due to too many failed attempts")
        
        # Verify PIN
        pin_bytes = pin_code.encode('utf-8')
        stored_hash = self.pin_hash.encode('utf-8')
        
        if bcrypt.checkpw(pin_bytes, stored_hash):
            # PIN correct - reset failed attempts and update last used
            self.failed_pin_attempts = 0
            self.pin_last_used = timezone.now()
            self.pin_locked_until = None
            self.save(update_fields=['failed_pin_attempts', 'pin_last_used', 'pin_locked_until'])
            return True
        else:
            # PIN incorrect - increment failed attempts
            self.failed_pin_attempts += 1
            
            # Lock PIN after 5 failed attempts for 30 minutes
            if self.failed_pin_attempts >= 5:
                from datetime import timedelta
                self.pin_locked_until = timezone.now() + timedelta(minutes=30)
            
            self.save(update_fields=['failed_pin_attempts', 'pin_locked_until'])
            return False
    
    def has_pin_set(self):
        """Check if rider has a PIN set"""
        return bool(self.pin_hash)
    
    def is_pin_locked(self):
        """Check if PIN is currently locked"""
        from django.utils import timezone
        return self.pin_locked_until and timezone.now() < self.pin_locked_until
    
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


# =============================================================================
# DIGITAL LITERACY TRAINING MODELS
# =============================================================================

class DigitalLiteracyModule(models.Model):
    """Digital literacy training modules"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    session_count = models.IntegerField(default=0)
    total_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    points_value = models.IntegerField()
    icon = models.CharField(max_length=50, default='📱')  # Emoji icon for UI
    order = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} ({self.session_count} sessions)"

class TrainingSession(models.Model):
    """Individual sessions within a digital literacy module"""
    module = models.ForeignKey(DigitalLiteracyModule, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    learning_objectives = models.JSONField(default=list)  # List of learning objectives
    required_materials = models.JSONField(default=list)  # List of required materials/devices
    points_value = models.IntegerField()
    
    class Meta:
        ordering = ['module', 'session_number']
        unique_together = ['module', 'session_number']
    
    def __str__(self):
        return f"{self.module.title} - Session {self.session_number}: {self.title}"

class SessionSchedule(models.Model):
    """Scheduled training sessions with specific trainers, times, and locations"""
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='schedules')
    trainer = models.ForeignKey(Enumerator, on_delete=models.CASCADE, related_name='training_sessions')
    scheduled_date = models.DateTimeField()
    location_name = models.CharField(max_length=200)
    location_address = models.TextField()
    gps_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    capacity = models.IntegerField(default=20)
    status_choices = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='SCHEDULED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.session.title} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')} @ {self.location_name}"
    
    @property
    def registered_count(self):
        """Get number of registered attendees"""
        return self.attendance_records.filter(status__in=['REGISTERED', 'ATTENDED']).count()
    
    @property
    def spots_remaining(self):
        """Get remaining capacity"""
        return max(0, self.capacity - self.registered_count)

class SessionAttendance(models.Model):
    """Track attendance at physical training sessions"""
    schedule = models.ForeignKey(SessionSchedule, on_delete=models.CASCADE, related_name='attendance_records')
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='training_attendance')
    registration_time = models.DateTimeField(auto_now_add=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_gps_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    check_in_gps_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    status_choices = [
        ('REGISTERED', 'Registered'),
        ('ATTENDED', 'Attended'),
        ('NO_SHOW', 'No Show'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='REGISTERED')
    trainer_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['schedule', 'rider']
        ordering = ['-registration_time']
    
    def __str__(self):
        return f"{self.rider.full_name} - {self.schedule.session.title} ({self.status})"
    
    def calculate_distance_from_venue(self):
        """Calculate distance between check-in location and scheduled venue"""
        if not all([self.check_in_gps_latitude, self.check_in_gps_longitude, 
                   self.schedule.gps_latitude, self.schedule.gps_longitude]):
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1 = radians(float(self.check_in_gps_latitude))
        lon1 = radians(float(self.check_in_gps_longitude))
        lat2 = radians(float(self.schedule.gps_latitude))
        lon2 = radians(float(self.schedule.gps_longitude))
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r * 1000  # Return distance in meters

class AttendanceVerification(models.Model):
    """Dual verification system for attendance"""
    attendance = models.OneToOneField(SessionAttendance, on_delete=models.CASCADE, related_name='verification')
    rider_verified = models.BooleanField(default=False)
    rider_verification_time = models.DateTimeField(null=True, blank=True)
    trainer_verified = models.BooleanField(default=False)
    trainer_verification_time = models.DateTimeField(null=True, blank=True)
    trainer_id_entered = models.CharField(max_length=50)  # The ID the rider entered
    distance_from_venue_meters = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    @property
    def is_fully_verified(self):
        return self.rider_verified and self.trainer_verified
    
    def __str__(self):
        verification_status = "Verified" if self.is_fully_verified else "Pending"
        return f"{self.attendance} - {verification_status}"

class DigitalLiteracyProgress(models.Model):
    """Track rider's progress through digital literacy modules"""
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='digital_literacy_progress')
    module = models.ForeignKey(DigitalLiteracyModule, on_delete=models.CASCADE)
    sessions_attended = models.IntegerField(default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    skill_level_choices = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    ]
    skill_level = models.CharField(max_length=20, choices=skill_level_choices, default='BEGINNER')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_session_attended = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['rider', 'module']
    
    def __str__(self):
        return f"{self.rider.full_name} - {self.module.title} ({self.completion_percentage}%)"
    
    def update_progress(self):
        """Update completion percentage based on attended sessions"""
        total_sessions = self.module.session_count
        if total_sessions > 0:
            self.completion_percentage = (self.sessions_attended / total_sessions) * 100
            if self.completion_percentage >= 100:
                self.completed_at = timezone.now()
        self.save()

class PostSessionAssessment(models.Model):
    """Assessment after each training session"""
    attendance = models.OneToOneField(SessionAttendance, on_delete=models.CASCADE, related_name='assessment')
    practical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0-100
    quiz_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0-100
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0-100
    
    feedback_choices = [
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('SATISFACTORY', 'Satisfactory'),
        ('NEEDS_IMPROVEMENT', 'Needs Improvement'),
    ]
    trainer_feedback = models.CharField(max_length=20, choices=feedback_choices, null=True, blank=True)
    trainer_notes = models.TextField(blank=True)
    self_assessment_rating = models.IntegerField(null=True, blank=True)  # 1-5 scale
    completed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Assessment - {self.attendance}"
    
    def calculate_overall_score(self):
        """Calculate overall score from practical and quiz scores"""
        scores = [score for score in [self.practical_score, self.quiz_score] if score is not None]
        if scores:
            self.overall_score = sum(scores) / len(scores)
            self.save()

class DigitalSkillsPoints(models.Model):
    """Enhanced points system for digital literacy training"""
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='digital_points')
    attendance = models.ForeignKey(SessionAttendance, on_delete=models.CASCADE, null=True, blank=True)
    points = models.IntegerField()
    
    source_choices = [
        ('ATTENDANCE', 'Session Attendance'),
        ('ASSESSMENT', 'Post-Session Assessment'),
        ('PERFECT_ATTENDANCE', 'Perfect Module Attendance'),
        ('EARLY_REGISTRATION', 'Early Registration'),
        ('PEER_REFERRAL', 'Peer Referral'),
        ('TRAINER_BONUS', 'Trainer Recognition Bonus'),
        ('SKILL_MILESTONE', 'Digital Skill Milestone'),
    ]
    source = models.CharField(max_length=20, choices=source_choices)
    bonus_type = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.rider.full_name} - {self.points} points ({self.source})"


class Stage(models.Model):
    """Boda boda stages where riders operate and training sessions are held"""
    
    # Status choices
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    MAINTENANCE = 'MAINTENANCE'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (MAINTENANCE, 'Under Maintenance'),
    ]
    
    # Basic Information
    stage_id = models.CharField(max_length=20, unique=True, help_text="Unique stage identifier (e.g., STAGE001)")
    name = models.CharField(max_length=100, help_text="Stage name")
    description = models.TextField(blank=True, help_text="Stage description or additional info")
    
    # Location Information  
    address = models.CharField(max_length=200, help_text="Physical address of the stage")
    district = models.CharField(max_length=50, help_text="District where stage is located")
    division = models.CharField(max_length=50, blank=True, help_text="Division/sub-county")
    parish = models.CharField(max_length=50, blank=True, help_text="Parish/ward")
    
    # GPS Coordinates (optional backup verification)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    gps_radius = models.IntegerField(default=100, help_text="Allowed GPS radius in meters for verification")
    
    # Operational Information
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=ACTIVE)
    capacity = models.IntegerField(default=50, help_text="Maximum number of riders at this stage")
    training_capacity = models.IntegerField(default=25, help_text="Maximum participants per training session")
    
    # Management
    stage_chairman = models.CharField(max_length=100, blank=True, help_text="Stage chairman name")
    chairman_phone = models.CharField(max_length=15, blank=True, help_text="Chairman contact")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['stage_id']
        verbose_name = 'Boda Boda Stage'
        verbose_name_plural = 'Boda Boda Stages'
    
    def __str__(self):
        return f"{self.stage_id} - {self.name}"
    
    def get_active_riders_count(self):
        """Get count of active riders at this stage"""
        return self.riders.filter(approval_status='approved').count()
    
    def get_training_sessions_count(self):
        """Get count of training sessions held at this stage"""
        return SessionSchedule.objects.filter(
            location_name__icontains=self.name
        ).count()
    
    @classmethod
    def verify_stage_for_location(cls, stage_id, location_name=None):
        """Verify if a stage ID is valid for a given location"""
        try:
            stage = cls.objects.get(stage_id=stage_id, status=cls.ACTIVE)
            
            # If location name is provided, check if it matches
            if location_name and location_name.lower() not in stage.name.lower():
                return False, f"Stage {stage_id} is not at {location_name}"
                
            return True, f"Stage verified: {stage.name}"
        except cls.DoesNotExist:
            return False, f"Invalid stage ID: {stage_id}"


class StageRiderAssignment(models.Model):
    """Assignment of riders to specific stages"""
    
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE, related_name='stage_assignments')
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='rider_assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=True, help_text="Is this the rider's primary stage?")
    status = models.CharField(max_length=10, choices=[
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ], default='ACTIVE')
    
    class Meta:
        unique_together = ['rider', 'stage']
        ordering = ['-is_primary', '-assigned_date']
    
    def __str__(self):
        return f"{self.rider.full_name} at {self.stage.name}"


class NotificationSchedule(models.Model):
    """Scheduled push notifications for training reminders"""
    
    # Notification types
    SESSION_REMINDER = 'session_reminder'
    ATTENDANCE_WINDOW = 'attendance_window'
    SESSION_STARTING = 'session_starting'
    ACHIEVEMENT_UNLOCKED = 'achievement_unlocked'
    NEW_MODULE_AVAILABLE = 'new_module'
    WEEKLY_PROGRESS = 'weekly_progress'
    
    NOTIFICATION_TYPES = [
        (SESSION_REMINDER, 'Session Reminder'),
        (ATTENDANCE_WINDOW, 'Attendance Window Open'),
        (SESSION_STARTING, 'Session Starting Soon'),
        (ACHIEVEMENT_UNLOCKED, 'Achievement Unlocked'),
        (NEW_MODULE_AVAILABLE, 'New Module Available'),
        (WEEKLY_PROGRESS, 'Weekly Progress Report'),
    ]
    
    # Status choices
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SENT, 'Sent'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    # Core fields
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='scheduled_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    
    # Scheduling
    scheduled_time = models.DateTimeField(help_text="When to send this notification")
    sent_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    
    # Related objects (optional)
    session_schedule = models.ForeignKey(SessionSchedule, on_delete=models.CASCADE, null=True, blank=True)
    module = models.ForeignKey(DigitalLiteracyModule, on_delete=models.CASCADE, null=True, blank=True)
    
    # Notification data
    data = models.JSONField(default=dict, blank=True, help_text="Additional data for the notification")
    
    # Retry and error handling
    attempt_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_time', 'status']),
            models.Index(fields=['rider', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.rider.full_name} at {self.scheduled_time}"
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = self.SENT
        self.sent_time = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_msg=""):
        """Mark notification as failed"""
        self.status = self.FAILED
        self.error_message = error_msg
        self.attempt_count += 1
        self.save()
    
    @classmethod
    def schedule_session_reminders(cls, session_schedule):
        """Schedule all reminders for a training session"""
        from datetime import timedelta
        
        # Get registered riders for this session
        registered_riders = Rider.objects.filter(
            sessionattendance__schedule=session_schedule,
            sessionattendance__status__in=['registered', 'attended']
        ).distinct()
        
        reminders = []
        session_start = session_schedule.scheduled_date
        
        for rider in registered_riders:
            # 1 day before reminder
            day_before = session_start - timedelta(days=1)
            if day_before > timezone.now():
                reminders.append(cls(
                    rider=rider,
                    notification_type=cls.SESSION_REMINDER,
                    title=f"Training Tomorrow: {session_schedule.session.title}",
                    message=f"Don't forget your {session_schedule.session.title} session tomorrow at {session_start.strftime('%I:%M %p')} at {session_schedule.location_name}",
                    scheduled_time=day_before,
                    session_schedule=session_schedule,
                    data={
                        'session_id': session_schedule.id,
                        'action': 'view_session'
                    }
                ))
            
            # 1 hour before reminder
            hour_before = session_start - timedelta(hours=1)
            if hour_before > timezone.now():
                reminders.append(cls(
                    rider=rider,
                    notification_type=cls.SESSION_STARTING,
                    title=f"Session Starting Soon!",
                    message=f"Your {session_schedule.session.title} session starts in 1 hour. Make sure to arrive on time!",
                    scheduled_time=hour_before,
                    session_schedule=session_schedule,
                    data={
                        'session_id': session_schedule.id,
                        'action': 'view_session'
                    }
                ))
            
            # Attendance window opening (30 minutes before)
            attendance_window = session_start - timedelta(minutes=30)
            if attendance_window > timezone.now():
                reminders.append(cls(
                    rider=rider,
                    notification_type=cls.ATTENDANCE_WINDOW,
                    title="Attendance Registration Open",
                    message=f"You can now register your attendance for {session_schedule.session.title}. Session starts in 30 minutes!",
                    scheduled_time=attendance_window,
                    session_schedule=session_schedule,
                    data={
                        'session_id': session_schedule.id,
                        'action': 'register_attendance'
                    }
                ))
        
        # Bulk create all reminders
        if reminders:
            cls.objects.bulk_create(reminders)
        
        return len(reminders)