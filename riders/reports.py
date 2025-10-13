# DigitalBoda Reporting System
import csv
import io
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
import pandas as pd

from .models import (
    Rider, SimpleAttendanceRecord, SessionSchedule, TrainingSession, 
    DigitalLiteracyModule, Stage, Enumerator
)


class ReportGenerator:
    """Comprehensive report generation with filtering and export capabilities"""
    
    def __init__(self):
        self.filters = {}
    
    def apply_filters(self, queryset, **filters):
        """Apply comprehensive filtering to any queryset"""
        filtered_qs = queryset
        
        # Date filtering
        if filters.get('start_date'):
            if hasattr(filtered_qs.model, 'session_date'):
                filtered_qs = filtered_qs.filter(session_date__gte=filters['start_date'])
            elif hasattr(filtered_qs.model, 'created_at'):
                filtered_qs = filtered_qs.filter(created_at__gte=filters['start_date'])
            elif hasattr(filtered_qs.model, 'registration_time'):
                filtered_qs = filtered_qs.filter(registration_time__gte=filters['start_date'])
                
        if filters.get('end_date'):
            if hasattr(filtered_qs.model, 'session_date'):
                filtered_qs = filtered_qs.filter(session_date__lte=filters['end_date'])
            elif hasattr(filtered_qs.model, 'created_at'):
                filtered_qs = filtered_qs.filter(created_at__lte=filters['end_date'])
            elif hasattr(filtered_qs.model, 'registration_time'):
                filtered_qs = filtered_qs.filter(registration_time__lte=filters['end_date'])
        
        # Session filtering
        if filters.get('session_id'):
            if hasattr(filtered_qs.model, 'session'):
                filtered_qs = filtered_qs.filter(session_id=filters['session_id'])
        
        # Module filtering
        if filters.get('module_id'):
            if hasattr(filtered_qs.model, 'session'):
                filtered_qs = filtered_qs.filter(session__module_id=filters['module_id'])
        
        # District filtering
        if filters.get('district'):
            if hasattr(filtered_qs.model, 'rider'):
                filtered_qs = filtered_qs.filter(rider__location__icontains=filters['district'])
            elif hasattr(filtered_qs.model, 'location'):
                filtered_qs = filtered_qs.filter(location__icontains=filters['district'])
        
        # Gender filtering
        if filters.get('gender'):
            if hasattr(filtered_qs.model, 'rider'):
                # For attendance records
                filtered_qs = filtered_qs.filter(rider__assigned_enumerator__gender=filters['gender'])
            elif hasattr(filtered_qs.model, 'assigned_enumerator'):
                # For riders
                filtered_qs = filtered_qs.filter(assigned_enumerator__gender=filters['gender'])
        
        # Age group filtering
        if filters.get('age_group'):
            if hasattr(filtered_qs.model, 'rider'):
                filtered_qs = filtered_qs.filter(rider__age_bracket=filters['age_group'])
            elif hasattr(filtered_qs.model, 'age_bracket'):
                filtered_qs = filtered_qs.filter(age_bracket=filters['age_group'])
        
        # Status filtering
        if filters.get('status'):
            filtered_qs = filtered_qs.filter(status=filters['status'])
        
        return filtered_qs
    
    def generate_attendance_report(self, **filters):
        """Generate comprehensive attendance report with filtering"""
        attendance_qs = SimpleAttendanceRecord.objects.select_related(
            'rider', 'session__module', 'trainer'
        ).all()
        
        filtered_attendance = self.apply_filters(attendance_qs, **filters)
        
        report_data = []
        for attendance in filtered_attendance:
            report_data.append({
                'Rider Name': attendance.rider.full_name,
                'Phone Number': attendance.rider.phone_number,
                'Gender': attendance.rider.assigned_enumerator.gender if attendance.rider.assigned_enumerator else 'N/A',
                'Age Group': attendance.rider.age_bracket or 'N/A',
                'Location/District': attendance.rider.location,
                'Module': attendance.session.module.title if attendance.session and attendance.session.module else 'N/A',
                'Session': attendance.session.title if attendance.session else 'N/A',
                'Trainer': attendance.trainer.full_name if attendance.trainer else 'N/A',
                'Session Date': attendance.session_date.strftime('%Y-%m-%d'),
                'Status': attendance.get_status_display(),
                'Points Earned': attendance.points_awarded or 0,
                'Notes': attendance.notes or 'N/A',
                'Recorded At': attendance.recorded_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        return report_data
    
    def generate_rider_summary_report(self, **filters):
        """Generate rider summary report with demographics and progress"""
        rider_qs = Rider.objects.select_related('assigned_enumerator').all()
        filtered_riders = self.apply_filters(rider_qs, **filters)
        
        report_data = []
        for rider in filtered_riders:
            # Calculate attendance stats
            total_sessions = SimpleAttendanceRecord.objects.filter(rider=rider).count()
            attended_sessions = SimpleAttendanceRecord.objects.filter(rider=rider, status='ATTENDED').count()
            attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
            
            report_data.append({
                'Rider ID': rider.unique_id,
                'Full Name': rider.full_name,
                'Phone Number': rider.phone_number,
                'Gender': rider.assigned_enumerator.gender if rider.assigned_enumerator else 'N/A',
                'Age Group': rider.age_bracket or 'N/A',
                'Location/District': rider.location,
                'Status': rider.get_status_display(),
                'Field Agent': rider.assigned_enumerator.full_name if rider.assigned_enumerator else 'N/A',
                'Registration Date': rider.created_at.strftime('%Y-%m-%d'),
                'Total Points': rider.points,
                'Total Sessions Registered': total_sessions,
                'Sessions Attended': attended_sessions,
                'Attendance Rate (%)': round(attendance_rate, 2),
            })
        
        return report_data
    
    def generate_module_completion_report(self, **filters):
        """Generate module completion and progress report"""
        modules = DigitalLiteracyModule.objects.filter(is_active=True)
        
        report_data = []
        for module in modules:
            sessions = TrainingSession.objects.filter(module=module)
            
            for session in sessions:
                # Get attendance data for this session
                attendance_qs = SimpleAttendanceRecord.objects.filter(
                    session=session
                ).select_related('rider', 'rider__assigned_enumerator')
                
                filtered_attendance = self.apply_filters(attendance_qs, **filters)
                
                total_registered = filtered_attendance.count()
                total_attended = filtered_attendance.filter(status='ATTENDED').count()
                completion_rate = (total_attended / total_registered * 100) if total_registered > 0 else 0
                
                # Gender breakdown
                male_attended = filtered_attendance.filter(
                    status='ATTENDED', 
                    rider__assigned_enumerator__gender='M'
                ).count()
                female_attended = filtered_attendance.filter(
                    status='ATTENDED', 
                    rider__assigned_enumerator__gender='F'
                ).count()
                
                report_data.append({
                    'Module': module.title,
                    'Session Number': session.session_number,
                    'Session Title': session.title,
                    'Duration (Hours)': float(session.duration_hours),
                    'Points Value': session.points_value,
                    'Total Registered': total_registered,
                    'Total Attended': total_attended,
                    'Completion Rate (%)': round(completion_rate, 2),
                    'Male Participants': male_attended,
                    'Female Participants': female_attended,
                    'No Shows': total_registered - total_attended,
                })
        
        return report_data
    
    def generate_geographical_report(self, **filters):
        """Generate geographical distribution report"""
        attendance_qs = SimpleAttendanceRecord.objects.select_related('rider').all()
        filtered_attendance = self.apply_filters(attendance_qs, **filters)
        
        # Group by location/district
        location_stats = {}
        for attendance in filtered_attendance:
            location = attendance.rider.location or 'Unknown'
            if location not in location_stats:
                location_stats[location] = {
                    'total_sessions': 0,
                    'attended_sessions': 0,
                    'unique_riders': set(),
                    'male_participants': 0,
                    'female_participants': 0,
                }
            
            location_stats[location]['total_sessions'] += 1
            location_stats[location]['unique_riders'].add(attendance.rider.id)
            
            if attendance.status == 'ATTENDED':
                location_stats[location]['attended_sessions'] += 1
                
                if attendance.rider.assigned_enumerator:
                    if attendance.rider.assigned_enumerator.gender == 'M':
                        location_stats[location]['male_participants'] += 1
                    elif attendance.rider.assigned_enumerator.gender == 'F':
                        location_stats[location]['female_participants'] += 1
        
        report_data = []
        for location, stats in location_stats.items():
            attendance_rate = (stats['attended_sessions'] / stats['total_sessions'] * 100) if stats['total_sessions'] > 0 else 0
            
            report_data.append({
                'Location/District': location,
                'Unique Riders': len(stats['unique_riders']),
                'Total Sessions': stats['total_sessions'],
                'Attended Sessions': stats['attended_sessions'],
                'Attendance Rate (%)': round(attendance_rate, 2),
                'Male Participants': stats['male_participants'],
                'Female Participants': stats['female_participants'],
            })
        
        return sorted(report_data, key=lambda x: x['Unique Riders'], reverse=True)
    
    def export_to_csv(self, data, filename):
        """Export report data to CSV format"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        if not data:
            response.write("No data available for the selected filters.")
            return response
        
        writer = csv.DictWriter(response, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return response
    
    def export_to_excel(self, data, filename, sheet_name="Report"):
        """Export report data to Excel format with formatting"""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        if not data:
            # Create empty workbook with message
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            ws['A1'] = "No data available for the selected filters."
            wb.save(response)
            return response
        
        # Create DataFrame for easier Excel export
        df = pd.DataFrame(data)
        
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # Add title
        ws['A1'] = f"DigitalBoda {sheet_name} - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:E1')
        
        # Add headers starting from row 3
        headers = list(df.columns)
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_num, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Add data
        for row_num, row_data in enumerate(df.values, 4):
            for col_num, value in enumerate(row_data, 1):
                ws.cell(row=row_num, column=col_num, value=value)
        
        # Auto-adjust column widths
        for col_num in range(1, len(headers) + 1):
            max_length = 0
            column_letter = get_column_letter(col_num)
            
            # Check header length
            header_length = len(str(headers[col_num - 1]))
            if header_length > max_length:
                max_length = header_length
            
            # Check data lengths
            for row_num in range(4, ws.max_row + 1):
                cell_value = ws.cell(row=row_num, column=col_num).value
                if cell_value:
                    cell_length = len(str(cell_value))
                    if cell_length > max_length:
                        max_length = cell_length
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        wb.save(response)
        return response


# Report generation functions for easy use
def generate_attendance_csv(request, **filters):
    """Generate and return attendance report as CSV"""
    generator = ReportGenerator()
    data = generator.generate_attendance_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_csv(data, f"attendance_report_{timestamp}")


def generate_attendance_excel(request, **filters):
    """Generate and return attendance report as Excel"""
    generator = ReportGenerator()
    data = generator.generate_attendance_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_excel(data, f"attendance_report_{timestamp}", "Attendance Report")


def generate_rider_summary_csv(request, **filters):
    """Generate and return rider summary report as CSV"""
    generator = ReportGenerator()
    data = generator.generate_rider_summary_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_csv(data, f"rider_summary_{timestamp}")


def generate_rider_summary_excel(request, **filters):
    """Generate and return rider summary report as Excel"""
    generator = ReportGenerator()
    data = generator.generate_rider_summary_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_excel(data, f"rider_summary_{timestamp}", "Rider Summary")


def generate_module_completion_csv(request, **filters):
    """Generate and return module completion report as CSV"""
    generator = ReportGenerator()
    data = generator.generate_module_completion_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_csv(data, f"module_completion_{timestamp}")


def generate_module_completion_excel(request, **filters):
    """Generate and return module completion report as Excel"""
    generator = ReportGenerator()
    data = generator.generate_module_completion_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_excel(data, f"module_completion_{timestamp}", "Module Completion")


def generate_geographical_csv(request, **filters):
    """Generate and return geographical report as CSV"""
    generator = ReportGenerator()
    data = generator.generate_geographical_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_csv(data, f"geographical_report_{timestamp}")


def generate_geographical_excel(request, **filters):
    """Generate and return geographical report as Excel"""
    generator = ReportGenerator()
    data = generator.generate_geographical_report(**filters)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return generator.export_to_excel(data, f"geographical_report_{timestamp}", "Geographical Report")