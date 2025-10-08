# Generated migration for PIN and age bracket fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('riders', '0012_notificationschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='rider',
            name='age_bracket',
            field=models.CharField(
                blank=True,
                choices=[
                    ('18-23', '18-23 (Young Adult)'),
                    ('24-29', '24-29 (Early Career)'),
                    ('30-35', '30-35 (Mid Career)'),
                    ('36-41', '36-41 (Experienced)'),
                    ('42-47', '42-47 (Senior)'),
                    ('48-53', '48-53 (Veteran)'),
                    ('54-59', '54-59 (Pre-retirement)'),
                    ('60-65', '60-65 (Senior Citizen)'),
                    ('66+', '66+ (Elder)'),
                ],
                help_text='Age bracket instead of exact age for privacy',
                max_length=10,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='rider',
            name='pin_hash',
            field=models.CharField(
                blank=True,
                help_text='Hashed PIN for quick authentication',
                max_length=128,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='rider',
            name='pin_set_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rider',
            name='pin_last_used',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rider',
            name='failed_pin_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='rider',
            name='pin_locked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='rider',
            name='age',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='DEPRECATED: Keep for migration - use age_bracket instead'
            ),
        ),
    ]