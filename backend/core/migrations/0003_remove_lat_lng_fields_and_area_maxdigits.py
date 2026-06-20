from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seaarea_boundary'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='seaarea',
            name='lat_min',
        ),
        migrations.RemoveField(
            model_name='seaarea',
            name='lat_max',
        ),
        migrations.RemoveField(
            model_name='seaarea',
            name='lng_min',
        ),
        migrations.RemoveField(
            model_name='seaarea',
            name='lng_max',
        ),
        migrations.AlterField(
            model_name='seaarea',
            name='area',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='面积(公顷)'),
        ),
    ]
