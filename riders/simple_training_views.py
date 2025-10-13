# =============================================================================
# 📚 SIMPLIFIED TRAINING SYSTEM API ENDPOINTS
# Digital Boda - Trainer-Managed Training & Attendance System
# =============================================================================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import date
from .models import (
    Rider, DigitalLiteracyModule, TrainingSession, 
    Enumerator, TrainingInterest, SimpleAttendanceRecord
)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_modules(request):
    """Get available training modules for enrollment"""
    try:
        modules = DigitalLiteracyModule.objects.filter(is_active=True).order_by('order')
        
        modules_data = []
        for module in modules:
            sessions = TrainingSession.objects.filter(module=module).order_by('session_number')
            
            modules_data.append({
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'icon': module.icon,
                'session_count': module.session_count,
                'total_duration_hours': float(module.total_duration_hours),
                'points_value': module.points_value,
                'sessions': [
                    {
                        'id': session.id,
                        'session_number': session.session_number,
                        'title': session.title,
                        'description': session.description,
                        'duration_hours': float(session.duration_hours),
                        'points_value': session.points_value,
                    }
                    for session in sessions
                ]
            })
        
        return Response({
            'success': True,
            'data': modules_data,
            'message': f'Found {len(modules_data)} available training modules'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch training modules: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def simple_enroll_in_module(request):
    """Simplified enrollment - records rider interest in a module"""
    try:
        data = request.data
        phone_number = data.get('phone_number')
        module_id = data.get('module_id')
        
        # Validate required fields
        if not all([phone_number, module_id]):
            return Response({
                'error': 'Missing required fields: phone_number, module_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rider
        try:
            rider = Rider.objects.get(phone_number=phone_number)
        except Rider.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get module
        try:
            module = DigitalLiteracyModule.objects.get(id=module_id, is_active=True)
        except DigitalLiteracyModule.DoesNotExist:
            return Response({'error': 'Training module not found or not available'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if rider already expressed interest in this module
        existing_interest = TrainingInterest.objects.filter(
            rider=rider, 
            module=module, 
            is_active=True
        ).first()
        
        if existing_interest:
            return Response({
                'success': True,
                'data': {
                    'module_title': module.title,
                    'module_description': module.description,
                    'module_icon': module.icon,
                    'trainer_name': rider.assigned_enumerator.full_name if rider.assigned_enumerator else 'Will be assigned',
                    'total_sessions': module.session_count,
                    'total_points': module.points_value,
                    'next_steps': 'You have already expressed interest in this module. Your trainer will contact you soon.',
                    'previously_expressed': True
                },
                'message': f'You have already expressed interest in {module.title}!'
            }, status=status.HTTP_201_CREATED)
        
        # Determine the trainer for this module
        # Check if module has an assigned trainer, fallback to rider's assigned trainer
        if hasattr(module, 'assigned_trainer') and module.assigned_trainer:
            module_trainer = module.assigned_trainer
        else:
            module_trainer = rider.assigned_enumerator
        
        # Record the training interest
        TrainingInterest.objects.create(
            rider=rider,
            module=module,
            trainer=module_trainer
        )
        
        return Response({
            'success': True,
            'data': {
                'module_title': module.title,
                'module_description': module.description,
                'module_icon': module.icon,
                'trainer_name': rider.assigned_enumerator.full_name if rider.assigned_enumerator else 'Will be assigned',
                'total_sessions': module.session_count,
                'total_points': module.points_value,
                'next_steps': 'Your trainer will contact you to schedule the training sessions.'
            },
            'message': f'Successfully expressed interest in {module.title}! Your trainer will contact you soon.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Enrollment failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_rider_training_progress(request):
    """Get rider's training progress from existing attendance data"""
    try:
        phone_number = request.GET.get('phone_number')
        
        if not phone_number:
            return Response({
                'error': 'phone_number parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rider
        try:
            rider = Rider.objects.get(phone_number=phone_number)
        except Rider.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get rider's training interests (modules they've expressed interest in)
        training_interests = TrainingInterest.objects.filter(
            rider=rider, 
            is_active=True
        ).select_related('module', 'trainer')
        
        # Get rider's attendance records using SimpleAttendanceRecord
        attendance_records = SimpleAttendanceRecord.objects.filter(
            rider=rider
        ).select_related('session__module', 'trainer')
        
        # Calculate basic stats
        total_sessions_attended = attendance_records.filter(status='ATTENDED').count()
        total_points = attendance_records.filter(status='ATTENDED').aggregate(
            total=Sum('points_awarded')
        )['total'] or 0
        
        # Build module progress data based on training interests and attendance
        modules_data = []
        
        # Get modules the rider has expressed interest in
        interested_module_ids = training_interests.values_list('module_id', flat=True)
        
        for interest in training_interests:
            module = interest.module
            
            # Count attended sessions for this specific module
            module_attendance = attendance_records.filter(
                session__module=module,
                status='ATTENDED'
            )
            module_attended = module_attendance.count()
            
            # Calculate points earned for this module
            module_points = module_attendance.aggregate(
                total=Sum('points_awarded')
            )['total'] or 0
            
            # Calculate completion percentage
            completion_percentage = round((module_attended / module.session_count) * 100) if module.session_count > 0 else 0
            
            # Determine status
            if completion_percentage >= 100:
                status_text = 'COMPLETED'
            elif module_attended > 0:
                status_text = 'IN_PROGRESS'
            else:
                status_text = 'ENROLLED'
            
            modules_data.append({
                'module_id': module.id,
                'module_title': module.title,
                'module_icon': module.icon,
                'total_sessions': module.session_count,
                'attended_sessions': module_attended,
                'completion_percentage': completion_percentage,
                'status': status_text,
                'points_value': module.points_value,
                'points_earned': module_points,
                'trainer': interest.trainer.full_name if interest.trainer else 'Not assigned',
                'enrolled_date': interest.expressed_at.strftime('%Y-%m-%d')
            })
        
        # Also show available modules that rider hasn't expressed interest in yet
        all_modules = DigitalLiteracyModule.objects.filter(is_active=True).exclude(
            id__in=interested_module_ids
        ).order_by('order')
        
        for module in all_modules:
            modules_data.append({
                'module_id': module.id,
                'module_title': module.title,
                'module_icon': module.icon,
                'total_sessions': module.session_count,
                'attended_sessions': 0,
                'completion_percentage': 0,
                'status': 'AVAILABLE',
                'points_value': module.points_value,
                'points_earned': 0,
                'trainer': 'Express interest to get assigned',
                'enrolled_date': None
            })

        # Calculate overall statistics
        enrolled_modules = [m for m in modules_data if m['status'] in ['ENROLLED', 'IN_PROGRESS', 'COMPLETED']]
        in_progress_modules = [m for m in modules_data if m['status'] == 'IN_PROGRESS']
        completed_modules = [m for m in modules_data if m['status'] == 'COMPLETED']
        available_modules = [m for m in modules_data if m['status'] == 'AVAILABLE']
        
        progress_data = {
            'rider_info': {
                'name': rider.full_name,
                'phone': rider.phone_number,
                'trainer': rider.assigned_enumerator.full_name if rider.assigned_enumerator else 'Not assigned',
                'rider_id': rider.unique_id,
                'status': rider.status
            },
            'overall_stats': {
                'total_sessions_attended': total_sessions_attended,
                'total_points_earned': total_points,
                'modules_enrolled': len(enrolled_modules),
                'modules_available': len(available_modules),
                'modules_in_progress': len(in_progress_modules),
                'modules_completed': len(completed_modules),
                'training_interests': len(training_interests)
            },
            'modules': modules_data,
            'recent_attendance': [
                {
                    'session_name': record.session.title if record.session else 'Training Session',
                    'module_name': record.session.module.title if record.session and record.session.module else 'Unknown Module',
                    'date': record.session_date.strftime('%Y-%m-%d'),
                    'status': record.get_status_display(),
                    'points_earned': record.points_awarded,
                    'trainer': record.trainer.full_name if record.trainer else 'Unknown'
                }
                for record in attendance_records.order_by('-session_date')[:5]
            ]
        }
        
        return Response({
            'success': True,
            'data': progress_data,
            'message': 'Training progress retrieved successfully'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Failed to fetch training progress: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_trainer_students(request):
    """Get list of students assigned to a trainer"""
    try:
        trainer_id = request.GET.get('trainer_id')
        
        if not trainer_id:
            return Response({
                'error': 'trainer_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get trainer
        try:
            trainer = Enumerator.objects.get(unique_id=trainer_id)
        except Enumerator.DoesNotExist:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get unique rider IDs who have expressed interest in training modules for this trainer
        interested_rider_ids = TrainingInterest.objects.filter(
            trainer=trainer, 
            is_active=True
        ).values_list('rider_id', flat=True).distinct()
        
        # Get the unique riders
        unique_riders = Rider.objects.filter(id__in=interested_rider_ids)
        
        students_data = []
        for student in unique_riders:
            # Get attendance count using SimpleAttendanceRecord
            attendance_count = SimpleAttendanceRecord.objects.filter(
                rider=student, 
                trainer=trainer,
                status='ATTENDED'
            ).count()
            
            # Get modules they're interested in
            interested_modules = TrainingInterest.objects.filter(
                rider=student,
                trainer=trainer,
                is_active=True
            ).values_list('module__title', flat=True)
            
            students_data.append({
                'id': student.id,
                'name': student.full_name,
                'phone': student.phone_number,
                'unique_id': student.unique_id,
                'sessions_attended': attendance_count,
                'points': getattr(student, 'points', 0),
                'joined_date': student.created_at.date(),
                'interested_modules': list(interested_modules),
                'modules_count': len(interested_modules)
            })
        
        return Response({
            'success': True,
            'data': {
                'trainer': {
                    'name': trainer.full_name,
                    'unique_id': trainer.unique_id
                },
                'students': students_data,
                'total_students': len(students_data)
            },
            'message': f'Found {len(students_data)} students'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch students: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def mark_student_attendance(request):
    """Simple trainer interface to mark student attendance"""
    try:
        data = request.data
        trainer_id = data.get('trainer_id')
        student_phone = data.get('student_phone')
        session_id = data.get('session_id')
        attendance_status = data.get('status', 'ATTENDED')  # ATTENDED, ABSENT, LATE, EXCUSED
        session_date = data.get('session_date', timezone.now().date())
        notes = data.get('notes', '')
        
        # Validate required fields
        if not all([trainer_id, student_phone, session_id]):
            return Response({
                'error': 'Missing required fields: trainer_id, student_phone, session_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get trainer
        try:
            trainer = Enumerator.objects.get(unique_id=trainer_id)
        except Enumerator.DoesNotExist:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get student
        try:
            student = Rider.objects.get(phone_number=student_phone)
        except Rider.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get session first
        try:
            session = TrainingSession.objects.get(id=session_id)
        except TrainingSession.DoesNotExist:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Verify trainer has authority to mark attendance for this student
        # Check if trainer is assigned to student OR if trainer is responsible for the module
        module = session.module
        
        trainer_has_authority = (
            student.assigned_enumerator == trainer or  # Direct assignment
            (hasattr(module, 'assigned_trainer') and module.assigned_trainer == trainer) or  # Module-specific assignment
            TrainingInterest.objects.filter(rider=student, module=module, trainer=trainer, is_active=True).exists()  # Interest recorded with this trainer
        )
        
        if not trainer_has_authority:
            return Response({
                'error': 'You are not authorized to mark attendance for this student in this module'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create the attendance record
        points_awarded = session.points_value if attendance_status == 'ATTENDED' else 0
        
        # Check if record already exists for this date
        existing_record, created = SimpleAttendanceRecord.objects.get_or_create(
            rider=student,
            session=session,
            session_date=session_date,
            defaults={
                'trainer': trainer,
                'status': attendance_status,
                'points_awarded': points_awarded,
                'notes': notes
            }
        )
        
        if not created:
            # Update existing record
            existing_record.status = attendance_status
            existing_record.points_awarded = points_awarded
            existing_record.notes = notes
            existing_record.trainer = trainer
            existing_record.save()
        
        response_data = {
            'attendance_id': existing_record.id,
            'student_name': student.full_name,
            'session_title': session.title,
            'module_title': session.module.title,
            'attendance_status': attendance_status,
            'session_date': str(session_date),
            'points_awarded': points_awarded,
            'trainer_name': trainer.full_name,
            'notes': notes,
            'was_updated': not created
        }
        
        return Response({
            'success': True,
            'data': response_data,
            'message': f'Attendance marked: {student.full_name} - {attendance_status} for {session.title}'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to mark attendance: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_daily_attendance_stats(request):
    """Get real-time daily attendance statistics for trainer dashboard"""
    try:
        trainer_id = request.GET.get('trainer_id')
        target_date = request.GET.get('date', str(date.today()))
        
        if not trainer_id:
            return Response({
                'error': 'trainer_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get trainer
        try:
            trainer = Enumerator.objects.get(unique_id=trainer_id)
        except Enumerator.DoesNotExist:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse target date
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            target_date = date.today()
        
        # Get today's attendance records for this trainer
        daily_records = SimpleAttendanceRecord.objects.filter(
            trainer=trainer,
            session_date=target_date
        )
        
        # Calculate stats
        total_marked = daily_records.count()
        attended = daily_records.filter(status='ATTENDED').count()
        absent = daily_records.filter(status='ABSENT').count()
        late = daily_records.filter(status='LATE').count()
        excused = daily_records.filter(status='EXCUSED').count()
        
        # Get session breakdown
        session_stats = daily_records.values(
            'session__title',
            'session__module__title',
            'session_id'
        ).annotate(
            total_students=Count('id'),
            attended_count=Count('id', filter=Q(status='ATTENDED')),
            absent_count=Count('id', filter=Q(status='ABSENT')),
            late_count=Count('id', filter=Q(status='LATE')),
            excused_count=Count('id', filter=Q(status='EXCUSED'))
        ).order_by('session__module__title', 'session__title')
        
        # Get recent attendance records (last 10)
        recent_records = daily_records.select_related(
            'rider', 'session', 'session__module'
        ).order_by('-recorded_at')[:10]
        
        recent_attendance = [
            {
                'attendance_id': record.id,
                'student_name': f"{record.rider.first_name} {record.rider.last_name}",
                'student_phone': record.rider.phone_number,
                'session_title': record.session.title,
                'module_title': record.session.module.title,
                'status': record.status,
                'points_awarded': record.points_awarded,
                'recorded_at': record.recorded_at.isoformat(),
                'notes': record.notes or ''
            }
            for record in recent_records
        ]
        
        dashboard_data = {
            'trainer_info': {
                'name': trainer.full_name,
                'unique_id': trainer.unique_id
            },
            'date': str(target_date),
            'is_today': target_date == date.today(),
            'summary_stats': {
                'total_marked': total_marked,
                'attended': attended,
                'absent': absent,
                'late': late,
                'excused': excused,
                'attendance_rate': round((attended / total_marked * 100) if total_marked > 0 else 0, 1)
            },
            'session_breakdown': list(session_stats),
            'recent_attendance': recent_attendance
        }
        
        return Response({
            'success': True,
            'data': dashboard_data,
            'message': f'Daily attendance stats for {target_date}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Failed to fetch daily attendance stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_session_attendance_details(request):
    """Get detailed attendance for a specific session on a specific date"""
    try:
        trainer_id = request.GET.get('trainer_id')
        session_id = request.GET.get('session_id')
        target_date = request.GET.get('date', str(date.today()))
        
        if not all([trainer_id, session_id]):
            return Response({
                'error': 'trainer_id and session_id parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get trainer
        try:
            trainer = Enumerator.objects.get(unique_id=trainer_id)
        except Enumerator.DoesNotExist:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get session
        try:
            session = TrainingSession.objects.get(id=session_id)
        except TrainingSession.DoesNotExist:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse target date
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            target_date = date.today()
        
        # Get attendance records for this session on this date
        attendance_records = SimpleAttendanceRecord.objects.filter(
            trainer=trainer,
            session=session,
            session_date=target_date
        ).select_related('rider').order_by('rider__first_name', 'rider__last_name')
        
        detailed_attendance = [
            {
                'attendance_id': record.id,
                'student_name': f"{record.rider.first_name} {record.rider.last_name}",
                'student_phone': record.rider.phone_number,
                'student_id': record.rider.unique_id,
                'status': record.status,
                'points_awarded': record.points_awarded,
                'recorded_at': record.recorded_at.isoformat(),
                'notes': record.notes or ''
            }
            for record in attendance_records
        ]
        
        session_data = {
            'session_info': {
                'id': session.id,
                'title': session.title,
                'module_title': session.module.title,
                'session_number': session.session_number,
                'duration_hours': float(session.duration_hours),
                'points_value': session.points_value
            },
            'trainer_info': {
                'name': trainer.full_name,
                'unique_id': trainer.unique_id
            },
            'date': str(target_date),
            'attendance_summary': {
                'total_students': len(detailed_attendance),
                'attended': len([r for r in detailed_attendance if r['status'] == 'ATTENDED']),
                'absent': len([r for r in detailed_attendance if r['status'] == 'ABSENT']),
                'late': len([r for r in detailed_attendance if r['status'] == 'LATE']),
                'excused': len([r for r in detailed_attendance if r['status'] == 'EXCUSED'])
            },
            'attendance_records': detailed_attendance
        }
        
        return Response({
            'success': True,
            'data': session_data,
            'message': f'Session attendance details for {session.title} on {target_date}'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch session attendance details: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_attendance_history(request):
    """Get attendance history over a date range for analytics"""
    try:
        trainer_id = request.GET.get('trainer_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not trainer_id:
            return Response({
                'error': 'trainer_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get trainer
        try:
            trainer = Enumerator.objects.get(unique_id=trainer_id)
        except Enumerator.DoesNotExist:
            return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse dates with defaults (last 7 days if not specified)
        if not end_date:
            end_date = date.today()
        else:
            end_date = date.fromisoformat(end_date)
            
        if not start_date:
            from datetime import timedelta
            start_date = end_date - timedelta(days=6)  # 7 days total
        else:
            start_date = date.fromisoformat(start_date)
        
        # Get attendance records in date range
        records = SimpleAttendanceRecord.objects.filter(
            trainer=trainer,
            session_date__gte=start_date,
            session_date__lte=end_date
        ).select_related('rider', 'session', 'session__module')
        
        # Group by date for daily breakdown
        daily_stats = {}
        from datetime import timedelta
        current_date = start_date
        
        while current_date <= end_date:
            date_str = str(current_date)
            daily_records = records.filter(session_date=current_date)
            
            daily_stats[date_str] = {
                'date': date_str,
                'is_today': current_date == date.today(),
                'total_marked': daily_records.count(),
                'attended': daily_records.filter(status='ATTENDED').count(),
                'absent': daily_records.filter(status='ABSENT').count(),
                'late': daily_records.filter(status='LATE').count(),
                'excused': daily_records.filter(status='EXCUSED').count(),
                'unique_students': daily_records.values('rider').distinct().count(),
                'total_points_awarded': sum(r.points_awarded for r in daily_records)
            }
            
            # Calculate attendance rate
            total = daily_stats[date_str]['total_marked']
            attended = daily_stats[date_str]['attended']
            daily_stats[date_str]['attendance_rate'] = round((attended / total * 100) if total > 0 else 0, 1)
            
            current_date += timedelta(days=1)
        
        # Overall summary for the period
        total_records = records.count()
        period_summary = {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_days': (end_date - start_date).days + 1,
            'total_sessions_conducted': total_records,
            'total_attended': records.filter(status='ATTENDED').count(),
            'total_absent': records.filter(status='ABSENT').count(),
            'total_late': records.filter(status='LATE').count(),
            'total_excused': records.filter(status='EXCUSED').count(),
            'unique_students_trained': records.values('rider').distinct().count(),
            'total_points_awarded': sum(r.points_awarded for r in records),
            'average_daily_sessions': round(total_records / max(1, (end_date - start_date).days + 1), 1)
        }
        
        # Calculate overall attendance rate
        total_attended = period_summary['total_attended']
        period_summary['overall_attendance_rate'] = round((total_attended / total_records * 100) if total_records > 0 else 0, 1)
        
        history_data = {
            'trainer_info': {
                'name': trainer.full_name,
                'unique_id': trainer.unique_id
            },
            'period_summary': period_summary,
            'daily_breakdown': list(daily_stats.values()),
            'recent_sessions': [
                {
                    'date': str(record.session_date),
                    'student_name': f"{record.rider.first_name} {record.rider.last_name}",
                    'session_title': record.session.title,
                    'module_title': record.session.module.title,
                    'status': record.status,
                    'points_awarded': record.points_awarded,
                    'recorded_at': record.recorded_at.isoformat()
                }
                for record in records.order_by('-recorded_at')[:20]
            ]
        }
        
        return Response({
            'success': True,
            'data': history_data,
            'message': f'Attendance history from {start_date} to {end_date}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Failed to fetch attendance history: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)