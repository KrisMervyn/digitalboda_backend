# DigitalBoda User Journey with Push Notifications

## Overview
This document outlines the complete user journey for the DigitalBoda system with Firebase Cloud Messaging (FCM) push notifications, showing what happens at each step and the expected outputs.

---

## 🚀 Journey 1: New Rider Registration & Approval

### Step 1: Rider Opens App
**Action**: First-time rider opens DigitalBoda app

**System Behavior**:
- Firebase initializes and requests notification permissions
- FCM token is generated and stored locally
- App navigates to phone number input screen

**Expected Output**:
```
📱 App Console:
🔔 Initializing notification service...
🔔 Notification permission granted
🔔 FCM Token: fR3xK9mBTY8:APA91bH... (truncated)
🔔 FCM token stored locally, will be sent when user authenticates
```

**User Sees**: Permission dialog for notifications, then phone registration screen

---

### Step 2: Phone Number Verification
**Action**: Rider enters phone number (+256753109660) and receives OTP

**System Behavior**:
- Firebase Authentication sends OTP
- User enters OTP and gets authenticated
- Firebase ID token is generated

**Expected Output**:
```
📱 App Console:
🔐 Sending OTP to +256753109660
🔐 Firebase Authentication successful
🔑 Firebase ID Token generated
```

**User Sees**: OTP input screen, then success message

---

### Step 3: Rider Registration
**Action**: Rider fills registration form with enumerator ID (EN-2025-0002)

**Form Data**:
- First Name: John
- Last Name: Doe  
- Experience Level: NEW
- Enumerator ID: EN-2025-0002

**System Behavior**:
- Registration request sent to Django backend
- Rider assigned to enumerator Mukiibi Mike
- Rider status set to REGISTERED

**Expected Output**:
```
📱 App Console:
🚀 Starting registration request...
📱 Phone: +256753109660
👤 Name: John Doe
🎯 Experience: NEW
👨‍💼 Enumerator: EN-2025-0002
📡 Response status: 201
📄 Registration successful

🖥️ Django Server Console:
📝 Registration request received
👤 Creating rider: John Doe (+256753109660)
🔍 Looking up enumerator: EN-2025-0002
✅ Found enumerator: Mukiibi Mike (EN-2025-0002)
🔗 Assigning rider to enumerator
✅ Rider registered successfully with ID: DB-2025-0007
```

**User Sees**: Success screen with reference number DB-2025-0007

---

### Step 4: Onboarding Process
**Action**: Rider completes onboarding with personal details

**Form Data**:
- Age: 28
- Location: Kampala
- National ID: CM12345678901

**System Behavior**:
- Onboarding data saved to database
- Rider status updated to PENDING_APPROVAL
- Rider appears in enumerator's pending list

**Expected Output**:
```
📱 App Console:
🚀 Starting onboarding submission...
📱 Phone: +256753109660
👤 Age: 28
📍 Location: Kampala
🆔 National ID: CM12345678901
📡 Response status: 200
✅ Onboarding completed

🖥️ Django Server Console:
📋 Onboarding submission received
👤 Updating rider: John Doe (+256753109660)
🔄 Status changed: REGISTERED → PENDING_APPROVAL
✅ Rider now pending enumerator approval
```

**User Sees**: Pending approval screen with animated clock

---

### Step 5: FCM Token Registration
**Action**: Pending approval screen loads automatically

**System Behavior**:
- Screen sends FCM token to Django backend
- Token stored in rider's database record
- Polling frequency reduced to 5 minutes
- Real-time notification listener activated

**Expected Output**:
```
📱 App Console:
🔔 Sending FCM token to backend for user: +256753109660
📡 Updating FCM token for: +256753109660
📡 FCM Response status: 200
🔔 FCM token sent successfully to backend

🖥️ Django Server Console:
🔔 FCM Token update request received
✅ FCM token updated for rider +256753109660
📱 Token: fR3xK9mBTY8:APA91bH... (first 20 chars)
```

**User Sees**: Pending approval screen with:
- Reference number: DB-2025-0007
- Applicant name: John Doe
- Status: Pending Review
- "You'll receive a notification once reviewed" message

---

## 👨‍💼 Journey 2: Enumerator Reviews Application

### Step 6: Enumerator Logs In
**Action**: Enumerator Mukiibi Mike logs into admin app with EN-2025-0002

**System Behavior**:
- Enumerator authentication verified
- Dashboard loads with pending riders count
- John Doe appears in pending list

**Expected Output**:
```
📱 Admin App Console:
🔐 Enumerator login: EN-2025-0002
✅ Authentication successful
👨‍💼 Enumerator: Mukiibi Mike
📊 Loading dashboard stats...
📋 Pending riders: 1
```

**Enumerator Sees**: Dashboard showing:
- Name: Mukiibi Mike
- ID: EN-2025-0002
- 1 Pending Approval
- John Doe in the pending riders list

---

### Step 7: Enumerator Approves Rider
**Action**: Enumerator clicks "Approve" on John Doe's application

**System Behavior**:
- Rider status updated to APPROVED
- FCM notification sent to rider's device
- Database updated with approval timestamp

**Expected Output**:
```
📱 Admin App Console:
✅ Rider approved successfully
📨 Notification sent to John Doe

🖥️ Django Server Console:
🔔 Rider approval request for rider 7
✅ Rider +256753109660 approved
🔔 Approval notification sent to John Doe
📧 FCM notification dispatched successfully
🕐 Approved at: 2025-09-10 09:23:45
```

**Enumerator Sees**: Success message "Rider approved successfully"

---

### Step 8: Rider Receives Push Notification
**Action**: Automatic - FCM delivers notification to rider's device

**System Behavior**:
- FCM sends push notification to rider's device
- Local notification displayed with sound and vibration
- App callback triggered if app is open
- Pending approval screen immediately updates

**Expected Output**:
```
📱 Rider App Console:
🔔 FCM notification received: Application Approved!
🔔 Status changed from PENDING_APPROVAL to APPROVED
🎉 Showing approval success dialog
📱 Navigating to home screen

Push Notification Content:
Title: "🎉 Application Approved!"
Body: "Congratulations John Doe! Your application has been approved. Welcome to DigitalBoda!"
Sound: Default notification sound
Vibration: Default pattern
```

**User Sees**: 
1. **Push notification** appears in notification bar/lock screen
2. **Approval dialog** appears if app is open:
   - Green checkmark icon
   - "Congratulations!" title
   - Welcome message
   - "Start Training" button

---

### Step 9: Rider Starts Training
**Action**: Rider taps "Start Training" button

**System Behavior**:
- Navigation to HomeScreen
- Training modules become available
- User can begin lesson progression

**Expected Output**:
```
📱 App Console:
🏠 Navigating to HomeScreen
📚 Training modules loaded
🎯 Ready to start lessons
```

**User Sees**: Home screen with available training modules

---

## ❌ Alternative Journey: Application Rejection

### Alternative Step 7: Enumerator Rejects Rider
**Action**: Enumerator clicks "Reject" and provides reason "Incomplete documentation"

**System Behavior**:
- Rider status updated to REJECTED
- Rejection reason stored in database
- FCM notification sent with rejection details

**Expected Output**:
```
📱 Admin App Console:
❌ Rider rejected: Incomplete documentation
📨 Rejection notification sent to John Doe

🖥️ Django Server Console:
🔔 Rider rejection request for rider 7
✅ Rider +256753109660 rejected: Incomplete documentation
🔔 Rejection notification sent to John Doe
📧 FCM notification dispatched successfully
💾 Rejection reason stored in database
```

**Enumerator Sees**: Success message "Rider rejected successfully"

---

### Step 8b: Rider Receives Rejection Notification
**Action**: Automatic - FCM delivers rejection notification

**Expected Output**:
```
📱 Rider App Console:
🔔 FCM notification received: Application Status Update
🔔 Status changed from PENDING_APPROVAL to REJECTED
📱 Fetching full profile for rejection details
❌ Showing rejection dialog with reason

Push Notification Content:
Title: "❌ Application Status Update"
Body: "Hi John Doe, your application was not approved. Reason: Incomplete documentation. Please contact your enumerator for more information."
Sound: Default notification sound
```

**User Sees**:
1. **Push notification** in notification bar
2. **Rejection dialog** if app is open:
   - Red X icon
   - "Application Status" title
   - "Your application was not approved" message
   - Reason: "Incomplete documentation"
   - "Contact your enumerator" guidance
   - "OK" button

---

## 📊 Technical Outputs & Monitoring

### Database State Changes
```sql
-- After Registration
INSERT INTO riders_rider (phone_number, first_name, last_name, status, assigned_enumerator_id, ...)
VALUES ('+256753109660', 'John', 'Doe', 'REGISTERED', 2, ...);

-- After Onboarding
UPDATE riders_rider SET 
  status = 'PENDING_APPROVAL',
  age = 28,
  location = 'Kampala',
  national_id_number = 'CM12345678901'
WHERE phone_number = '+256753109660';

-- After FCM Token Update
UPDATE riders_rider SET 
  fcm_token = 'fR3xK9mBTY8:APA91bH...'
WHERE phone_number = '+256753109660';

-- After Approval
UPDATE riders_rider SET 
  status = 'APPROVED',
  approved_at = '2025-09-10 09:23:45',
  approved_by_id = 2
WHERE phone_number = '+256753109660';
```

### API Request/Response Examples

**FCM Token Update Request:**
```http
PUT /api/fcm/update-token/ HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
Content-Type: application/json

{
  "fcm_token": "fR3xK9mBTY8:APA91bH...",
  "phone_number": "+256753109660"
}
```

**FCM Token Update Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "FCM token updated successfully"
}
```

**Rider Approval Request:**
```http
POST /api/riders/7/approve/ HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
```

**Rider Approval Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Rider approved successfully",
  "notification_sent": true
}
```

### System Performance Metrics

**Before FCM Implementation:**
- Polling frequency: Every 30 seconds
- Server requests per hour per user: 120 requests
- Battery impact: High (continuous background requests)
- Notification delay: Up to 30 seconds

**After FCM Implementation:**
- Polling frequency: Every 5 minutes (backup only)
- Server requests per hour per user: 12 requests (90% reduction)
- Battery impact: Low (push-based updates)
- Notification delay: Near-instant (1-3 seconds)

---

## 🎯 User Experience Summary

### Rider Experience
✅ **Seamless**: Automatic notification permissions and token management  
✅ **Fast**: Instant notifications when status changes  
✅ **Clear**: Descriptive messages with actionable content  
✅ **Reliable**: Fallback polling ensures no missed updates  
✅ **Battery Friendly**: Minimal background activity

### Enumerator Experience
✅ **Efficient**: Simple approve/reject actions  
✅ **Feedback**: Confirmation that notifications were sent  
✅ **Real-time**: Dashboard updates immediately  
✅ **Trackable**: Clear audit trail of actions

### System Benefits
✅ **Scalable**: 90% reduction in server polling requests  
✅ **Reliable**: Multiple notification delivery methods  
✅ **Maintainable**: Comprehensive logging and error handling  
✅ **Secure**: Token-based authentication throughout  
✅ **Testable**: Full end-to-end test coverage