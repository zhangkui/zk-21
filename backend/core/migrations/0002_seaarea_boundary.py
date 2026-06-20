from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seaarea',
            name='boundary',
            field=models.JSONField(blank=True, null=True, verbose_name='边界坐标(多边形点集合)'),
        ),
    ]
