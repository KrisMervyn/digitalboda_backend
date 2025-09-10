from django.urls import path
from . import views

urlpatterns = [
    # Rider endpoints
    path('register/', views.register_rider, name='register_rider'),
    path('lessons/', views.get_lessons, name='get_lessons'),
    path('profile/<str:phone_number>/', views.rider_profile, name='rider_profile'),
    path('onboarding/submit/', views.submit_onboarding, name='submit_onboarding'),
    
    # Admin endpoints
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/pending-riders/', views.admin_pending_riders, name='admin_pending_riders'),
    path('admin/rider/<int:rider_id>/', views.admin_rider_details, name='admin_rider_details'),
    path('admin/rider/<int:rider_id>/approve/', views.admin_approve_rider, name='admin_approve_rider'),
    path('admin/rider/<int:rider_id>/reject/', views.admin_reject_rider, name='admin_reject_rider'),
    path('admin/dashboard/stats/', views.admin_dashboard_stats, name='admin_dashboard_stats'),
    
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
]