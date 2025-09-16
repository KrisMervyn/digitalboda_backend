from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Rider, TrainingSession, SessionAttendance, Stage, 
    DigitalLiteracyModule, SessionSchedule
)

def dashboard_data(request):
    """
    Context processor to add dashboard data to all templates.
    """
    print(f"DEBUG: Context processor called for path: {request.path}")
    
    # Only add dashboard data to admin pages
    if not request.path.startswith('/admin/'):
        return {}
    
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
        
        # Module progress data - simplified to avoid complex joins
        module_progress = DigitalLiteracyModule.objects.values('title').annotate(
            completed_count=Count('sessions')
        )[:4]
        
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
        
        context_data = {
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
        print(f"DEBUG: Returning context data: {context_data}")
        return context_data
        
    except Exception as e:
        # Fallback to default values if database queries fail
        return {
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
        }