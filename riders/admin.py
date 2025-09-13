# Django Admin - Limited Configuration
# Main admin management is done via the DigitalBoda Admin mobile app
# This is kept minimal for emergency access and debugging only

from django.contrib import admin
from django.utils.html import format_html
from .models import Rider, RiderApplication, Lesson, RiderProgress, Enumerator

# Simple admin configuration - main admin work done via mobile app
@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone_number', 'status', 'unique_id', 'created_at']
    list_filter = ['status', 'experience_level', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number', 'unique_id']
    readonly_fields = ['unique_id', 'created_at', 'updated_at', 'approved_at', 'approved_by']
    
    def get_readonly_fields(self, request, obj=None):
        # Make most fields read-only to encourage mobile app usage
        if obj:
            return self.readonly_fields + ['first_name', 'last_name', 'phone_number', 'status']
        return self.readonly_fields

@admin.register(RiderApplication)
class RiderApplicationAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'rider', 'submitted_at', 'reviewed_at']
    list_filter = ['submitted_at', 'reviewed_at']
    search_fields = ['reference_number', 'rider__first_name', 'rider__last_name']
    readonly_fields = ['reference_number', 'submitted_at', 'reviewed_at']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'points_reward', 'created_at']
    list_display_links = ['title']
    list_editable = ['order', 'points_reward']

@admin.register(RiderProgress)
class RiderProgressAdmin(admin.ModelAdmin):
    list_display = ['rider', 'lesson', 'completed', 'completed_at']
    list_filter = ['completed', 'lesson']

@admin.register(Enumerator)
class EnumeratorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'unique_id', 'phone_number', 'gender', 'status', 'location', 'created_at']
    list_filter = ['status', 'gender', 'assigned_region', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number', 'unique_id']
    readonly_fields = ['unique_id', 'created_at', 'updated_at', 'approved_at', 'approved_by']

# Customize admin site headers
admin.site.site_header = "DigitalBoda - Emergency Web Access"
admin.site.site_title = "DigitalBoda Web Admin"
admin.site.index_title = "⚠️ Use DigitalBoda Admin Mobile App for Full Management"
