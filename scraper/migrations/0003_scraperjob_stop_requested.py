from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0002_scraperjob_logs'),
    ]

    operations = [
        migrations.AddField(
            model_name='scraperjob',
            name='stop_requested',
            field=models.BooleanField(default=False),
        ),
    ]


