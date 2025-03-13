# Generated by Django 5.1.2 on 2025-03-13 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mpesa_application', '0004_savingsaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='savingsaccount',
            name='email',
            field=models.EmailField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='savingsaccount',
            name='id_number',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='savingsaccount',
            name='next_of_kin_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='savingsaccount',
            name='next_of_kin_phone',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
        migrations.AddField(
            model_name='savingsaccount',
            name='next_of_kin_relationship',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='savingsaccount',
            name='phone_number',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
    ]
