# DigitalBoda Admin - User-Friendly Configuration
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from .models import (
    Rider, RiderApplication, Enumerator,
    DigitalLiteracyModule, TrainingSession, SessionSchedule, 
    SessionAttendance, Stage, StageEnumeratorAssignment, NotificationSchedule
)


class DigitalBodaAdminSite(AdminSite):
    """Custom admin site with organized sections"""
    site_header = "DigitalBoda Admin"
    site_title = "DigitalBoda"
    index_title = "Platform Dashboard"
    
    def get_app_list(self, request, app_label=None):
        """Return a custom app list with organized sections"""
        app_list = super().get_app_list(request, app_label)
        
        # Define custom groupings
        custom_app_list = [
            {
                'name': 'User Management',
                'app_label': 'user_management',
                'models': [
                    {
                        'name': 'Boda Boda Riders',
                        'object_name': 'Rider',
                        'admin_url': '/admin/riders/rider/',
                        'add_url': '/admin/riders/rider/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'Field Agents',
                        'object_name': 'Enumerator',
                        'admin_url': '/admin/riders/enumerator/',
                        'add_url': '/admin/riders/enumerator/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'Rider Applications',
                        'object_name': 'RiderApplication',
                        'admin_url': '/admin/riders/riderapplication/',
                        'add_url': '/admin/riders/riderapplication/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    }
                ]
            },
            {
                'name': 'Training Management',
                'app_label': 'training_management',
                'models': [
                    {
                        'name': 'Training Modules',
                        'object_name': 'DigitalLiteracyModule',
                        'admin_url': '/admin/riders/digitalliteracymodule/',
                        'add_url': '/admin/riders/digitalliteracymodule/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'Training Sessions',
                        'object_name': 'TrainingSession',
                        'admin_url': '/admin/riders/trainingsession/',
                        'add_url': '/admin/riders/trainingsession/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'Session Schedules',
                        'object_name': 'SessionSchedule',
                        'admin_url': '/admin/riders/sessionschedule/',
                        'add_url': '/admin/riders/sessionschedule/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'Session Attendance',
                        'object_name': 'SessionAttendance',
                        'admin_url': '/admin/riders/sessionattendance/',
                        'add_url': '/admin/riders/sessionattendance/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    }
                ]
            },
            {
                'name': 'Stage Management',
                'app_label': 'stage_management',
                'models': [
                    {
                        'name': 'Boda Boda Stages',
                        'object_name': 'Stage',
                        'admin_url': '/admin/riders/stage/',
                        'add_url': '/admin/riders/stage/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'Field Agent Assignments',
                        'object_name': 'StageEnumeratorAssignment',
                        'admin_url': '/admin/riders/stageenumeratorassignment/',
                        'add_url': '/admin/riders/stageenumeratorassignment/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    }
                ]
            },
            {
                'name': 'System Management',
                'app_label': 'system_management',
                'models': [
                    {
                        'name': 'Notifications',
                        'object_name': 'NotificationSchedule',
                        'admin_url': '/admin/riders/notificationschedule/',
                        'add_url': '/admin/riders/notificationschedule/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'User Accounts',
                        'object_name': 'User',
                        'admin_url': '/admin/auth/user/',
                        'add_url': '/admin/auth/user/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    },
                    {
                        'name': 'API Tokens',
                        'object_name': 'Token',
                        'admin_url': '/admin/authtoken/token/',
                        'add_url': '/admin/authtoken/token/add/',
                        'perms': {'add': True, 'change': True, 'delete': True, 'view': True}
                    }
                ]
            }
        ]
        
        return custom_app_list


# Create custom admin site instance
admin_site = DigitalBodaAdminSite(name='digitalboda_admin')

# Register models with custom admin site
from .admin import (
    RiderAdmin, EnumeratorAdmin, RiderApplicationAdmin,
    DigitalLiteracyModuleAdmin, TrainingSessionAdmin,
    SessionScheduleAdmin, SessionAttendanceAdmin, StageAdmin,
    StageEnumeratorAssignmentAdmin, NotificationScheduleAdmin
)

admin_site.register(Rider, RiderAdmin)
admin_site.register(Enumerator, EnumeratorAdmin)
admin_site.register(RiderApplication, RiderApplicationAdmin)
admin_site.register(DigitalLiteracyModule, DigitalLiteracyModuleAdmin)
admin_site.register(TrainingSession, TrainingSessionAdmin)
admin_site.register(SessionSchedule, SessionScheduleAdmin)
admin_site.register(SessionAttendance, SessionAttendanceAdmin)
admin_site.register(Stage, StageAdmin)
admin_site.register(StageEnumeratorAssignment, StageEnumeratorAssignmentAdmin)
admin_site.register(NotificationSchedule, NotificationScheduleAdmin)

# Register auth models
from django.contrib.auth.admin import UserAdmin, GroupAdmin
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)

# Register token model
from rest_framework.authtoken.admin import TokenAdmin
admin_site.register(Token, TokenAdmin)