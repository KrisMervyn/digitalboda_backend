from django.core.management.base import BaseCommand
from riders.models import Stage


class Command(BaseCommand):
    help = 'Populate sample boda boda stages for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing stages before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('🗑️  Clearing existing stages...')
            Stage.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all existing stages'))

        self.stdout.write('📍 Creating sample boda boda stages...')

        # Sample stages data
        stages_data = [
            {
                'stage_id': 'STAGE001',
                'name': 'Kampala Central Stage',
                'description': 'Main boda boda stage in Kampala central business district',
                'address': 'Buganda Road, Kampala Central',
                'district': 'Kampala',
                'division': 'Central Division',
                'parish': 'Namirembe',
                'latitude': 0.3152,
                'longitude': 32.5827,
                'capacity': 80,
                'training_capacity': 30,
                'stage_chairman': 'John Mukasa',
                'chairman_phone': '+256701234567',
                'status': Stage.ACTIVE
            },
            {
                'stage_id': 'STAGE002',
                'name': 'Nakawa Stage',
                'description': 'Busy stage serving Nakawa and surrounding areas',
                'address': 'Nakawa Market, Kampala',
                'district': 'Kampala',
                'division': 'Nakawa Division',
                'parish': 'Nakawa',
                'latitude': 0.3476,
                'longitude': 32.6131,
                'capacity': 60,
                'training_capacity': 25,
                'stage_chairman': 'Grace Nakamya',
                'chairman_phone': '+256702345678',
                'status': Stage.ACTIVE
            },
            {
                'stage_id': 'STAGE003',
                'name': 'Wandegeya Stage',
                'description': 'Major stage near Makerere University',
                'address': 'Wandegeya Market, Kampala',
                'district': 'Kampala',
                'division': 'Kawempe Division',
                'parish': 'Wandegeya',
                'latitude': 0.3369,
                'longitude': 32.5661,
                'capacity': 70,
                'training_capacity': 28,
                'stage_chairman': 'Peter Ssali',
                'chairman_phone': '+256703456789',
                'status': Stage.ACTIVE
            },
            {
                'stage_id': 'STAGE004',
                'name': 'Ntinda Stage',
                'description': 'Strategic stage serving Ntinda and Kyanja areas',
                'address': 'Ntinda Shopping Complex, Kampala',
                'district': 'Kampala',
                'division': 'Nakawa Division',
                'parish': 'Ntinda',
                'latitude': 0.3667,
                'longitude': 32.6167,
                'capacity': 50,
                'training_capacity': 20,
                'stage_chairman': 'Mary Namutebi',
                'chairman_phone': '+256704567890',
                'status': Stage.ACTIVE
            },
            {
                'stage_id': 'STAGE005',
                'name': 'Bugolobi Stage',
                'description': 'Growing stage in the eastern suburbs',
                'address': 'Bugolobi Trading Centre, Kampala',
                'district': 'Kampala',
                'division': 'Nakawa Division',
                'parish': 'Bugolobi',
                'latitude': 0.3445,
                'longitude': 32.6234,
                'capacity': 45,
                'training_capacity': 18,
                'stage_chairman': 'David Kiwanuka',
                'chairman_phone': '+256705678901',
                'status': Stage.ACTIVE
            },
            {
                'stage_id': 'STAGE006',
                'name': 'Kabalagala Stage',
                'description': 'Popular stage serving the nightlife district',
                'address': 'Kabalagala, Kampala',
                'district': 'Kampala',
                'division': 'Makindye Division',
                'parish': 'Kabalagala',
                'latitude': 0.2944,
                'longitude': 32.5889,
                'capacity': 55,
                'training_capacity': 22,
                'stage_chairman': 'Sarah Namugga',
                'chairman_phone': '+256706789012',
                'status': Stage.ACTIVE
            },
            {
                'stage_id': 'STAGE007',
                'name': 'Entebbe Stage',
                'description': 'Main stage serving Entebbe municipality and airport area',
                'address': 'Entebbe Main Market, Entebbe',
                'district': 'Wakiso',
                'division': 'Entebbe Municipality',
                'parish': 'Entebbe Central',
                'latitude': 0.0474,
                'longitude': 32.4635,
                'capacity': 40,
                'training_capacity': 16,
                'stage_chairman': 'James Kato',
                'chairman_phone': '+256707890123',
                'status': Stage.ACTIVE
            },
            {
                'stage_id': 'STAGE008',
                'name': 'Mukono Stage',
                'description': 'Regional stage serving Mukono town and surrounding areas',
                'address': 'Mukono Central Market, Mukono',
                'district': 'Mukono',
                'division': 'Mukono Municipality',
                'parish': 'Mukono Central',
                'latitude': 0.3533,
                'longitude': 32.7556,
                'capacity': 65,
                'training_capacity': 26,
                'stage_chairman': 'Agnes Nalwoga',
                'chairman_phone': '+256708901234',
                'status': Stage.ACTIVE
            }
        ]

        created_count = 0
        for stage_data in stages_data:
            stage, created = Stage.objects.get_or_create(
                stage_id=stage_data['stage_id'],
                defaults=stage_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✅ Created stage: {stage.stage_id} - {stage.name}')
            else:
                self.stdout.write(f'⏭️  Stage already exists: {stage.stage_id} - {stage.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Successfully created {created_count} new stages out of {len(stages_data)} total stages'
            )
        )
        
        # Display summary
        total_stages = Stage.objects.count()
        active_stages = Stage.objects.filter(status=Stage.ACTIVE).count()
        
        self.stdout.write('\n📊 Stages Summary:')
        self.stdout.write(f'   Total stages: {total_stages}')
        self.stdout.write(f'   Active stages: {active_stages}')
        self.stdout.write(f'   Total capacity: {sum(s.capacity for s in Stage.objects.all())} riders')
        self.stdout.write(f'   Training capacity: {sum(s.training_capacity for s in Stage.objects.all())} participants')