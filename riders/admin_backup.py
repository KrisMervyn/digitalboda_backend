# Django Admin - Organized Digital Literacy Training Management
# Simple working version to test basic functionality

from django.contrib import admin
from django.utils.html import format_html

# Import models
from .models import (
    Rider, RiderApplication, Lesson, RiderProgress, Enumerator,
    DigitalLiteracyModule, TrainingSession, SessionSchedule, 
    SessionAttendance, Stage, StageRiderAssignment, NotificationSchedule
)

# Unregister any existing admin registrations to prevent conflicts
models_to_unregister = [
    Rider, RiderApplication, Lesson, RiderProgress, Enumerator,
    DigitalLiteracyModule, TrainingSession, SessionSchedule, 
    SessionAttendance, Stage, StageRiderAssignment, NotificationSchedule
]

for model in models_to_unregister:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

# Simple Admin Classes (Working Version)
@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone_number', 'status', 'created_at']
    list_filter = ['status', 'experience_level', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number', 'unique_id']
    readonly_fields = ['unique_id', 'created_at', 'updated_at']

@admin.register(Enumerator)
class EnumeratorAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone_number', 'status', 'assigned_region', 'created_at']
    list_filter = ['status', 'gender', 'assigned_region', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number', 'unique_id']
    readonly_fields = ['unique_id', 'created_at', 'updated_at']

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'module', 'session_number', 'duration_hours', 'points_value']
    list_filter = ['module', 'duration_hours', 'points_value']
    search_fields = ['title', 'description', 'module__title']

@admin.register(SessionSchedule)
class SessionScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'trainer', 'scheduled_date', 'location_name', 'capacity', 'status']
    list_filter = ['status', 'scheduled_date', 'trainer']
    search_fields = ['session__title', 'trainer__first_name', 'trainer__last_name', 'location_name']

@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'rider', 'schedule', 'status', 'registration_time', 'check_in_time']
    list_filter = ['status', 'registration_time']
    search_fields = ['rider__first_name', 'rider__last_name', 'rider__phone_number']

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ['stage_id', 'name', 'district', 'status', 'capacity', 'created_at']
    list_filter = ['status', 'district', 'division', 'created_at']
    search_fields = ['stage_id', 'name', 'address', 'district']

@admin.register(StageRiderAssignment)
class StageRiderAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'rider', 'stage', 'is_primary', 'status', 'assigned_date']
    list_filter = ['is_primary', 'status', 'assigned_date']
    search_fields = ['rider__first_name', 'rider__last_name', 'stage__name']

@admin.register(NotificationSchedule)
class NotificationScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'rider', 'notification_type', 'title', 'status', 'scheduled_time', 'sent_time']
    list_filter = ['status', 'notification_type', 'scheduled_time', 'created_at']
    search_fields = ['rider__first_name', 'rider__last_name', 'title', 'message']

# Simple registration for remaining models
admin.site.register(RiderApplication)
admin.site.register(Lesson)
admin.site.register(RiderProgress)
admin.site.register(DigitalLiteracyModule)

# Customize admin site headers
admin.site.site_header = "DigitalBoda - Training Management Admin"
admin.site.site_title = "DigitalBoda Admin"
admin.site.index_title = "Digital Literacy Training Management System"