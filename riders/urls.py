from django.urls import path
from . import views
from . import authentication
from . import photo_views
from . import report_views
from . import simple_training_views

urlpatterns = [
    # Authentication endpoints
    path('auth/rider/login/', authentication.rider_login, name='rider_login'),
    path('auth/enumerator/login/', authentication.enumerator_login, name='enumerator_login'),
    path('auth/admin/login/', authentication.admin_login, name='admin_login'),
    path('auth/logout/', authentication.logout, name='logout'),
    path('auth/verify-token/', authentication.verify_token, name='verify_token'),
    
    # PIN Management endpoints
    path('auth/pin/setup/', authentication.setup_pin, name='setup_pin'),
    path('auth/pin/change/', authentication.change_pin, name='change_pin'),
    path('auth/pin/status/', authentication.pin_status, name='pin_status'),
    
    # Rider endpoints
    path('register/', views.register_rider, name='register_rider'),
    path('lessons/', views.get_lessons, name='get_lessons'),
    path('profile/<str:phone_number>/', views.rider_profile, name='rider_profile'),
    path('onboarding/submit/', views.submit_onboarding, name='submit_onboarding'),
    path('associations/', views.get_associations, name='get_associations'),
    
    # Admin endpoints
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/pending-riders/', views.admin_pending_riders, name='admin_pending_riders'),
    path('admin/pending-riders-by-enumerator/', views.admin_pending_riders_by_enumerator, name='admin_pending_riders_by_enumerator'),
    path('admin/rider/<int:rider_id>/', views.admin_rider_details, name='admin_rider_details'),
    path('admin/rider/<int:rider_id>/approve/', views.admin_approve_rider, name='admin_approve_rider'),
    path('admin/rider/<int:rider_id>/reject/', views.admin_reject_rider, name='admin_reject_rider'),
    path('admin/dashboard/stats/', views.admin_dashboard_stats, name='admin_dashboard_stats'),
    
    # Admin Enumerator Management endpoints
    path('admin/enumerators/', views.admin_enumerators_list, name='admin_enumerators_list'),
    path('admin/enumerator/create/', views.admin_create_enumerator, name='admin_create_enumerator'),
    path('admin/enumerators/search/', views.admin_search_enumerators, name='admin_search_enumerators'),
    path('admin/enumerator/<str:enumerator_id>/', views.admin_enumerator_details, name='admin_enumerator_details'),
    path('admin/enumerator/<str:enumerator_id>/update/', views.admin_update_enumerator, name='admin_update_enumerator'),
    path('admin/enumerator/<str:enumerator_id>/delete/', views.admin_delete_enumerator, name='admin_delete_enumerator'),
    
    # Enumerator endpoints
    path('enumerator/login/', views.enumerator_login, name='enumerator_login'),
    path('enumerator/assigned-riders/', views.enumerator_assigned_riders, name='enumerator_assigned_riders'),
    path('enumerator/pending-riders/', views.enumerator_pending_riders, name='enumerator_pending_riders'),
    path('enumerator/rider/<int:rider_id>/approve/', views.enumerator_approve_rider, name='enumerator_approve_rider'),
    path('enumerator/rider/<int:rider_id>/reject/', views.enumerator_reject_rider, name='enumerator_reject_rider'),
    path('enumerator/dashboard/stats/', views.enumerator_dashboard_stats, name='enumerator_dashboard_stats'),
    path('enumerator/change-password/', views.enumerator_change_password, name='enumerator_change_password'),
    
    # FCM/Push Notification endpoints
    path('fcm/update-token/', views.update_fcm_token, name='update_fcm_token'),
    path('riders/<int:rider_id>/approve/', views.approve_rider, name='approve_rider'),
    path('riders/<int:rider_id>/reject/', views.reject_rider, name='reject_rider'),
    
    # Photo Verification endpoints
    path('riders/<int:rider_id>/verify-photos/', photo_views.verify_rider_photos, name='verify_rider_photos'),
    path('riders/<int:rider_id>/photo-verification-report/', photo_views.get_photo_verification_report, name='photo_verification_report'),
    path('riders/<int:rider_id>/approve-photos/', photo_views.approve_photo_verification, name='approve_photo_verification'),
    path('enumerator/pending-photo-verification/', photo_views.get_riders_pending_photo_verification, name='pending_photo_verification'),
    path('admin/photo-verification-stats/', photo_views.photo_verification_statistics, name='photo_verification_stats'),
    
    # Digital Literacy Training endpoints (Original Complex System)
    path('digital-literacy/modules/', views.digital_literacy_modules, name='digital_literacy_modules'),
    path('digital-literacy/upcoming-sessions/', views.upcoming_training_sessions, name='upcoming_training_sessions'),
    path('digital-literacy/register-attendance/', views.register_attendance, name='register_attendance'),
    path('digital-literacy/rider-progress/', views.rider_digital_literacy_progress, name='rider_digital_literacy_progress'),
    path('digital-literacy/leaderboard/', views.digital_literacy_leaderboard, name='digital_literacy_leaderboard'),
    path('digital-literacy/achievements/', views.digital_literacy_achievements, name='digital_literacy_achievements'),
    path('digital-literacy/achievement-stats/', views.digital_literacy_achievement_stats, name='digital_literacy_achievement_stats'),
    path('digital-literacy/notifications/', views.digital_literacy_notifications, name='digital_literacy_notifications'),
    path('digital-literacy/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('digital-literacy/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('digital-literacy/certificates/', views.digital_literacy_certificates, name='digital_literacy_certificates'),
    path('digital-literacy/badges/', views.digital_literacy_badges, name='digital_literacy_badges'),
    path('digital-literacy/verify-stage/', views.verify_stage_id, name='verify_stage_id'),
    path('digital-literacy/register-session/', views.register_for_session, name='register_for_session'),
    path('digital-literacy/session-status/<int:schedule_id>/', views.get_session_status, name='get_session_status'),
    path('digital-literacy/check-attendance-window/', views.check_attendance_window, name='check_attendance_window'),
    
    # Simplified Training System endpoints (New Trainer-Managed System)
    path('training/modules/', simple_training_views.get_available_modules, name='simple_get_modules'),
    path('training/enroll/', simple_training_views.simple_enroll_in_module, name='simple_enroll'),
    path('training/progress/', simple_training_views.get_rider_training_progress, name='simple_progress'),
    path('training/trainer/students/', simple_training_views.get_trainer_students, name='trainer_students'),
    path('training/trainer/mark-attendance/', simple_training_views.mark_student_attendance, name='mark_attendance'),
    path('training/trainer/daily-stats/', simple_training_views.get_daily_attendance_stats, name='daily_attendance_stats'),
    path('training/trainer/session-details/', simple_training_views.get_session_attendance_details, name='session_attendance_details'),
    path('training/trainer/attendance-history/', simple_training_views.get_attendance_history, name='attendance_history'),
    
    # Reporting Dashboard and API endpoints
    path('reports/dashboard/', report_views.reports_dashboard, name='reports_dashboard'),
    path('reports/filters/', report_views.get_available_filters, name='report_filters'),
    path('reports/preview/', report_views.preview_report_data, name='report_preview'),
    path('reports/statistics/', report_views.get_report_statistics, name='report_statistics'),
    path('reports/schedule/', report_views.schedule_automated_report, name='schedule_automated_report'),
    
    # CSV Export endpoints
    path('reports/export/attendance/csv/', report_views.export_attendance_csv, name='export_attendance_csv'),
    path('reports/export/rider-summary/csv/', report_views.export_rider_summary_csv, name='export_rider_summary_csv'),
    path('reports/export/module-completion/csv/', report_views.export_module_completion_csv, name='export_module_completion_csv'),
    path('reports/export/geographical/csv/', report_views.export_geographical_csv, name='export_geographical_csv'),
    
    # Excel Export endpoints
    path('reports/export/attendance/excel/', report_views.export_attendance_excel, name='export_attendance_excel'),
    path('reports/export/rider-summary/excel/', report_views.export_rider_summary_excel, name='export_rider_summary_excel'),
    path('reports/export/module-completion/excel/', report_views.export_module_completion_excel, name='export_module_completion_excel'),
    path('reports/export/geographical/excel/', report_views.export_geographical_excel, name='export_geographical_excel'),
]