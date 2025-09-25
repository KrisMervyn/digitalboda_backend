from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from riders.models import (
    DigitalLiteracyModule, TrainingSession, SessionSchedule,
    Enumerator
)


class Command(BaseCommand):
    help = 'Populate sample digital literacy training data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing training data before populating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing training data...')
            DigitalLiteracyModule.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Existing data cleared.'))

        self.stdout.write('🚀 Creating digital literacy training modules...')
        
        # Create training modules
        modules_data = [
            {
                'title': 'Smartphone Basics',
                'description': 'Master the fundamentals of smartphone operation, navigation, and essential features for daily digital activities.',
                'icon': '📱',
                'order': 1,
                'points_value': 150,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Getting Started with Your Phone',
                        'description': 'Learn to power on, unlock, and navigate your smartphone interface',
                        'duration_hours': 1.5,
                        'points_value': 30,
                        'learning_objectives': [
                            'Power on and unlock smartphone',
                            'Navigate home screen and menus',
                            'Understand basic touch gestures',
                            'Customize basic settings'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Charger',
                            'Practice cards with common icons'
                        ]
                    },
                    {
                        'session_number': 2,
                        'title': 'Making Calls and Contacts',
                        'description': 'Master voice calling, contact management, and emergency features',
                        'duration_hours': 1.0,
                        'points_value': 25,
                        'learning_objectives': [
                            'Make and receive voice calls',
                            'Add and organize contacts',
                            'Use emergency calling features',
                            'Manage call history'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'SIM card with airtime',
                            'Emergency contact list'
                        ]
                    },
                    {
                        'session_number': 3,
                        'title': 'Text Messaging Essentials',
                        'description': 'Send and receive SMS messages, manage conversations',
                        'duration_hours': 1.0,
                        'points_value': 25,
                        'learning_objectives': [
                            'Compose and send SMS messages',
                            'Read and reply to messages',
                            'Organize message conversations',
                            'Use predictive text input'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Practice message templates',
                            'Contact for messaging practice'
                        ]
                    },
                    {
                        'session_number': 4,
                        'title': 'Apps and App Store',
                        'description': 'Download, install, and manage mobile applications',
                        'duration_hours': 1.5,
                        'points_value': 35,
                        'learning_objectives': [
                            'Navigate Google Play Store',
                            'Download and install apps',
                            'Update and uninstall apps',
                            'Understand app permissions'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Google account',
                            'Wi-Fi connection',
                            'List of recommended apps'
                        ]
                    },
                    {
                        'session_number': 5,
                        'title': 'Photos and Camera',
                        'description': 'Take photos, manage gallery, and share images',
                        'duration_hours': 1.0,
                        'points_value': 35,
                        'learning_objectives': [
                            'Take and review photos',
                            'Organize photo gallery',
                            'Share photos via messaging',
                            'Delete and manage storage'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Good lighting for photos',
                            'Objects for photo practice'
                        ]
                    }
                ]
            },
            {
                'title': 'Mobile Banking & Digital Payments',
                'description': 'Learn secure mobile money transactions, banking apps, and digital payment safety practices.',
                'icon': '💳',
                'order': 2,
                'points_value': 200,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Mobile Money Basics',
                        'description': 'Introduction to mobile money services and basic transactions',
                        'duration_hours': 2.0,
                        'points_value': 50,
                        'learning_objectives': [
                            'Understand mobile money services',
                            'Register for mobile money account',
                            'Send and receive money',
                            'Check account balance'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'National ID',
                            'Mobile money agent location',
                            'Practice transaction amounts'
                        ]
                    },
                    {
                        'session_number': 2,
                        'title': 'Digital Banking Safety',
                        'description': 'Security practices for safe mobile banking and fraud prevention',
                        'duration_hours': 1.5,
                        'points_value': 40,
                        'learning_objectives': [
                            'Recognize fraud attempts',
                            'Create secure PINs',
                            'Safely use banking apps',
                            'Protect personal information'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Banking app examples',
                            'Security scenario cards',
                            'PIN creation guidelines'
                        ]
                    },
                    {
                        'session_number': 3,
                        'title': 'Bill Payments and Utilities',
                        'description': 'Pay bills, buy airtime, and manage utility payments digitally',
                        'duration_hours': 1.5,
                        'points_value': 45,
                        'learning_objectives': [
                            'Pay electricity bills via mobile',
                            'Purchase airtime and data',
                            'Pay water and other utilities',
                            'Keep transaction records'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Utility bill examples',
                            'Account numbers for practice',
                            'Transaction history tracking sheet'
                        ]
                    },
                    {
                        'session_number': 4,
                        'title': 'Advanced Banking Features',
                        'description': 'Loans, savings, and investment options through mobile banking',
                        'duration_hours': 2.0,
                        'points_value': 65,
                        'learning_objectives': [
                            'Explore mobile loan options',
                            'Set up automatic savings',
                            'Understand investment products',
                            'Plan financial goals digitally'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Banking apps with full features',
                            'Financial planning worksheets',
                            'Investment option comparisons'
                        ]
                    }
                ]
            },
            {
                'title': 'Digital Marketing for Boda Boda',
                'description': 'Promote your boda boda services using social media, online platforms, and digital marketing strategies.',
                'icon': '📈',
                'order': 3,
                'points_value': 250,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Social Media for Business',
                        'description': 'Create business profiles on Facebook, WhatsApp Business, and Instagram',
                        'duration_hours': 2.0,
                        'points_value': 60,
                        'learning_objectives': [
                            'Create Facebook business page',
                            'Set up WhatsApp Business',
                            'Post engaging business content',
                            'Interact with customers online'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Business photos and info',
                            'Wi-Fi connection',
                            'Sample social media posts'
                        ]
                    },
                    {
                        'session_number': 2,
                        'title': 'Online Customer Service',
                        'description': 'Manage customer inquiries and bookings through digital channels',
                        'duration_hours': 1.5,
                        'points_value': 45,
                        'learning_objectives': [
                            'Respond to customer messages',
                            'Handle booking requests',
                            'Manage customer complaints',
                            'Build customer relationships'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Customer service script templates',
                            'Booking management system',
                            'Response time guidelines'
                        ]
                    },
                    {
                        'session_number': 3,
                        'title': 'Digital Advertising',
                        'description': 'Create and manage online advertisements for your boda boda services',
                        'duration_hours': 2.0,
                        'points_value': 70,
                        'learning_objectives': [
                            'Design simple online ads',
                            'Target local customers',
                            'Track ad performance',
                            'Optimize advertising budget'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Business photos and videos',
                            'Advertising budget planning sheet',
                            'Local market research data'
                        ]
                    },
                    {
                        'session_number': 4,
                        'title': 'Building Online Reputation',
                        'description': 'Manage online reviews, build trust, and maintain digital presence',
                        'duration_hours': 1.5,
                        'points_value': 50,
                        'learning_objectives': [
                            'Encourage positive reviews',
                            'Respond to customer feedback',
                            'Build trust and credibility',
                            'Maintain consistent online presence'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Review platform examples',
                            'Response templates for reviews',
                            'Brand consistency guidelines'
                        ]
                    },
                    {
                        'session_number': 5,
                        'title': 'Business Analytics and Growth',
                        'description': 'Track business performance and plan growth using digital tools',
                        'duration_hours': 1.5,
                        'points_value': 25,
                        'learning_objectives': [
                            'Track social media metrics',
                            'Analyze customer behavior',
                            'Plan business growth strategies',
                            'Use data for decision making'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Analytics apps and tools',
                            'Business performance tracking sheets',
                            'Growth planning templates'
                        ]
                    }
                ]
            },
            {
                'title': 'Internet and Online Safety',
                'description': 'Navigate the internet safely, recognize online threats, and protect personal information.',
                'icon': '🔒',
                'order': 4,
                'points_value': 180,
                'sessions': [
                    {
                        'session_number': 1,
                        'title': 'Internet Basics',
                        'description': 'Introduction to web browsing, search engines, and basic internet navigation',
                        'duration_hours': 1.5,
                        'points_value': 35,
                        'learning_objectives': [
                            'Open and use web browsers',
                            'Perform basic internet searches',
                            'Navigate between web pages',
                            'Bookmark useful websites'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Wi-Fi or data connection',
                            'List of useful websites',
                            'Search practice exercises'
                        ]
                    },
                    {
                        'session_number': 2,
                        'title': 'Email and Communication',
                        'description': 'Create and manage email accounts, send messages, and handle attachments',
                        'duration_hours': 2.0,
                        'points_value': 50,
                        'learning_objectives': [
                            'Create email account',
                            'Send and receive emails',
                            'Organize email folders',
                            'Handle email attachments'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Internet connection',
                            'Email practice templates',
                            'File attachment examples'
                        ]
                    },
                    {
                        'session_number': 3,
                        'title': 'Online Safety and Privacy',
                        'description': 'Protect personal information and recognize online threats',
                        'duration_hours': 1.5,
                        'points_value': 45,
                        'learning_objectives': [
                            'Create strong passwords',
                            'Recognize phishing attempts',
                            'Protect personal information',
                            'Use secure websites'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Password manager app',
                            'Phishing example scenarios',
                            'Privacy settings checklists'
                        ]
                    },
                    {
                        'session_number': 4,
                        'title': 'Government and Business Services',
                        'description': 'Access online government services and business platforms',
                        'duration_hours': 1.5,
                        'points_value': 50,
                        'learning_objectives': [
                            'Access government online services',
                            'Use business platforms',
                            'Submit digital applications',
                            'Track service requests'
                        ],
                        'required_materials': [
                            'Android smartphone',
                            'Government service websites',
                            'Digital ID or account credentials',
                            'Service application examples'
                        ]
                    }
                ]
            }
        ]

        # Create modules and sessions
        for module_data in modules_data:
            sessions_data = module_data.pop('sessions')
            
            module = DigitalLiteracyModule.objects.create(**module_data)
            self.stdout.write(f'✅ Created module: {module.title}')
            
            total_duration = 0
            for session_data in sessions_data:
                session = TrainingSession.objects.create(
                    module=module,
                    **session_data
                )
                total_duration += float(session_data['duration_hours'])
                self.stdout.write(f'   📚 Created session: {session.title}')
            
            # Update module totals
            module.session_count = len(sessions_data)
            module.total_duration_hours = total_duration
            module.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Successfully created {DigitalLiteracyModule.objects.count()} '
                f'training modules with {TrainingSession.objects.count()} sessions!'
            )
        )
        
        # Create some sample scheduled sessions if we have trainers
        enumerators = Enumerator.objects.filter(status='ACTIVE')[:3]
        if enumerators.exists():
            self.stdout.write('\n📅 Creating sample scheduled sessions...')
            
            # Sample locations in Kampala
            locations = [
                {
                    'name': 'Nakawa Stage',
                    'address': 'Nakawa Division, Kampala',
                    'lat': 0.3476, 'lng': 32.6131
                },
                {
                    'name': 'Wandegeya Stage',
                    'address': 'Wandegeya, Kampala',  
                    'lat': 0.3301, 'lng': 32.5731
                },
                {
                    'name': 'Ntinda Stage',
                    'address': 'Ntinda, Kampala',
                    'lat': 0.3641, 'lng': 32.6176
                }
            ]
            
            # Create schedules for the first few sessions
            sessions = TrainingSession.objects.filter(
                module__order__lte=2, session_number__lte=2
            )[:6]
            
            for i, session in enumerate(sessions):
                location = locations[i % len(locations)]
                trainer = enumerators[i % len(enumerators)]
                
                # Schedule sessions over the next few weeks
                schedule_date = timezone.now() + timedelta(days=(i * 3) + 1)
                
                schedule = SessionSchedule.objects.create(
                    session=session,
                    trainer=trainer,
                    scheduled_date=schedule_date,
                    location_name=location['name'],
                    location_address=location['address'],
                    gps_latitude=location['lat'],
                    gps_longitude=location['lng'],
                    capacity=25,
                    status='SCHEDULED'
                )
                
                self.stdout.write(
                    f'   📅 Scheduled: {session.title} with {trainer.full_name} '
                    f'at {location["name"]} on {schedule_date.strftime("%Y-%m-%d")}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🚀 Training data population complete! '
                'You can now manage training content through the Django admin interface.'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\n💡 Access the admin at: http://192.168.1.25:8000/admin/'
            )
        )