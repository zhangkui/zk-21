from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('inspection', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inspectionrecord',
            name='inspector',
        ),
        migrations.AddField(
            model_name='inspectionrecord',
            name='inspector',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='inspection_records',
                to=settings.AUTH_USER_MODEL,
                verbose_name='巡检人'
            ),
        ),
    ]
