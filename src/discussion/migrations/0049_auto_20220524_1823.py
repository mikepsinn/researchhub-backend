# Generated by Django 2.2 on 2022-05-24 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussion', '0048_auto_20220517_1322'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flag',
            name='reason_choice',
            field=models.CharField(blank=True, choices=[('ABUSIVE_OR_RUDE', 'ABUSIVE_OR_RUDE'), ('COPYRIGHT', 'COPYRIGHT'), ('LOW_QUALITY', 'LOW_QUALITY'), ('NOT_CONSTRUCTIVE', 'NOT_CONSTRUCTIVE'), ('PLAGIARISM', 'PLAGIARISM'), ('SPAM', 'SPAM'), ('NOT_SPECIFIED', 'NOT_SPECIFIED')], max_length=255),
        ),
    ]
