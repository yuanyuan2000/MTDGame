# Generated by Django 4.1.7 on 2023-05-09 03:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Node",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("layer", models.IntegerField()),
                ("x", models.FloatField()),
                ("y", models.FloatField()),
                ("color", models.CharField(max_length=7)),
            ],
        ),
        migrations.CreateModel(
            name="GameRoom",
            fields=[
                ("room_id", models.AutoField(primary_key=True, serialize=False)),
                ("game_mode", models.CharField(max_length=20)),
                ("creator_role", models.CharField(max_length=20)),
                (
                    "opponent_role",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="creator",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "opponent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="opponent",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Edge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_node",
                        to="api.node",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="target_node",
                        to="api.node",
                    ),
                ),
            ],
        ),
    ]