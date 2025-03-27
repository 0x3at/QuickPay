# Generated by Django 5.1.7 on 2025-03-27 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("PayPortal", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientNotes",
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
                ("clientID", models.IntegerField(default=0)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
                ("createdBy", models.CharField(blank=True, default="", max_length=128)),
                ("note", models.CharField(max_length=248)),
            ],
        ),
    ]
