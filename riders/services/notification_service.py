import logging
from typing import Optional, List, Dict, Any
from firebase_admin import messaging, initialize_app, credentials
from django.conf import settings
import os
import json

logger = logging.getLogger(__name__)


class FCMService:
    """Firebase Cloud Messaging service for sending push notifications."""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK."""
        if cls._initialized:
            return
            
        try:
            # Try to get service account key from environment or file
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
            
            if service_account_path and os.path.exists(service_account_path):
                # Initialize with service account file
                cred = credentials.Certificate(service_account_path)
                initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with service account file")
            else:
                # For development/testing, create a mock configuration
                # In production, you would have proper Firebase credentials
                logger.info("Firebase Admin SDK not fully configured - running in development mode")
                # Don't initialize Firebase in development to avoid errors
                return
                
            cls._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
            # For development, we'll continue without FCM
            pass
    
    @classmethod
    def send_status_change_notification(
        cls, 
        fcm_token: str, 
        rider_name: str, 
        new_status: str,
        rejection_reason: Optional[str] = None
    ) -> bool:
        """
        Send status change notification to a specific rider.
        
        Args:
            fcm_token: The FCM token of the rider's device
            rider_name: Name of the rider
            new_status: New status (APPROVED, REJECTED, etc.)
            rejection_reason: Reason for rejection (if applicable)
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        # If still not initialized (development mode), simulate success
        if not cls._initialized:
            logger.info(f"Firebase not initialized - simulating notification to {rider_name}")
            return True
            
        try:
            # Prepare notification content based on status
            if new_status == 'APPROVED':
                title = "🎉 Application Approved!"
                body = f"Congratulations {rider_name}! Your application has been approved. Welcome to DigitalBoda!"
            elif new_status == 'REJECTED':
                title = "❌ Application Status Update"
                body = f"Hi {rider_name}, your application was not approved."
                if rejection_reason:
                    body += f" Reason: {rejection_reason}"
                body += " Please contact your enumerator for more information."
            else:
                title = "📋 Application Status Update"
                body = f"Hi {rider_name}, your application status has been updated to: {new_status}"
            
            # Create the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    'type': 'status_change',
                    'status': new_status,
                    'rider_name': rider_name,
                    'rejection_reason': rejection_reason or '',
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon='ic_stat_notification',
                        color='#4CA1AF',
                        sound='default',
                        channel_id='status_updates'
                    ),
                    priority='high',
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                            sound='default',
                            badge=1,
                        ),
                    ),
                    headers={'apns-priority': '10'},
                ),
            )
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent FCM notification to {rider_name}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send FCM notification to {rider_name}: {str(e)}")
            return False
    
    @classmethod
    def send_bulk_notification(
        cls,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send notification to multiple devices.
        
        Args:
            fcm_tokens: List of FCM tokens
            title: Notification title
            body: Notification body
            data: Additional data to send
            
        Returns:
            Dict with success and failure counts
        """
        if not cls._initialized:
            cls.initialize()
            
        if not fcm_tokens:
            return {'success_count': 0, 'failure_count': 0, 'errors': []}
        
        # If still not initialized (development mode), simulate success
        if not cls._initialized:
            logger.info(f"Firebase not initialized - simulating bulk notification to {len(fcm_tokens)} devices")
            return {
                'success_count': len(fcm_tokens),
                'failure_count': 0,
                'errors': []
            }
            
        try:
            # Create the message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=fcm_tokens,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon='ic_stat_notification',
                        color='#4CA1AF',
                        sound='default',
                    ),
                    priority='high',
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                            sound='default',
                        ),
                    ),
                ),
            )
            
            # Send the message (using send_all for compatibility)
            response = messaging.send_all([messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon='ic_stat_notification',
                        color='#4CA1AF',
                        sound='default',
                    ),
                    priority='high',
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(title=title, body=body),
                            sound='default',
                        ),
                    ),
                ),
            ) for token in fcm_tokens])
            
            logger.info(f"Bulk notification sent - Success: {response.success_count}, Failed: {response.failure_count}")
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [str(resp.exception) for resp in response.responses if not resp.success]
            }
            
        except Exception as e:
            logger.error(f"Failed to send bulk FCM notification: {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(fcm_tokens),
                'errors': [str(e)]
            }
    
    @classmethod
    def update_rider_fcm_token(cls, rider, fcm_token: str) -> bool:
        """
        Update rider's FCM token in the database.
        
        Args:
            rider: Rider instance
            fcm_token: New FCM token
            
        Returns:
            bool: True if updated successfully
        """
        try:
            rider.fcm_token = fcm_token
            rider.save(update_fields=['fcm_token'])
            logger.info(f"Updated FCM token for rider {rider.phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to update FCM token for rider {rider.phone_number}: {str(e)}")
            return False
    
    @classmethod
    def send_notification(
        cls,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a general push notification.
        
        Args:
            fcm_token: FCM token of the device
            title: Notification title
            body: Notification body
            data: Additional data to send
            
        Returns:
            bool: True if sent successfully
        """
        if not cls._initialized:
            cls.initialize()
            
        if not fcm_token:
            logger.warning("No FCM token provided")
            return False
        
        # If still not initialized (development mode), simulate success
        if not cls._initialized:
            logger.info(f"Firebase not initialized - simulating notification: {title}")
            return True
            
        try:
            # Create the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={str(k): str(v) for k, v in (data or {}).items()},  # FCM requires string values
                token=fcm_token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon='ic_stat_notification',
                        color='#4CA1AF',
                        sound='default',
                        channel_id='training_reminders'
                    ),
                    priority='high',
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                            sound='default',
                            badge=1,
                        ),
                    ),
                    headers={'apns-priority': '10'},
                ),
            )
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent notification: {title} -> {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification '{title}': {str(e)}")
            return False
    
    @classmethod
    def send_training_reminder(
        cls,
        fcm_token: str,
        rider_name: str,
        session_title: str,
        session_time: str,
        location: str,
        action: str = 'view_session',
        session_id: int = None
    ) -> bool:
        """
        Send a training session reminder notification.
        
        Args:
            fcm_token: FCM token of the rider
            rider_name: Name of the rider
            session_title: Title of the training session
            session_time: Formatted session time
            location: Session location
            action: Action type for the notification
            session_id: ID of the session schedule
            
        Returns:
            bool: True if sent successfully
        """
        title = f"Training Reminder: {session_title}"
        body = f"Hi {rider_name}! Your {session_title} session is at {session_time} in {location}"
        
        data = {
            'type': 'training_reminder',
            'action': action,
            'session_title': session_title,
            'session_time': session_time,
            'location': location
        }
        
        if session_id:
            data['session_id'] = str(session_id)
        
        return cls.send_notification(fcm_token, title, body, data)