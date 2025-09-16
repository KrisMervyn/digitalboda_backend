from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from riders.models import NotificationSchedule, Rider
from riders.services.notification_service import FCMService


class Command(BaseCommand):
    help = 'Send scheduled push notifications for training reminders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending notifications',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of notifications to process',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']
        limit = options['limit']
        
        self.stdout.write(f'📱 Processing scheduled notifications at {now}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No notifications will be sent'))

        # Get notifications that should be sent now
        pending_notifications = NotificationSchedule.objects.filter(
            status=NotificationSchedule.PENDING,
            scheduled_time__lte=now
        ).select_related('rider', 'session_schedule__session')[:limit]
        
        if not pending_notifications:
            self.stdout.write(self.style.SUCCESS('✅ No notifications to send'))
            return

        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                if dry_run:
                    self.stdout.write(f'📧 Would send: {notification.title} to {notification.rider.full_name}')
                    continue
                
                # Get rider's FCM token
                if not notification.rider.fcm_token:
                    self.stdout.write(f'⚠️  No FCM token for {notification.rider.full_name}')
                    notification.mark_as_failed("No FCM token")
                    failed_count += 1
                    continue
                
                # Send the notification
                success = FCMService.send_notification(
                    fcm_token=notification.rider.fcm_token,
                    title=notification.title,
                    body=notification.message,
                    data=notification.data
                )
                
                if success:
                    notification.mark_as_sent()
                    sent_count += 1
                    self.stdout.write(f'✅ Sent: {notification.title} to {notification.rider.full_name}')
                else:
                    notification.mark_as_failed("FCM send failed")
                    failed_count += 1
                    self.stdout.write(f'❌ Failed: {notification.title} to {notification.rider.full_name}')
                    
            except Exception as e:
                notification.mark_as_failed(str(e))
                failed_count += 1
                self.stdout.write(f'💥 Error sending to {notification.rider.full_name}: {e}')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 Notification processing complete: {sent_count} sent, {failed_count} failed'
                )
            )
        
        # Schedule automatic reminders for upcoming sessions
        self._schedule_automatic_reminders()
    
    def _schedule_automatic_reminders(self):
        """Schedule reminders for sessions that don't have them yet"""
        from riders.models import SessionSchedule
        from datetime import timedelta
        
        # Get sessions in the next 7 days that don't have reminders scheduled
        upcoming_sessions = SessionSchedule.objects.filter(
            scheduled_date__gte=timezone.now(),
            scheduled_date__lte=timezone.now() + timedelta(days=7),
            status='scheduled'
        ).exclude(
            notificationschedule__isnull=False
        )
        
        total_reminders = 0
        for session in upcoming_sessions:
            count = NotificationSchedule.schedule_session_reminders(session)
            if count > 0:
                total_reminders += count
                self.stdout.write(f'📅 Scheduled {count} reminders for {session.session.title}')
        
        if total_reminders > 0:
            self.stdout.write(
                self.style.SUCCESS(f'🔔 Automatically scheduled {total_reminders} new reminders')
            )