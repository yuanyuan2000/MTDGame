# Generated by Django 4.1.7 on 2023-05-09 04:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gameroom",
            name="creator",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AlterField(
            model_name="gameroom",
            name="opponent",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
