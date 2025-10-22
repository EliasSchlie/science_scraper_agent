# Generated migration for adding logs field to ScraperJob

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scraperjob',
            name='logs',
            field=models.TextField(blank=True, default=''),
        ),
    ]

