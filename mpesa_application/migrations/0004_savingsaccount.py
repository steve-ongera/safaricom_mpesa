# Generated by Django 5.1.2 on 2025-03-13 14:39

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mpesa_application', '0003_alter_user_id_number_alter_user_phone_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavingsAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_number', models.CharField(editable=False, max_length=10, unique=True)),
                ('balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='savings_account', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
