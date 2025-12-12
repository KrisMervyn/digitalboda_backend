# Generated manually for account deletion feature (Google Play Store compliance)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('riders', '0019_auto_20251013_0840'),
    ]

    operations = [
        migrations.AddField(
            model_name='rider',
            name='deletion_requested_at',
            field=models.DateTimeField(blank=True, help_text='When account deletion was requested', null=True),
        ),
        migrations.AddField(
            model_name='rider',
            name='deletion_reason',
            field=models.TextField(blank=True, help_text="User's reason for deletion"),
        ),
        # Add DELETION_PENDING to status choices
        migrations.AlterField(
            model_name='rider',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('REGISTERED', 'Registered'),
                    ('ONBOARDING', 'In Onboarding'),
                    ('PENDING_APPROVAL', 'Pending Approval'),
                    ('APPROVED', 'Approved'),
                    ('REJECTED', 'Rejected'),
                    ('SUSPENDED', 'Suspended'),
                    ('DELETION_PENDING', 'Deletion Pending'),
                ],
                default='REGISTERED'
            ),
        ),
    ]
