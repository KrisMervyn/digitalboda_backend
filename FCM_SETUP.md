# Firebase Cloud Messaging (FCM) Setup Guide

## Overview
This guide explains how to set up Firebase Cloud Messaging (FCM) for the DigitalBoda backend to send push notifications to rider mobile apps.

## Prerequisites
- Firebase project with FCM enabled
- Firebase Admin SDK service account key
- Django backend with FCM service implemented

## Configuration Steps

### 1. Firebase Console Setup
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your DigitalBoda project
3. Navigate to **Project Settings** > **Service Accounts**
4. Click **Generate new private key**
5. Download the JSON service account key file

### 2. Backend Configuration

#### Environment Variables
Add the following to your `.env` file:

```bash
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_KEY=/path/to/your/service-account-key.json
```

#### Alternative: Environment Variable JSON
Instead of a file path, you can set the entire service account key as an environment variable:

```bash
FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"your-project-id",...}'
```

### 3. Service Account Key Placement
Place your `service-account-key.json` file in a secure location:
- **Development**: In your project root (add to .gitignore)
- **Production**: In a secure directory like `/etc/firebase/` or use environment variables

### 4. Testing FCM Setup

Run the test script to verify everything is working:

```bash
source venv/bin/activate
python test_fcm.py
```

## API Endpoints

### Update FCM Token
**PUT** `/api/fcm/update-token/`

Request:
```json
{
  "fcm_token": "device_fcm_token_here",
  "phone_number": "+256700000000"
}
```

Headers:
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

### Approve Rider (with notification)
**POST** `/api/riders/{rider_id}/approve/`

Headers:
```
Authorization: Bearer <firebase_id_token>
```

### Reject Rider (with notification)
**POST** `/api/riders/{rider_id}/reject/`

Request:
```json
{
  "rejection_reason": "Reason for rejection"
}
```

Headers:
```
Authorization: Bearer <firebase_id_token>
```

## Flutter App Integration

The Flutter app automatically:
1. Gets FCM token on app start
2. Sends token to backend when user reaches pending approval screen
3. Listens for status change notifications
4. Displays notifications when app is in foreground/background

## Notification Types

### Status Change Notifications
- **APPROVED**: Congratulations message with call to action
- **REJECTED**: Rejection message with reason (if provided)
- **OTHER**: General status update message

### Notification Data Structure
```json
{
  "notification": {
    "title": "Application Status Update",
    "body": "Your application has been approved!"
  },
  "data": {
    "type": "status_change",
    "status": "APPROVED",
    "rider_name": "John Doe",
    "rejection_reason": ""
  }
}
```

## Security Considerations

1. **Service Account Key**: Keep the service account key secure and never commit it to version control
2. **Token Verification**: All API endpoints verify Firebase ID tokens before processing
3. **FCM Token Storage**: FCM tokens are stored securely in the database
4. **Error Handling**: Graceful handling of FCM errors and token refresh

## Troubleshooting

### Common Issues

1. **FCM Token Not Updating**
   - Check Firebase token verification
   - Ensure phone number matches database record
   - Verify network connectivity

2. **Notifications Not Sending**
   - Check Firebase service account key configuration
   - Verify FCM token is valid and stored in database
   - Check server logs for FCM errors

3. **App Not Receiving Notifications**
   - Verify app has notification permissions
   - Check FCM token registration with backend
   - Test with Firebase Console test message

### Debug Commands

```bash
# Test FCM service
python test_fcm.py

# Check rider FCM tokens in database
python manage.py shell
>>> from riders.models import Rider
>>> riders_with_tokens = Rider.objects.exclude(fcm_token__isnull=True)
>>> for rider in riders_with_tokens:
...     print(f"{rider.full_name}: {rider.fcm_token[:20]}...")

# Send test notification
>>> from riders.services.notification_service import FCMService
>>> rider = Rider.objects.first()
>>> FCMService.send_status_change_notification(
...     rider.fcm_token, rider.full_name, 'APPROVED'
... )
```

## Production Deployment

1. Set environment variables in your production environment
2. Ensure service account key is accessible to the Django application
3. Configure proper logging for FCM operations
4. Monitor FCM usage in Firebase Console
5. Set up alerts for FCM failures

## Next Steps

1. Add FCM token refresh handling
2. Implement notification analytics
3. Add support for notification categories
4. Implement notification scheduling
5. Add bulk notification capabilities for broadcasts