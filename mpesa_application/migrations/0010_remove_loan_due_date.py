# Generated by Django 5.1.2 on 2025-03-13 18:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mpesa_application', '0009_loan_remaining_amount_alter_limit_transaction_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loan',
            name='due_date',
        ),
    ]
