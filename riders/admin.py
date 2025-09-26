# Django Admin - Organized Digital Literacy Training Management
from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render
from django.http import HttpResponse
from .models import (
    
    Rider, RiderApplication, Lesson, RiderProgress, Enumerator,
    DigitalLiteracyModule, TrainingSession, SessionSchedule, 
    SessionAttendance, Stage, StageRiderAssignment, NotificationSchedule
)

# Unregister any existing registrations
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

# =============================================================================
# RIDER ADMIN - All rider functionality grouped together
# =============================================================================

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
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'age')
        }),
        ('Registration Details', {
            'fields': ('experience_level', 'location', 'national_id_number', 'status')
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

# =============================================================================
# ENUMERATOR ADMIN - All enumerator functionality grouped together
# =============================================================================

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
# SESSION ADMIN - All training session functionality grouped together
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

@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'rider', 'session_info', 'trainer', 'status_badge',
        'registration_time', 'check_in_time'
    ]
    list_display_links = ['rider']
    list_filter = [
        'status', 'schedule__status', 'schedule__trainer',
        'schedule__session__module', 'registration_time'
    ]
    search_fields = [
        'rider__first_name', 'rider__last_name', 'rider__phone_number',
        'schedule__session__title', 'schedule__location_name'
    ]
    date_hierarchy = 'registration_time'
    ordering = ['-registration_time']
    
    def session_info(self, obj):
        return f"{obj.schedule.session.module.title} - {obj.schedule.session.title}"
    session_info.short_description = "Session"
    
    def trainer(self, obj):
        return obj.schedule.trainer.full_name
    trainer.short_description = "Trainer"
    
    def status_badge(self, obj):
        colors = {
            'REGISTERED': '#3498DB',
            'ATTENDED': '#27AE60',
            'NO_SHOW': '#E74C3C',
            'LATE': '#F39C12'
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

# =============================================================================
# STAGE ADMIN - All stage functionality grouped together
# =============================================================================

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = [
        'stage_id', 'name', 'district', 'status_badge', 
        'capacity', 'rider_count', 'created_at'
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
    
    def rider_count(self, obj):
        count = obj.rider_assignments.count()
        return format_html(
            '<span style="background: #3498DB; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">👥 {}</span>',
            count
        )
    rider_count.short_description = 'Riders'

@admin.register(StageRiderAssignment)
class StageRiderAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'rider', 'stage', 'is_primary', 'status_badge', 'assigned_date'
    ]
    list_filter = ['is_primary', 'status', 'assigned_date', 'stage__district']
    search_fields = ['rider__first_name', 'rider__last_name', 'stage__name', 'stage__stage_id']
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
# NOTIFICATION ADMIN - All notification functionality grouped together  
# =============================================================================

@admin.register(NotificationSchedule)
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
# CUSTOM ADMIN SITE WITH DASHBOARD DATA
# =============================================================================

from django.contrib.admin import AdminSite
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta

class CustomAdminSite(AdminSite):
    site_header = "DigitalBoda - Training Management Admin"
    site_title = "DigitalBoda Admin"
    index_title = "Digital Literacy Training Management System"
    
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
            total_attendance_records = SessionAttendance.objects.count()
            attended_records = SessionAttendance.objects.filter(status='ATTENDED').count()
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
                day_attendance = SessionAttendance.objects.filter(
                    registration_time__date=date,
                    status='ATTENDED'
                ).count()
                total_day_sessions = SessionAttendance.objects.filter(
                    registration_time__date=date
                ).count()
                rate = round((day_attendance / total_day_sessions * 100), 1) if total_day_sessions > 0 else 0
                weekly_attendance.append(rate)
            
            # Module progress data
            module_progress = DigitalLiteracyModule.objects.annotate(
                completed_count=Count('sessions__attendance_records', filter=Q(sessions__attendance_records__status='ATTENDED'))
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

# Re-register all models with custom admin site
admin_site.register(Rider, RiderAdmin)
admin_site.register(RiderApplication, RiderApplicationAdmin)
admin_site.register(Lesson, LessonAdmin)
admin_site.register(RiderProgress, RiderProgressAdmin)
admin_site.register(Enumerator, EnumeratorAdmin)
admin_site.register(DigitalLiteracyModule, DigitalLiteracyModuleAdmin)
admin_site.register(TrainingSession, TrainingSessionAdmin)
admin_site.register(SessionSchedule, SessionScheduleAdmin)
admin_site.register(SessionAttendance, SessionAttendanceAdmin)
admin_site.register(Stage, StageAdmin)
admin_site.register(StageRiderAssignment, StageRiderAssignmentAdmin)
admin_site.register(NotificationSchedule, NotificationScheduleAdmin)

# Override the default admin site's index method to include dashboard data
def custom_admin_index(request, extra_context=None):
    """
    Custom admin index view with real dashboard data.
    """
    print(f"DEBUG: Custom admin index called for path: {request.path}")
    extra_context = extra_context or {}
    
    # Get dashboard statistics from database
    try:
        # Total riders count
        total_riders = Rider.objects.count()
        
        # Total training sessions
        total_sessions = TrainingSession.objects.count()
        
        # Attendance rate calculation
        total_attendance_records = SessionAttendance.objects.count()
        attended_records = SessionAttendance.objects.filter(status='ATTENDED').count()
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
            day_attendance = SessionAttendance.objects.filter(
                registration_time__date=date,
                status='ATTENDED'
            ).count()
            total_day_sessions = SessionAttendance.objects.filter(
                registration_time__date=date
            ).count()
            rate = round((day_attendance / total_day_sessions * 100), 1) if total_day_sessions > 0 else 0
            weekly_attendance.append(rate)
        
        # Module progress data
        module_progress = DigitalLiteracyModule.objects.annotate(
            completed_count=Count('sessions__attendance_records', filter=Q(sessions__attendance_records__status='ATTENDED'))
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
        dashboard_data = {
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
        }
        
        print(f"DEBUG: Injecting dashboard data: {dashboard_data}")
        extra_context.update(dashboard_data)
        
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
    
    # Call the original admin index view
    from django.contrib.admin.sites import AdminSite
    return AdminSite.index(admin.site, request, extra_context)

# Override the admin site's index method
admin.site.index = custom_admin_index

# Customize admin site headers
admin.site.site_header = "DigitalBoda - Training Management Admin"
admin.site.site_title = "DigitalBoda Admin"
admin.site.index_title = "Digital Literacy Training Management System"