# DigitalBoda Reporting API Views
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from .reports import (
    ReportGenerator,
    generate_attendance_csv, generate_attendance_excel,
    generate_rider_summary_csv, generate_rider_summary_excel,
    generate_module_completion_csv, generate_module_completion_excel,
    generate_geographical_csv, generate_geographical_excel
)
from .models import DigitalLiteracyModule, TrainingSession


def parse_filters_from_request(request):
    """Parse and validate filters from request parameters"""
    filters = {}
    
    # Date filtering
    if request.GET.get('start_date'):
        try:
            filters['start_date'] = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            filters['end_date'] = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Session and module filtering
    if request.GET.get('session_id'):
        try:
            filters['session_id'] = int(request.GET['session_id'])
        except ValueError:
            pass
    
    if request.GET.get('module_id'):
        try:
            filters['module_id'] = int(request.GET['module_id'])
        except ValueError:
            pass
    
    # Location filtering
    if request.GET.get('district'):
        filters['district'] = request.GET['district'].strip()
    
    # Gender filtering
    if request.GET.get('gender') in ['M', 'F', 'O']:
        filters['gender'] = request.GET['gender']
    
    # Age group filtering
    if request.GET.get('age_group'):
        valid_age_groups = ['18-25', '26-35', '36-45', '46-55', '56-65', '66+']
        if request.GET['age_group'] in valid_age_groups:
            filters['age_group'] = request.GET['age_group']
    
    # Status filtering
    if request.GET.get('status'):
        valid_statuses = ['REGISTERED', 'ATTENDED', 'NO_SHOW', 'LATE']
        if request.GET['status'] in valid_statuses:
            filters['status'] = request.GET['status']
    
    return filters


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_filters(request):
    """Get available filter options for report generation"""
    try:
        # Get available modules and sessions
        modules = list(DigitalLiteracyModule.objects.filter(is_active=True).values('id', 'title'))
        sessions = list(TrainingSession.objects.select_related('module').values(
            'id', 'title', 'module__title', 'module_id'
        ))
        
        # Get available age groups
        age_groups = [
            {'value': '18-25', 'label': '18-25 years'},
            {'value': '26-35', 'label': '26-35 years'},
            {'value': '36-45', 'label': '36-45 years'},
            {'value': '46-55', 'label': '46-55 years'},
            {'value': '56-65', 'label': '56-65 years'},
            {'value': '66+', 'label': '66+ years'},
        ]
        
        # Get available genders
        genders = [
            {'value': 'M', 'label': 'Male'},
            {'value': 'F', 'label': 'Female'},
            {'value': 'O', 'label': 'Other'},
        ]
        
        # Get available statuses
        statuses = [
            {'value': 'REGISTERED', 'label': 'Registered'},
            {'value': 'ATTENDED', 'label': 'Attended'},
            {'value': 'NO_SHOW', 'label': 'No Show'},
            {'value': 'LATE', 'label': 'Late'},
        ]
        
        return Response({
            'modules': modules,
            'sessions': sessions,
            'age_groups': age_groups,
            'genders': genders,
            'statuses': statuses,
            'date_format': 'YYYY-MM-DD'
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to get filter options: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def preview_report_data(request):
    """Preview report data with current filters (first 10 rows)"""
    try:
        report_type = request.GET.get('report_type', 'attendance')
        filters = parse_filters_from_request(request)
        
        generator = ReportGenerator()
        
        if report_type == 'attendance':
            data = generator.generate_attendance_report(**filters)
        elif report_type == 'rider_summary':
            data = generator.generate_rider_summary_report(**filters)
        elif report_type == 'module_completion':
            data = generator.generate_module_completion_report(**filters)
        elif report_type == 'geographical':
            data = generator.generate_geographical_report(**filters)
        else:
            return Response(
                {'error': 'Invalid report type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return first 10 rows for preview
        preview_data = data[:10] if data else []
        
        return Response({
            'report_type': report_type,
            'total_records': len(data),
            'preview_records': len(preview_data),
            'applied_filters': filters,
            'data': preview_data
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to generate preview: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# CSV Export Views
@login_required
def export_attendance_csv(request):
    """Export attendance report as CSV"""
    filters = parse_filters_from_request(request)
    return generate_attendance_csv(request, **filters)


@login_required
def export_rider_summary_csv(request):
    """Export rider summary report as CSV"""
    filters = parse_filters_from_request(request)
    return generate_rider_summary_csv(request, **filters)


@login_required
def export_module_completion_csv(request):
    """Export module completion report as CSV"""
    filters = parse_filters_from_request(request)
    return generate_module_completion_csv(request, **filters)


@login_required
def export_geographical_csv(request):
    """Export geographical report as CSV"""
    filters = parse_filters_from_request(request)
    return generate_geographical_csv(request, **filters)


# Excel Export Views
@login_required
def export_attendance_excel(request):
    """Export attendance report as Excel"""
    filters = parse_filters_from_request(request)
    return generate_attendance_excel(request, **filters)


@login_required
def export_rider_summary_excel(request):
    """Export rider summary report as Excel"""
    filters = parse_filters_from_request(request)
    return generate_rider_summary_excel(request, **filters)


@login_required
def export_module_completion_excel(request):
    """Export module completion report as Excel"""
    filters = parse_filters_from_request(request)
    return generate_module_completion_excel(request, **filters)


@login_required
def export_geographical_excel(request):
    """Export geographical report as Excel"""
    filters = parse_filters_from_request(request)
    return generate_geographical_excel(request, **filters)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_report_statistics(request):
    """Get summary statistics for dashboard"""
    try:
        filters = parse_filters_from_request(request)
        generator = ReportGenerator()
        
        # Generate basic statistics
        attendance_data = generator.generate_attendance_report(**filters)
        rider_data = generator.generate_rider_summary_report(**filters)
        geographical_data = generator.generate_geographical_report(**filters)
        
        # Calculate summary stats
        total_sessions = len(attendance_data)
        total_riders = len(rider_data)
        total_locations = len(geographical_data)
        
        # Attendance stats
        attended_sessions = len([a for a in attendance_data if a['Status'] == 'Attended'])
        overall_attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Gender breakdown
        male_participants = len([a for a in attendance_data if a['Gender'] == 'M'])
        female_participants = len([a for a in attendance_data if a['Gender'] == 'F'])
        
        # Age group breakdown
        age_groups = {}
        for rider in rider_data:
            age_group = rider.get('Age Group', 'Unknown')
            age_groups[age_group] = age_groups.get(age_group, 0) + 1
        
        # Top performing locations
        top_locations = sorted(
            geographical_data, 
            key=lambda x: x['Attendance Rate (%)'], 
            reverse=True
        )[:5]
        
        return Response({
            'summary': {
                'total_sessions': total_sessions,
                'total_riders': total_riders,
                'total_locations': total_locations,
                'overall_attendance_rate': round(overall_attendance_rate, 2),
                'male_participants': male_participants,
                'female_participants': female_participants,
            },
            'age_group_breakdown': age_groups,
            'top_performing_locations': top_locations,
            'applied_filters': filters,
            'generated_at': timezone.now().isoformat()
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to generate statistics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_automated_report(request):
    """Schedule automated report generation (placeholder for future implementation)"""
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['report_type', 'frequency', 'recipients']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Missing required field: {field}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # For now, just return success with planned implementation
        return Response({
            'message': 'Automated report scheduling received',
            'status': 'pending_implementation',
            'scheduled_report': {
                'report_type': data['report_type'],
                'frequency': data['frequency'],
                'recipients': data['recipients'],
                'filters': data.get('filters', {}),
                'created_at': timezone.now().isoformat()
            },
            'note': 'This feature will be implemented with celery/background tasks'
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to schedule report: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@login_required
def reports_dashboard(request):
    """Render the visual reporting dashboard"""
    return render(request, 'admin/reports_dashboard.html', {
        'title': 'Reports Dashboard',
        'site_title': 'DigitalBoda Admin',
        'has_permission': True,
    })