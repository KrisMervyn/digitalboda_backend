# DigitalBoda Backend User Manual

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Authentication System](#authentication-system)
5. [Data Models](#data-models)
6. [API Endpoints](#api-endpoints)
7. [User Roles & Permissions](#user-roles--permissions)
8. [Features](#features)
9. [Security](#security)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

## Overview

DigitalBoda is a Django REST API backend system designed to manage digital literacy training for motorcycle taxi (boda boda) riders in Uganda. The system facilitates rider registration, photo verification, digital literacy training sessions, and administrative oversight.

### Key Features
- Multi-role authentication (Riders, Enumerators, Admins)
- Rider registration and verification
- Photo verification using AI/ML
- Digital literacy training modules
- Push notifications via Firebase
- Real-time dashboard statistics
- Secure ID encryption and data protection

## System Architecture

### Technology Stack
- **Backend**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Token-based authentication
- **Photo Processing**: OpenCV, Face Recognition, PIL
- **OCR**: Tesseract
- **Push Notifications**: Firebase Admin SDK
- **Deployment**: Docker, Gunicorn, Nginx
- **Security**: Cryptography, ID encryption, HTTPS

### Project Structure
```
digitalboda_backend/
├── digitalboda_backend/         # Main project settings
│   ├── settings.py             # Django configuration
│   ├── urls.py                 # Main URL routing
│   └── wsgi.py                 # WSGI application
├── riders/                     # Main app
│   ├── models.py              # Database models
│   ├── views.py               # API views
│   ├── authentication.py      # Auth endpoints
│   ├── photo_views.py         # Photo verification
│   ├── photo_models.py        # Photo-related models
│   ├── encryption.py          # ID encryption utilities
│   ├── urls.py                # App URL routing
│   └── admin.py               # Django admin config
├── media/                     # User uploaded files
├── static/                    # Static files
├── templates/                 # HTML templates
└── manage.py                  # Django management
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis (for background tasks)
- Firebase project with admin SDK

### Environment Setup

1. **Clone and setup virtual environment:**
```bash
git clone <repository_url>
cd digitalboda_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Environment Configuration:**
Create `.env` file with the following variables:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=digitalboda_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Security
ID_ENCRYPTION_KEY=your-encryption-key
ID_HASH_SALT=your-hash-salt

# Firebase (optional for push notifications)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
```

4. **Database Setup:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. **Run Development Server:**
```bash
python manage.py runserver
```

## Authentication System

### Overview
The system uses Django REST Framework's Token Authentication with three user types:

### Authentication Endpoints

#### Rider Login
- **Endpoint**: `POST /api/auth/rider/login/`
- **Authentication**: Phone number only
- **Request**:
```json
{
    "phone_number": "+256123456789"
}
```
- **Response**:
```json
{
    "token": "auth_token_here",
    "rider_id": 1,
    "unique_id": "RID-2024-0001",
    "full_name": "John Doe",
    "status": "APPROVED",
    "points": 150
}
```

#### Enumerator Login
- **Endpoint**: `POST /api/auth/enumerator/login/`
- **Authentication**: Unique ID + password
- **Request**:
```json
{
    "unique_id": "EN-2024-0001",
    "password": "password123"
}
```

#### Admin Login
- **Endpoint**: `POST /api/auth/admin/login/`
- **Authentication**: Username + password
- **Request**:
```json
{
    "username": "admin",
    "password": "admin_password"
}
```

#### Token Verification
- **Endpoint**: `GET /api/auth/verify-token/`
- **Headers**: `Authorization: Token your_token_here`

#### Logout
- **Endpoint**: `POST /api/auth/logout/`
- **Headers**: `Authorization: Token your_token_here`

## Data Models

### Core Models

#### Rider Model
Represents motorcycle taxi drivers in the system.

**Key Fields:**
- `unique_id`: Auto-generated format "RID-YYYY-NNNN"
- `first_name`, `last_name`: Personal information
- `phone_number`: Primary identifier (unique)
- `status`: PENDING, APPROVED, REJECTED, SUSPENDED
- `points`: Digital literacy points earned
- `current_stage`: Training progression stage
- `enumerator_id_input`: Assigned enumerator reference

**Status Flow:**
PENDING → APPROVED/REJECTED → SUSPENDED (if needed)

#### Enumerator Model
Field agents who conduct training and verify riders.

**Key Fields:**
- `unique_id`: Auto-generated format "EN-YYYY-NNNN"
- `user`: OneToOne relationship with Django User
- `status`: ACTIVE, INACTIVE, SUSPENDED
- `location`, `assigned_region`: Geographic assignment
- `phone_number`: Contact information

#### Digital Literacy Models

**DigitalLiteracyModule:**
- Training modules with session counts
- Prerequisites and completion tracking

**TrainingSchedule:**
- Scheduled training sessions
- Date, time, location, capacity management

**SessionAttendance:**
- Tracks rider attendance at sessions
- Points allocation and completion status

**Achievement:**
- Badges and certificates system
- Progress milestones

**TrainingNotification:**
- Push notification management
- Read/unread status tracking

### Photo Verification Models

#### PhotoVerificationResult
Stores AI-powered photo verification results.

**Key Fields:**
- `rider`: Foreign key to Rider
- `verification_status`: PENDING, VERIFIED, FAILED
- `confidence_score`: ML confidence level
- `face_detected`: Boolean face detection result
- `id_document_detected`: Document detection result
- `face_match_score`: Similarity score between photos

## API Endpoints

### Rider Endpoints

#### Registration
```
POST /api/register/
Content-Type: application/json

{
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+256123456789",
    "age": 25,
    "gender": "M",
    "enumerator_id_input": "EN-2024-0001",
    "location": "Kampala"
}
```

#### Profile
```
GET /api/profile/{phone_number}/
Authorization: Token your_token_here
```

#### Lessons
```
GET /api/lessons/
Authorization: Token your_token_here
```

#### Onboarding
```
POST /api/onboarding/submit/
Authorization: Token your_token_here
Content-Type: multipart/form-data

{
    "profile_photo": [file],
    "id_document_photo": [file],
    "additional_info": "Additional details"
}
```

### Admin Endpoints

#### Dashboard Stats
```
GET /api/admin/dashboard/stats/
Authorization: Token admin_token_here

Response:
{
    "total_riders": 150,
    "pending_riders": 25,
    "approved_riders": 120,
    "rejected_riders": 5,
    "total_enumerators": 10,
    "active_enumerators": 8
}
```

#### Pending Riders
```
GET /api/admin/pending-riders/
Authorization: Token admin_token_here

Response:
{
    "riders": [
        {
            "id": 1,
            "unique_id": "RID-2024-0001",
            "full_name": "John Doe",
            "phone_number": "+256123456789",
            "status": "PENDING",
            "submitted_at": "2024-01-15T10:30:00Z",
            "enumerator_id_input": "EN-2024-0001"
        }
    ]
}
```

#### Approve/Reject Riders
```
POST /api/admin/rider/{rider_id}/approve/
POST /api/admin/rider/{rider_id}/reject/
Authorization: Token admin_token_here

{
    "reason": "Approval/rejection reason"
}
```

### Enumerator Endpoints

#### Assigned Riders
```
GET /api/enumerator/assigned-riders/
Authorization: Token enumerator_token_here
```

#### Pending Riders
```
GET /api/enumerator/pending-riders/
Authorization: Token enumerator_token_here
```

#### Dashboard Stats
```
GET /api/enumerator/dashboard/stats/
Authorization: Token enumerator_token_here
```

### Digital Literacy Endpoints

#### Training Modules
```
GET /api/digital-literacy/modules/
Authorization: Token your_token_here

Response:
{
    "modules": [
        {
            "id": 1,
            "name": "Basic Phone Skills",
            "description": "Introduction to smartphone usage",
            "session_count": 3,
            "prerequisites": []
        }
    ]
}
```

#### Register for Session
```
POST /api/digital-literacy/register-session/
Authorization: Token rider_token_here

{
    "schedule_id": 1
}
```

#### Record Attendance
```
POST /api/digital-literacy/register-attendance/
Authorization: Token rider_token_here

{
    "schedule_id": 1,
    "stage_id": "STAGE001"
}
```

#### Progress Tracking
```
GET /api/digital-literacy/rider-progress/
Authorization: Token rider_token_here

Response:
{
    "total_points": 150,
    "completed_modules": 2,
    "current_stage": "INTERMEDIATE",
    "achievements": [
        {
            "name": "First Steps",
            "description": "Completed first training session",
            "earned_at": "2024-01-15T14:30:00Z"
        }
    ]
}
```

### Photo Verification Endpoints

#### Verify Photos
```
POST /api/riders/{rider_id}/verify-photos/
Authorization: Token admin_token_here

Response:
{
    "verification_id": 1,
    "status": "VERIFIED",
    "confidence_score": 0.95,
    "face_detected": true,
    "id_document_detected": true,
    "face_match_score": 0.92
}
```

#### Verification Report
```
GET /api/riders/{rider_id}/photo-verification-report/
Authorization: Token admin_token_here
```

### Push Notification Endpoints

#### Update FCM Token
```
POST /api/fcm/update-token/
Authorization: Token your_token_here

{
    "fcm_token": "firebase_token_here",
    "device_type": "android"
}
```

## User Roles & Permissions

### Rider Permissions
- Register and update profile
- View training modules and schedules
- Register for training sessions
- Record attendance
- View progress and achievements
- Receive push notifications

### Enumerator Permissions
- View assigned riders
- Approve/reject rider registrations (first level)
- Conduct photo verification
- Schedule training sessions
- View enumerator dashboard
- Change password

### Admin Permissions
- Full system access
- Manage all riders and enumerators
- Final approval/rejection of riders
- View comprehensive statistics
- System configuration
- User management

## Features

### 1. Rider Registration Flow
1. Rider submits registration via mobile app
2. Enumerator receives notification
3. Enumerator conducts initial verification
4. Admin performs final approval
5. Rider receives notification of status
6. Approved riders can access training

### 2. Photo Verification System
- AI-powered face detection
- ID document verification
- Face matching between profile and ID photos
- Confidence scoring
- Manual override capabilities

### 3. Digital Literacy Training
- Modular training system
- Progressive stages (BEGINNER → INTERMEDIATE → ADVANCED)
- Point-based rewards system
- Achievement badges and certificates
- Attendance tracking with location verification

### 4. Push Notification System
- Firebase Cloud Messaging integration
- Targeted notifications by user type
- Training reminders and updates
- Status change notifications

### 5. Security Features
- Token-based authentication
- ID field encryption
- Secure hash generation
- HTTPS enforcement in production
- Rate limiting
- CORS protection

## Security

### Data Protection
- **ID Encryption**: National IDs and sensitive data are encrypted
- **Secure Storage**: Profile and ID document photos stored securely
- **Access Logging**: ID access events are logged for audit
- **Hash Salting**: Secure hash generation with custom salts

### Authentication Security
- Token-based authentication
- Password validation
- Session management
- Rate limiting on authentication endpoints

### Production Security Headers
- SSL redirect enforcement
- Secure cookie settings
- XSS protection
- Content type validation
- HSTS headers

## Deployment

### Docker Deployment
```bash
# Build image
docker build -t digitalboda-backend .

# Run with docker-compose
docker-compose up -d
```

### Environment Variables for Production
```env
DJANGO_ENV=production
SECRET_KEY=production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database (use production values)
DB_NAME=prod_digitalboda_db
DB_USER=prod_user
DB_PASSWORD=secure_password
DB_HOST=db.yourdomain.com
DB_PORT=5432

# Security
SECURE_SSL_REDIRECT=True
ID_ENCRYPTION_KEY=production-encryption-key
```

### Gunicorn Configuration
The system includes `gunicorn.conf.py` with optimized settings for production deployment.

## Troubleshooting

### Common Issues

#### Database Connection Errors
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists and user has permissions

#### Authentication Failures
- Verify token format: `Authorization: Token your_token_here`
- Check token expiration
- Ensure user status is active/approved

#### Photo Upload Issues
- Check file size limits (10MB default)
- Verify media directory permissions
- Ensure PIL/OpenCV dependencies are installed

#### Push Notification Problems
- Verify Firebase credentials path
- Check FCM token validity
- Confirm Firebase project configuration

### Logs and Monitoring
- Application logs: Check Django logging configuration
- Database logs: Monitor PostgreSQL query logs
- Error tracking: Configure Sentry or similar service
- Performance monitoring: Use APM tools for production

### Support Commands
```bash
# Check system status
python manage.py check

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Test database connection
python manage.py dbshell

# Run tests
python manage.py test
```

## API Testing

### Using curl
```bash
# Login as rider
curl -X POST http://192.168.1.25:8000/api/auth/rider/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+256123456789"}'

# Get profile
curl -X GET http://192.168.1.25:8000/api/profile/+256123456789/ \
  -H "Authorization: Token your_token_here"
```

### Using Python requests
```python
import requests

# Login
response = requests.post(
    'http://192.168.1.25:8000/api/auth/rider/login/',
    json={'phone_number': '+256123456789'}
)
token = response.json()['token']

# Get lessons
response = requests.get(
    'http://192.168.1.25:8000/api/lessons/',
    headers={'Authorization': f'Token {token}'}
)
```

---

For additional support or questions, please refer to the project documentation or contact the development team.