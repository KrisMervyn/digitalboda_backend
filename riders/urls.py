from django.urls import path
from . import views
from . import authentication
from . import photo_views

urlpatterns = [
    # Authentication endpoints
    path('auth/rider/login/', authentication.rider_login, name='rider_login'),
    path('auth/enumerator/login/', authentication.enumerator_login, name='enumerator_login'),
    path('auth/admin/login/', authentication.admin_login, name='admin_login'),
    path('auth/logout/', authentication.logout, name='logout'),
    path('auth/verify-token/', authentication.verify_token, name='verify_token'),
    
    # Rider endpoints
    path('register/', views.register_rider, name='register_rider'),
    path('lessons/', views.get_lessons, name='get_lessons'),
    path('profile/<str:phone_number>/', views.rider_profile, name='rider_profile'),
    path('onboarding/submit/', views.submit_onboarding, name='submit_onboarding'),
    
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
]