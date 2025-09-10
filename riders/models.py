from django.db import models
from django.contrib.auth.models import User
import uuid


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
    national_id_number = models.CharField(max_length=20, blank=True)
    
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