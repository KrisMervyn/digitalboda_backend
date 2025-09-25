# FCM Push Notifications Testing Guide

## Overview
This guide provides step-by-step instructions for testing the complete Firebase Cloud Messaging (FCM) push notification system for DigitalBoda.

---

## 🚀 Quick Test (Automated)

### 1. Run Automated Test Suite
```bash
cd /home/katende/Desktop/DigitalBoda/digitalboda_backend
source venv/bin/activate
python test_notification_flow.py
```

**Expected Result**: All 5 tests should pass (100% success rate)

**What This Tests**:
- FCM token storage and retrieval
- Status change notifications
- Approval/rejection endpoints with notifications
- Bulk notification functionality
- Database integration

---

## 📱 Manual End-to-End Testing

### Prerequisites
1. **Django Server Running**: `python manage.py runserver 192.168.1.25:8000`
2. **Two Devices/Emulators**:
   - Device A: DigitalBoda Rider App
   - Device B: DigitalBoda Admin App
3. **Test Data**: Enumerator Mukiibi Mike (EN-2025-0002) should exist

---

## 🎯 Test Scenario 1: Complete Registration & Approval Flow

### Step 1: Setup Test Environment
```bash
# Ensure Django server is running
source venv/bin/activate
python manage.py runserver 192.168.1.25:8000

# Check test data exists
python manage.py shell
>>> from riders.models import Enumerator
>>> enumerator = Enumerator.objects.get(unique_id='EN-2025-0002')
>>> print(f"Enumerator: {enumerator.full_name}")
>>> exit()
```

### Step 2: Test Rider Registration (Device A)
1. **Open** DigitalBoda Rider App
2. **Allow** notification permissions when prompted
3. **Enter** test phone number: `+256700000001`
4. **Complete** OTP verification
5. **Fill** registration form:
   - First Name: `Test`
   - Last Name: `Rider`
   - Experience: `New Rider`
   - Enumerator ID: `EN-2025-0002`
6. **Submit** registration

**Expected Results**:
```
✅ Registration successful with reference number
✅ Navigate to onboarding screen
```

**Check Console Logs**:
```
📱 App Console:
🚀 Starting registration request...
📡 Response status: 201
✅ Registration successful

🖥️ Django Console:
📝 Registration request received
✅ Rider registered successfully with ID: DB-2025-XXXX
```

### Step 3: Complete Onboarding (Device A)
1. **Fill** onboarding form:
   - Age: `25`
   - Location: `Kampala`
   - National ID: `CM98765432101`
2. **Submit** onboarding

**Expected Results**:
```
✅ Onboarding completed
✅ Navigate to pending approval screen
✅ FCM token automatically sent to backend
```

**Check Console Logs**:
```
📱 App Console:
🔔 Sending FCM token to backend for user: +256700000001
📡 FCM Response status: 200
🔔 FCM token sent successfully to backend

🖥️ Django Console:
🔔 FCM Token update request received
✅ FCM token updated for rider +256700000001
```

### Step 4: Verify Pending Status (Device A)
**Check Pending Approval Screen Shows**:
- ✅ Reference number (DB-2025-XXXX)
- ✅ Applicant name: Test Rider
- ✅ Status: Pending Review
- ✅ Notification message about 1-2 business days
- ✅ Check Status button

### Step 5: Enumerator Login (Device B)
1. **Open** DigitalBoda Admin App
2. **Login** with credentials:
   - Enumerator ID: `EN-2025-0002`
   - Password: `mukiibi123`

**Expected Results**:
```
✅ Dashboard loads with enumerator info
✅ Shows 1+ pending riders
✅ Test Rider appears in pending list
```

### Step 6: Test Approval Notification (Device B → Device A)
1. **On Device B**: Find Test Rider in pending list
2. **Tap** "Approve" button
3. **Confirm** approval

**Expected Results - Device B**:
```
✅ "Rider approved successfully" message
✅ Rider moves from pending to approved list
```

**Expected Results - Device A**:
```
📱 IMMEDIATE push notification appears:
   Title: "🎉 Application Approved!"
   Body: "Congratulations Test Rider! Your application has been approved..."

📱 If app is open:
   ✅ Approval success dialog appears
   ✅ "Start Training" button visible
   ✅ Status updates to APPROVED
```

**Check Console Logs**:
```
🖥️ Django Console:
🔔 Rider approval request for rider X
✅ Rider +256700000001 approved
🔔 Approval notification sent to Test Rider

📱 Rider App Console:
🔔 FCM notification received: Application Approved!
🔔 Status changed from PENDING_APPROVAL to APPROVED
🎉 Showing approval success dialog
```

### Step 7: Verify Training Access (Device A)
1. **Tap** "Start Training" in approval dialog
2. **Verify** navigation to HomeScreen
3. **Check** training modules are accessible

---

## ❌ Test Scenario 2: Rejection Flow

### Step 1: Create Another Test Rider
**Repeat Steps 2-4** from Scenario 1 with:
- Phone: `+256700000002`
- Name: `Reject Test`

### Step 2: Test Rejection Notification (Device B → Device A)
1. **On Device B**: Find Reject Test in pending list
2. **Tap** "Reject" button
3. **Enter** rejection reason: `Missing required documents`
4. **Confirm** rejection

**Expected Results - Device A**:
```
📱 IMMEDIATE push notification appears:
   Title: "❌ Application Status Update"
   Body: "Hi Reject Test, your application was not approved. Reason: Missing required documents..."

📱 If app is open:
   ✅ Rejection dialog appears with reason
   ✅ Status updates to REJECTED
   ✅ Contact enumerator message shown
```

---

## 🔍 Advanced Testing

### Test 1: Notification When App is Closed
1. **Close** rider app completely (swipe away from recent apps)
2. **Approve/reject** a rider from admin app
3. **Check** notification appears in notification bar
4. **Tap** notification to open app
5. **Verify** app opens to appropriate screen

### Test 2: Notification When App is in Background
1. **Open** rider app to pending approval screen
2. **Switch** to another app (home screen/other app)
3. **Approve/reject** from admin app
4. **Check** notification appears in notification bar
5. **Return** to rider app and verify status updated

### Test 3: Multiple Riders Testing
1. **Create** 3-5 test riders with different phone numbers
2. **Bulk approve/reject** them from admin app
3. **Verify** all notifications are sent
4. **Check** admin dashboard updates correctly

---

## 🧪 API Testing with Postman/curl

### Test FCM Token Update
```bash
curl -X PUT http://192.168.1.25:8000/api/fcm/update-token/ \
  -H "Authorization: Bearer mock_firebase_token_for_testing_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "fcm_token": "test_fcm_token_12345",
    "phone_number": "+256700000001"
  }'
```

**Expected Response**:
```json
{
  "message": "FCM token updated successfully"
}
```

### Test Rider Approval
```bash
# Get rider ID first
curl -X GET http://192.168.1.25:8000/api/enumerator/pending-riders/ \
  -H "Authorization: Bearer mock_firebase_token_for_testing_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Approve rider (replace 7 with actual ID)
curl -X POST http://192.168.1.25:8000/api/riders/7/approve/ \
  -H "Authorization: Bearer mock_firebase_token_for_testing_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Expected Response**:
```json
{
  "message": "Rider approved successfully",
  "notification_sent": true
}
```

### Test Rider Rejection
```bash
curl -X POST http://192.168.1.25:8000/api/riders/8/reject/ \
  -H "Authorization: Bearer mock_firebase_token_for_testing_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "API test rejection"
  }'
```

---

## 📊 Verification & Monitoring

### Check Database State
```bash
python manage.py shell
>>> from riders.models import Rider
>>> 
>>> # Check riders with FCM tokens
>>> riders_with_tokens = Rider.objects.exclude(fcm_token__isnull=True)
>>> for rider in riders_with_tokens:
...     print(f"{rider.full_name}: {rider.fcm_token[:20]}...")
>>> 
>>> # Check recent status changes
>>> recent_approved = Rider.objects.filter(status='APPROVED').order_by('-approved_at')[:5]
>>> for rider in recent_approved:
...     print(f"✅ {rider.full_name} approved at {rider.approved_at}")
>>> 
>>> # Check rejections with reasons
>>> rejected = Rider.objects.filter(status='REJECTED').exclude(rejection_reason='')
>>> for rider in rejected:
...     print(f"❌ {rider.full_name}: {rider.rejection_reason}")
```

### Monitor Server Logs
```bash
# Watch Django server logs in real-time
tail -f /path/to/your/django.log

# Or watch console output if running in foreground
python manage.py runserver 192.168.1.25:8000
```

**Look for these log patterns**:
```
🔔 FCM Token update request received
✅ FCM token updated for rider +256700000001
🔔 Rider approval request for rider X
✅ Rider +256700000001 approved
🔔 Approval notification sent to Test Rider
```

---

## 🚨 Troubleshooting

### Issue: Notifications Not Received

**Check 1: FCM Token Registration**
```bash
python manage.py shell
>>> from riders.models import Rider
>>> rider = Rider.objects.get(phone_number='+256700000001')
>>> print(f"FCM Token: {rider.fcm_token}")
>>> # Should show a valid token, not None
```

**Check 2: App Permissions**
- Ensure notification permissions are granted
- Check if app is in battery optimization whitelist

**Check 3: Network Connectivity**
- Verify devices can reach Django server
- Check firewall settings

### Issue: Server Errors

**Check Django Logs**:
```bash
# Look for these error patterns
❌ Invalid Firebase token
❌ Rider not found
❌ Error updating FCM token
```

**Common Solutions**:
- Verify phone number format matches database
- Check Firebase token length (should be 100+ characters)
- Ensure rider exists in database

### Issue: Delayed Notifications

**Expected Timing**:
- FCM notifications: 1-3 seconds
- Fallback polling: 5 minutes maximum

**If delayed**:
- Check network connection quality
- Verify FCM service is not throttled
- Restart apps and try again

---

## ✅ Test Checklist

### Basic Functionality
- [ ] App requests notification permissions
- [ ] FCM token generated and stored
- [ ] Token sent to backend successfully
- [ ] Approval notifications received instantly
- [ ] Rejection notifications received with reasons
- [ ] Bulk notifications work for multiple riders

### User Experience
- [ ] Notifications appear in notification bar
- [ ] Tapping notifications opens correct screen
- [ ] In-app dialogs show for status changes
- [ ] Polling frequency reduced (5 min intervals)
- [ ] Battery usage acceptable

### Edge Cases
- [ ] Notifications work when app is closed
- [ ] Notifications work when app is background
- [ ] Multiple rapid status changes handled correctly
- [ ] Network interruptions don't break flow
- [ ] App restart preserves notification setup

### Performance
- [ ] Server polling reduced by 90%
- [ ] Database queries optimized
- [ ] No memory leaks in notification service
- [ ] Error handling graceful

---

## 📈 Success Criteria

**✅ Test Pass Criteria**:
1. **100% automated test success** rate
2. **<3 second notification delivery** time
3. **Correct notification content** for all scenarios
4. **No crashes** during testing
5. **Proper database updates** for all status changes
6. **90% reduction** in server polling requests

**📊 Performance Benchmarks**:
- Notification delivery: 1-3 seconds
- Server requests per user/hour: 12 (down from 120)
- Battery impact: Minimal
- Memory usage: <50MB additional

Run through this testing guide to ensure your FCM push notification system is working perfectly! 🚀