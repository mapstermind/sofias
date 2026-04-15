from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_role_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='role',
            options={'managed': False, 'permissions': [
                ('can_manage_surveys', 'Can manage surveys'),
                ('can_view_dashboard', 'Can view dashboard'),
                ('can_view_insights', 'Can view insights'),
                ('can_take_assigned_surveys', 'Can take assigned surveys'),
                ('can_manage_employees', 'Can manage employees'),
                ('can_view_submissions', 'Can view submissions'),
            ]},
        ),
    ]
