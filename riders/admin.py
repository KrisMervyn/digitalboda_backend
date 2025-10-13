# DigitalBoda Admin - Clean and User-Friendly Interface
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, timedelta
from .models import (
    Rider, RiderApplication, Enumerator, BodaBodaAssociation,
    DigitalLiteracyModule, TrainingSession, SessionSchedule, 
    Stage, StageEnumeratorAssignment, 
    NotificationSchedule, SimpleAttendanceRecord, TrainingInterest
)
from .reports import ReportGenerator

# =============================================================================
# 📊 REPORTING ADMIN ACTIONS
# =============================================================================

def export_attendance_report_excel(modeladmin, request, queryset):
    """Admin action to export attendance report as Excel"""
    generator = ReportGenerator()
    data = generator.generate_attendance_report()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_excel(data, f"attendance_report_{timestamp}", "Attendance Report")

def export_rider_summary_excel(modeladmin, request, queryset):
    """Admin action to export rider summary as Excel"""
    generator = ReportGenerator()
    data = generator.generate_rider_summary_report()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_excel(data, f"rider_summary_{timestamp}", "Rider Summary")

def export_module_completion_excel(modeladmin, request, queryset):
    """Admin action to export module completion report as Excel"""
    generator = ReportGenerator()
    data = generator.generate_module_completion_report()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_excel(data, f"module_completion_{timestamp}", "Module Completion")

# Configure admin actions
export_attendance_report_excel.short_description = "📊 Export Attendance Report (Excel)"
export_rider_summary_excel.short_description = "📊 Export Rider Summary (Excel)"
export_module_completion_excel.short_description = "📊 Export Module Completion Report (Excel)"

# Unregister any existing registrations and unwanted Django built-ins
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token

models_to_unregister = [
    Rider, RiderApplication, Enumerator, BodaBodaAssociation,
    DigitalLiteracyModule, TrainingSession, SessionSchedule, 
    Stage, StageEnumeratorAssignment, NotificationSchedule,
    Group, Token  # Remove irrelevant Django built-ins
]

for model in models_to_unregister:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

# =============================================================================
# 👥 USER MANAGEMENT - Associations, Riders and Field Agents
# =============================================================================

@admin.register(BodaBodaAssociation)
class BodaBodaAssociationAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'contact_person', 'contact_phone', 'riders_count', 'is_active', 'created_at']
    list_display_links = ['name']
    list_filter = ['is_active', 'location', 'created_at']
    search_fields = ['name', 'location', 'contact_person', 'contact_phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Association Information', {
            'fields': ('name', 'description', 'location', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('contact_person', 'contact_phone')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def riders_count(self, obj):
        count = obj.riders.count()
        return format_html(
            '<span style="background: #3498DB; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">🏍️ {}</span>',
            count
        )
    riders_count.short_description = 'Riders'

@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'phone_number', 'status_badge', 
        'points_display', 'unique_id', 'created_at'
    ]
    list_display_links = ['full_name']
    list_filter = ['status', 'experience_level', 'created_at', 'assigned_enumerator']
    search_fields = ['first_name', 'last_name', 'phone_number', 'unique_id']
    readonly_fields = ['unique_id', 'created_at', 'updated_at', 'approved_at', 'approved_by']
    actions = [export_rider_summary_excel]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'age')
        }),
        ('Registration Details', {
            'fields': ('experience_level', 'association', 'status')
        }),
        ('Training Information', {
            'fields': ('points', 'assigned_enumerator'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('unique_id', 'created_at', 'updated_at', 'approved_at', 'approved_by'),
            'classes': ('collapse',)
        }),
        ('Photos', {
            'fields': ('profile_photo', 'national_id_photo'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'PENDING_APPROVAL': '#F39C12',
            'APPROVED': '#27AE60',
            'REJECTED': '#E74C3C',
            'ACTIVE': '#3498DB'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def training_progress(self, obj):
        total_sessions = obj.training_attendance.count()
        completed_sessions = obj.training_attendance.filter(status='ATTENDED').count()
        if total_sessions > 0:
            percentage = int((completed_sessions / total_sessions) * 100)
            return format_html(
                '<div style="width: 100px; background: #eee; border-radius: 10px; overflow: hidden;">'
                '<div style="width: {}%; height: 20px; background: #4CA1AF; text-align: center; line-height: 20px; color: white; font-size: 11px;">{}</div>'
                '</div>',
                percentage, f"{percentage}%"
            )
        return "No sessions"
    training_progress.short_description = 'Progress'
    
    def points_display(self, obj):
        return format_html(
            '<strong style="color: #F39C12;">🏆 {}</strong>',
            obj.points
        )
    points_display.short_description = 'Points'

# Removed from admin interface - RiderApplication no longer visible in sidebar
# @admin.register(RiderApplication)
class RiderApplicationAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'rider', 'submitted_at', 'reviewed_at']
    list_filter = ['submitted_at', 'reviewed_at']
    search_fields = ['reference_number', 'rider__first_name', 'rider__last_name']
    readonly_fields = ['reference_number', 'submitted_at', 'reviewed_at']

# Field Agents (Enumerators)

@admin.register(Enumerator)
class EnumeratorAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'unique_id', 'phone_number', 'gender', 'status_badge', 
        'location', 'assigned_riders_count', 'created_at'
    ]
    list_filter = ['status', 'gender', 'assigned_region', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number', 'unique_id']
    readonly_fields = ['unique_id', 'created_at', 'updated_at', 'approved_at', 'approved_by']
    
    def status_badge(self, obj):
        colors = {
            'PENDING_APPROVAL': '#F39C12',
            'APPROVED': '#27AE60',
            'REJECTED': '#E74C3C',
            'ACTIVE': '#3498DB'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def assigned_riders_count(self, obj):
        count = obj.assigned_riders.count()
        return format_html(
            '<span style="background: #3498DB; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">👥 {}</span>',
            count
        )
    assigned_riders_count.short_description = 'Assigned Riders'

# =============================================================================
# 📚 TRAINING MANAGEMENT - Modules, Sessions, and Attendance
# =============================================================================

@admin.register(DigitalLiteracyModule)
class DigitalLiteracyModuleAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'title', 'session_count', 'total_duration_hours', 
        'points_value', 'icon', 'is_active', 'created_at'
    ]
    list_display_links = ['title']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'created_at', 'total_duration_hours']
    search_fields = ['title', 'description']
    ordering = ['order']

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'module', 'session_number', 'title', 'duration_hours', 
        'points_value'
    ]
    list_display_links = ['title']
    list_filter = ['module', 'duration_hours', 'points_value']
    search_fields = ['title', 'description', 'module__title']
    ordering = ['module__order', 'session_number']
    actions = [export_module_completion_excel]

@admin.register(SessionSchedule)
class SessionScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'trainer', 'scheduled_date', 'location_name',
        'capacity', 'status_badge', 'created_at'
    ]
    list_display_links = ['session']
    list_filter = ['status', 'scheduled_date', 'trainer', 'session__module']
    search_fields = [
        'session__title', 'trainer__first_name', 'trainer__last_name',
        'location_name', 'location_address'
    ]
    date_hierarchy = 'scheduled_date'
    ordering = ['-scheduled_date']
    
    def status_badge(self, obj):
        colors = {
            'SCHEDULED': '#3498DB',
            'ONGOING': '#F39C12',
            'COMPLETED': '#27AE60',
            'CANCELLED': '#E74C3C'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

# =============================================================================
# 📚 SIMPLIFIED TRAINING ADMIN - Module Enrollments & Attendance
# =============================================================================

# ModuleEnrollment has been replaced by TrainingInterest for simplified enrollment

# Temporarily disabled due to database schema issues - use SimpleAttendanceRecord instead
# @admin.register(SessionAttendance)
# class SessionAttendanceAdmin(admin.ModelAdmin):
#     list_display = [
#         'rider', 'session', 'trainer', 'status_badge',
#         'session_date', 'marked_at', 'points_awarded'
#     ]
#     list_display_links = ['rider']
#     list_filter = [
#         'status', 'trainer', 'session__module', 'session_date'
#     ]
#     search_fields = [
#         'rider__first_name', 'rider__last_name', 'rider__phone_number',
#         'session__title', 'trainer__first_name', 'trainer__last_name'
#     ]
#     date_hierarchy = 'session_date'
#     ordering = ['-session_date', '-marked_at']
#     actions = [export_attendance_report_excel]
#     
#     def status_badge(self, obj):
#         colors = {
#             'PRESENT': '#27AE60',
#             'ABSENT': '#E74C3C',
#             'LATE': '#F39C12',
#             'EXCUSED': '#3498DB'
#         }
#         color = colors.get(obj.status, '#95A5A6')
#         return format_html(
#             '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
#             color, obj.get_status_display()
#         )
#     status_badge.short_description = 'Status'

@admin.register(SimpleAttendanceRecord)
class SimpleAttendanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'rider_name', 'session_title', 'trainer_name', 'status_badge',
        'session_date', 'points_awarded', 'recorded_at'
    ]
    list_display_links = ['rider_name']
    list_filter = [
        'status', 'trainer', 'session__module', 'session_date'
    ]
    search_fields = [
        'rider__first_name', 'rider__last_name', 'rider__phone_number',
        'session__title', 'trainer__first_name', 'trainer__last_name'
    ]
    date_hierarchy = 'session_date'
    ordering = ['-session_date', '-recorded_at']
    readonly_fields = ['recorded_at']
    
    def rider_name(self, obj):
        return f"{obj.rider.first_name} {obj.rider.last_name}"
    rider_name.short_description = 'Rider'
    rider_name.admin_order_field = 'rider__first_name'
    
    def session_title(self, obj):
        return f"{obj.session.module.title}: {obj.session.title}"
    session_title.short_description = 'Session'
    session_title.admin_order_field = 'session__title'
    
    def trainer_name(self, obj):
        return f"{obj.trainer.first_name} {obj.trainer.last_name}"
    trainer_name.short_description = 'Trainer'
    trainer_name.admin_order_field = 'trainer__first_name'
    
    def status_badge(self, obj):
        colors = {
            'ATTENDED': '#27AE60',
            'ABSENT': '#E74C3C',
            'LATE': '#F39C12',
            'EXCUSED': '#3498DB'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

@admin.register(TrainingInterest)
class TrainingInterestAdmin(admin.ModelAdmin):
    list_display = [
        'rider_name', 'module_title', 'trainer_name', 'expressed_at', 'is_active'
    ]
    list_filter = ['is_active', 'trainer', 'module', 'expressed_at']
    search_fields = [
        'rider__first_name', 'rider__last_name', 'rider__phone_number',
        'module__title', 'trainer__first_name', 'trainer__last_name'
    ]
    date_hierarchy = 'expressed_at'
    ordering = ['-expressed_at']
    
    def rider_name(self, obj):
        return f"{obj.rider.first_name} {obj.rider.last_name}"
    rider_name.short_description = 'Rider'
    rider_name.admin_order_field = 'rider__first_name'
    
    def module_title(self, obj):
        return obj.module.title
    module_title.short_description = 'Module'
    module_title.admin_order_field = 'module__title'
    
    def trainer_name(self, obj):
        return f"{obj.trainer.first_name} {obj.trainer.last_name}"
    trainer_name.short_description = 'Trainer'
    trainer_name.admin_order_field = 'trainer__first_name'

# =============================================================================
# 🏍️ STAGE MANAGEMENT - Boda Boda Stages and Assignments
# =============================================================================

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = [
        'stage_id', 'name', 'district', 'status_badge', 
        'capacity', 'enumerator_count', 'created_at'
    ]
    list_filter = ['status', 'district', 'division', 'created_at']
    search_fields = ['stage_id', 'name', 'address', 'district']
    ordering = ['stage_id']
    
    def status_badge(self, obj):
        colors = {
            'ACTIVE': '#27AE60',
            'INACTIVE': '#E74C3C',
            'MAINTENANCE': '#F39C12'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def enumerator_count(self, obj):
        count = obj.enumerator_assignments.count()
        return format_html(
            '<span style="background: #3498DB; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">👤 {}</span>',
            count
        )
    enumerator_count.short_description = 'Field Agents'

@admin.register(StageEnumeratorAssignment)
class StageEnumeratorAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'enumerator', 'stage', 'is_primary', 'status_badge', 'assigned_date'
    ]
    list_filter = ['is_primary', 'status', 'assigned_date', 'stage__district']
    search_fields = ['enumerator__first_name', 'enumerator__last_name', 'stage__name', 'stage__stage_id']
    date_hierarchy = 'assigned_date'
    
    def status_badge(self, obj):
        colors = {
            'ACTIVE': '#27AE60',
            'INACTIVE': '#E74C3C'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

# =============================================================================
# 📱 COMMUNICATION - Notifications and Alerts
# =============================================================================

# Removed from admin interface - NotificationSchedule no longer visible in sidebar
# @admin.register(NotificationSchedule)
class NotificationScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'rider', 'notification_type_badge', 'title', 'scheduled_time', 
        'status_badge', 'attempt_count', 'sent_time'
    ]
    list_filter = [
        'status', 'notification_type', 'scheduled_time', 'created_at',
        'session_schedule__session__module'
    ]
    search_fields = [
        'rider__first_name', 'rider__last_name', 'title', 'message'
    ]
    date_hierarchy = 'scheduled_time'
    ordering = ['-scheduled_time']
    
    def notification_type_badge(self, obj):
        colors = {
            'REMINDER': '#F39C12',
            'ALERT': '#E74C3C',
            'UPDATE': '#3498DB',
            'TRAINING': '#27AE60'
        }
        color = colors.get(obj.notification_type, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.notification_type
        )
    notification_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#F39C12',
            'SENT': '#27AE60',
            'FAILED': '#E74C3C'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

# =============================================================================
# DASHBOARD DATA AND ADMIN CUSTOMIZATION
# =============================================================================

from django.contrib.admin import AdminSite
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta

class CustomAdminSite(AdminSite):
    site_header = "DigitalBoda Admin"
    site_title = "DigitalBoda"
    index_title = "Dashboard"
    
    def index(self, request, extra_context=None):
        """
        Display the main admin index page with real dashboard data.
        """
        extra_context = extra_context or {}
        
        # Get dashboard statistics from database
        try:
            # Total riders count
            total_riders = Rider.objects.count()
            
            # Total training sessions
            total_sessions = TrainingSession.objects.count()
            
            # Attendance rate calculation
            total_attendance_records = SimpleAttendanceRecord.objects.count()
            attended_records = SimpleAttendanceRecord.objects.filter(status='ATTENDED').count()
            attendance_rate = round((attended_records / total_attendance_records * 100), 1) if total_attendance_records > 0 else 0
            
            # Active stages count
            active_stages = Stage.objects.filter(status='ACTIVE').count()
            
            # Recent registrations (last 5 riders)
            recent_riders = Rider.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).order_by('-created_at')[:5]
            
            # Upcoming sessions (next 5 scheduled sessions)
            upcoming_sessions = SessionSchedule.objects.filter(
                status='SCHEDULED',
                scheduled_date__gte=timezone.now()
            ).select_related('session', 'trainer').order_by('scheduled_date')[:5]
            
            # Weekly attendance data for chart
            weekly_attendance = []
            for i in range(7):
                date = timezone.now().date() - timedelta(days=6-i)
                day_attendance = SimpleAttendanceRecord.objects.filter(
                    session_date=date,
                    status='ATTENDED'
                ).count()
                total_day_sessions = SimpleAttendanceRecord.objects.filter(
                    session_date=date
                ).count()
                rate = round((day_attendance / total_day_sessions * 100), 1) if total_day_sessions > 0 else 0
                weekly_attendance.append(rate)
            
            # Module progress data
            module_progress = DigitalLiteracyModule.objects.annotate(
                completed_count=Count('sessions__simple_attendance_records', filter=Q(sessions__simple_attendance_records__status='ATTENDED'))
            ).values('title', 'completed_count')[:4]
            
            # Pending riders count
            pending_riders = Rider.objects.filter(status='PENDING_APPROVAL').count()
            
            # Recent activity data
            recent_activities = []
            for rider in recent_riders:
                time_diff = timezone.now() - rider.created_at
                if time_diff.days == 0:
                    if time_diff.seconds < 3600:
                        time_ago = f"{time_diff.seconds // 60} minutes ago"
                    else:
                        time_ago = f"{time_diff.seconds // 3600} hours ago"
                else:
                    time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                
                recent_activities.append({
                    'rider': rider,
                    'time_ago': time_ago
                })
            
            # Update extra_context with real data
            extra_context.update({
                'total_riders': total_riders,
                'total_sessions': total_sessions,
                'attendance_rate': attendance_rate,
                'active_stages': active_stages,
                'recent_riders': recent_activities,
                'upcoming_sessions': upcoming_sessions,
                'pending_riders': pending_riders,
                'weekly_attendance': weekly_attendance,
                'module_progress': list(module_progress),
                'current_time': timezone.now(),
            })
            
        except Exception as e:
            # Fallback to default values if database queries fail
            extra_context.update({
                'total_riders': 0,
                'total_sessions': 0,
                'attendance_rate': 0,
                'active_stages': 0,
                'recent_riders': [],
                'upcoming_sessions': [],
                'pending_riders': 0,
                'weekly_attendance': [0, 0, 0, 0, 0, 0, 0],
                'module_progress': [],
                'error_message': f"Dashboard data loading error: {str(e)}",
            })
        
        return super().index(request, extra_context)

# Create custom admin site instance
admin_site = CustomAdminSite(name='custom_admin')

# Re-register all models with custom admin site (excluding NotificationSchedule and RiderApplication)
admin_site.register(Rider, RiderAdmin)
# admin_site.register(RiderApplication, RiderApplicationAdmin)  # Removed from sidebar
admin_site.register(Enumerator, EnumeratorAdmin)
admin_site.register(BodaBodaAssociation, BodaBodaAssociationAdmin)
admin_site.register(DigitalLiteracyModule, DigitalLiteracyModuleAdmin)
admin_site.register(TrainingSession, TrainingSessionAdmin)
admin_site.register(SessionSchedule, SessionScheduleAdmin)
# admin_site.register(ModuleEnrollment, ModuleEnrollmentAdmin)  # Replaced by TrainingInterest
# admin_site.register(SessionAttendance, SessionAttendanceAdmin)  # Disabled due to database schema issues
admin_site.register(Stage, StageAdmin)
admin_site.register(StageEnumeratorAssignment, StageEnumeratorAssignmentAdmin)
# admin_site.register(NotificationSchedule, NotificationScheduleAdmin)  # Removed from sidebar

# Customize admin site headers and titles
admin.site.site_header = "DigitalBoda Admin"
admin.site.site_title = "DigitalBoda"
admin.site.index_title = "Dashboard"