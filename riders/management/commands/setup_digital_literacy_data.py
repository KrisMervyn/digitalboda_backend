from django.core.management.base import BaseCommand
from django.utils import timezone
from riders.models import (
    DigitalLiteracyModule, TrainingSession, Enumerator, SessionSchedule
)
from datetime import datetime, timedelta
import json


class Command(BaseCommand):
    help = 'Set up digital literacy training modules and sessions with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up Digital Literacy Training Data...'))
        
        # Clear existing data
        DigitalLiteracyModule.objects.all().delete()
        
        # Create the 4 core modules
        modules_data = [
            {
                'title': 'Smartphone Basics & Digital Communication',
                'description': 'Learn fundamental smartphone navigation, digital communication tools, and online safety practices essential for modern boda boda operations.',
                'session_count': 4,
                'total_duration_hours': 8.0,
                'points_value': 400,
                'icon': '📱',
                'order': 1,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Smartphone Navigation & Basic Functions',
                        'description': 'Master the basics of smartphone operation including touch navigation, app opening, settings, and basic troubleshooting.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Navigate smartphone interface confidently',
                            'Open and close applications',
                            'Adjust basic settings (volume, brightness, wifi)',
                            'Understand app icons and notifications'
                        ],
                        'required_materials': ['Smartphone', 'Internet connection'],
                        'points_value': 100
                    },
                    {
                        'session_number': 2,
                        'title': 'WhatsApp & Digital Messaging',
                        'description': 'Learn to use WhatsApp for customer communication, group coordination, and business messaging.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Set up WhatsApp profile and privacy settings',
                            'Send text, voice, and image messages',
                            'Use WhatsApp for customer updates',
                            'Manage group communications'
                        ],
                        'required_materials': ['Smartphone with WhatsApp', 'Phone number'],
                        'points_value': 100
                    },
                    {
                        'session_number': 3,
                        'title': 'Internet Browsing & Information Search',
                        'description': 'Develop skills to search for information online, use maps, and browse websites safely.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Use Google search effectively',
                            'Browse websites safely',
                            'Find location information online',
                            'Identify reliable vs unreliable sources'
                        ],
                        'required_materials': ['Smartphone', 'Internet data'],
                        'points_value': 100
                    },
                    {
                        'session_number': 4,
                        'title': 'Digital Safety & Privacy Fundamentals',
                        'description': 'Learn essential digital safety practices, password management, and privacy protection.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Create strong passwords',
                            'Recognize and avoid scams',
                            'Manage app permissions',
                            'Protect personal information online'
                        ],
                        'required_materials': ['Smartphone', 'Notebook for password tracking'],
                        'points_value': 100
                    }
                ]
            },
            {
                'title': 'Mobile Money & Digital Financial Services',
                'description': 'Master mobile money platforms, digital payments, and financial security practices to enhance your business transactions.',
                'session_count': 3,
                'total_duration_hours': 7.5,
                'points_value': 350,
                'icon': '💰',
                'order': 2,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Mobile Money Platform Setup & Navigation',
                        'description': 'Set up and navigate MTN Mobile Money, Airtel Money, and other mobile money platforms.',
                        'duration_hours': 2.5,
                        'learning_objectives': [
                            'Register for mobile money services',
                            'Navigate mobile money menus',
                            'Understand transaction limits',
                            'Set up and use mobile money PINs'
                        ],
                        'required_materials': ['Smartphone', 'National ID', 'SIM card'],
                        'points_value': 125
                    },
                    {
                        'session_number': 2,
                        'title': 'Digital Payments & Transfers',
                        'description': 'Learn to send money, receive payments, and handle customer transactions digitally.',
                        'duration_hours': 2.5,
                        'learning_objectives': [
                            'Send and receive money via mobile money',
                            'Pay bills and purchase airtime',
                            'Handle customer digital payments',
                            'Track transaction history'
                        ],
                        'required_materials': ['Active mobile money account', 'Small amounts for practice'],
                        'points_value': 125
                    },
                    {
                        'session_number': 3,
                        'title': 'Financial Security & Fraud Prevention',
                        'description': 'Understand digital financial security, recognize fraud attempts, and protect your mobile money accounts.',
                        'duration_hours': 2.5,
                        'learning_objectives': [
                            'Recognize mobile money fraud attempts',
                            'Secure mobile money accounts',
                            'Report fraudulent activities',
                            'Understand terms and conditions'
                        ],
                        'required_materials': ['Smartphone', 'Mobile money account'],
                        'points_value': 100
                    }
                ]
            },
            {
                'title': 'Ride-Hailing Apps & GPS Navigation',
                'description': 'Learn to use ride-hailing applications, GPS navigation systems, and digital trip management for enhanced customer service.',
                'session_count': 3,
                'total_duration_hours': 6.0,
                'points_value': 300,
                'icon': '🛵',
                'order': 3,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Ride-Hailing App Registration & Setup',
                        'description': 'Register as a driver on major ride-hailing platforms and complete profile setup.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Download and install ride-hailing apps',
                            'Complete driver registration process',
                            'Upload required documents',
                            'Set up payment and payout methods'
                        ],
                        'required_materials': ['Smartphone', 'Driver license', 'Vehicle registration'],
                        'points_value': 100
                    },
                    {
                        'session_number': 2,
                        'title': 'GPS Navigation & Map Reading',
                        'description': 'Master GPS navigation, map reading, and route optimization using smartphone applications.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Use Google Maps for navigation',
                            'Find optimal routes',
                            'Use voice navigation',
                            'Share location with customers'
                        ],
                        'required_materials': ['Smartphone', 'Google Maps app', 'Internet data'],
                        'points_value': 100
                    },
                    {
                        'session_number': 3,
                        'title': 'Trip Management & Customer Communication',
                        'description': 'Learn to manage rides, communicate with customers, and handle trip completion through apps.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Accept and manage ride requests',
                            'Communicate with customers via app',
                            'Handle trip modifications',
                            'Complete trips and process payments'
                        ],
                        'required_materials': ['Active ride-hailing app account', 'Smartphone'],
                        'points_value': 100
                    }
                ]
            },
            {
                'title': 'Digital Business Skills & Online Presence',
                'description': 'Develop digital marketing skills, create an online business presence, and use digital tools for business growth and customer management.',
                'session_count': 4,
                'total_duration_hours': 8.0,
                'points_value': 400,
                'icon': '💼',
                'order': 4,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Social Media for Business Promotion',
                        'description': 'Create and manage business profiles on social media platforms to attract customers.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Create professional Facebook business page',
                            'Post engaging content about services',
                            'Respond to customer inquiries',
                            'Use hashtags effectively'
                        ],
                        'required_materials': ['Smartphone', 'Facebook app', 'Business photos'],
                        'points_value': 100
                    },
                    {
                        'session_number': 2,
                        'title': 'Online Customer Service Excellence',
                        'description': 'Master digital customer service techniques and professional online communication.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Write professional messages to customers',
                            'Handle customer complaints online',
                            'Maintain positive online reputation',
                            'Use customer feedback for improvement'
                        ],
                        'required_materials': ['Smartphone', 'Social media accounts'],
                        'points_value': 100
                    },
                    {
                        'session_number': 3,
                        'title': 'Digital Marketing & Customer Acquisition',
                        'description': 'Learn digital marketing basics to grow your customer base and increase bookings.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Create promotional content',
                            'Use WhatsApp Status for marketing',
                            'Build customer referral networks',
                            'Track marketing effectiveness'
                        ],
                        'required_materials': ['Smartphone', 'WhatsApp', 'Camera for content'],
                        'points_value': 100
                    },
                    {
                        'session_number': 4,
                        'title': 'Digital Record Keeping & Business Analytics',
                        'description': 'Use digital tools for tracking income, expenses, and analyzing business performance.',
                        'duration_hours': 2.0,
                        'learning_objectives': [
                            'Track daily income using smartphone apps',
                            'Record expenses digitally',
                            'Analyze business patterns',
                            'Set and track financial goals'
                        ],
                        'required_materials': ['Smartphone', 'Spreadsheet or tracking app'],
                        'points_value': 100
                    }
                ]
            }
        ]
        
        # Create modules and sessions
        for module_data in modules_data:
            sessions_data = module_data.pop('sessions')
            
            module = DigitalLiteracyModule.objects.create(**module_data)
            self.stdout.write(f'Created module: {module.title}')
            
            # Create sessions for this module
            for session_data in sessions_data:
                session = TrainingSession.objects.create(
                    module=module,
                    **session_data
                )
                self.stdout.write(f'  Created session: {session.title}')
        
        # Create sample schedules for the first few sessions if we have trainers
        trainers = Enumerator.objects.filter(status=Enumerator.ACTIVE)[:2]
        if trainers.exists():
            self.stdout.write(self.style.WARNING('Creating sample session schedules...'))
            
            # Get first few training sessions
            sessions = TrainingSession.objects.all()[:4]
            
            # Sample locations in Kampala
            locations = [
                {
                    'name': 'Kampala Community Center',
                    'address': 'Plot 123, Kampala Road, Central Division, Kampala',
                    'lat': 0.3476,
                    'lng': 32.5825
                },
                {
                    'name': 'Makerere University ICT Lab',
                    'address': 'Makerere University, Kampala',
                    'lat': 0.3354,
                    'lng': 32.5656
                },
                {
                    'name': 'Nakawa Digital Hub',
                    'address': 'Industrial Area, Nakawa Division, Kampala', 
                    'lat': 0.3354,
                    'lng': 32.6149
                }
            ]
            
            base_date = timezone.now() + timedelta(days=7)  # Start next week
            
            for i, session in enumerate(sessions):
                for j, trainer in enumerate(trainers):
                    location = locations[i % len(locations)]
                    schedule_date = base_date + timedelta(days=i*2, hours=j*3)
                    
                    schedule = SessionSchedule.objects.create(
                        session=session,
                        trainer=trainer,
                        scheduled_date=schedule_date,
                        location_name=location['name'],
                        location_address=location['address'],
                        gps_latitude=location['lat'],
                        gps_longitude=location['lng'],
                        capacity=20,
                        status='SCHEDULED'
                    )
                    
                    self.stdout.write(f'  Created schedule: {schedule}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {DigitalLiteracyModule.objects.count()} modules '
                f'with {TrainingSession.objects.count()} sessions total!'
            )
        )