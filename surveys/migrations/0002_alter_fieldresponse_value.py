# Generated by Django 5.1 on 2024-08-16 00:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fieldresponse",
            name="value",
            field=models.JSONField(blank=True, default=""),
            preserve_default=False,
        ),
    ]
