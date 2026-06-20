from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('disease', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diseasereport',
            name='reporter',
        ),
        migrations.RemoveField(
            model_name='mortalityreport',
            name='reporter',
        ),
        migrations.AddField(
            model_name='diseasereport',
            name='reporter',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='disease_reports',
                to=settings.AUTH_USER_MODEL,
                verbose_name='上报人'
            ),
        ),
        migrations.AddField(
            model_name='mortalityreport',
            name='reporter',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='mortality_reports',
                to=settings.AUTH_USER_MODEL,
                verbose_name='上报人'
            ),
        ),
    ]
