# Generated by Django 5.1.2 on 2025-03-13 01:11

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import mpesa_application.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Limit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal'), ('TRANSFER', 'Transfer'), ('PAYMENT', 'Payment'), ('AIRTIME', 'Airtime Purchase'), ('BILLPAY', 'Bill Payment')], max_length=10)),
                ('min_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('daily_limit', models.DecimalField(decimal_places=2, max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id_number', models.CharField(help_text='National ID number', max_length=8, unique=True, validators=[mpesa_application.models.validate_kenyan_id])),
                ('phone_number', models.CharField(max_length=13, unique=True, validators=[django.core.validators.RegexValidator(message="Phone number must be in the format: '+254XXXXXXXXX'", regex='^\\+?254\\d{9}$')])),
                ('date_of_birth', models.DateField()),
                ('is_verified', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_name', models.CharField(max_length=100)),
                ('business_number', models.CharField(max_length=20, unique=True)),
                ('location', models.CharField(max_length=255)),
                ('float_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('commission_rate', models.DecimalField(decimal_places=2, default=0.5, max_digits=5)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agent_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MPesaAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_number', models.CharField(max_length=10, unique=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('pin_hash', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='mpesa_account', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PhoneLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_number', models.CharField(max_length=8, validators=[mpesa_application.models.validate_kenyan_id])),
                ('phone_number', models.CharField(max_length=13, unique=True, validators=[django.core.validators.RegexValidator(message="Phone number must be in the format: '+254XXXXXXXXX'", regex='^\\+?254\\d{9}$')])),
                ('is_active', models.BooleanField(default=True)),
                ('registration_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('id_number', 'phone_number'), name='unique_id_phone_combination')],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=20, unique=True)),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal'), ('TRANSFER', 'Transfer'), ('PAYMENT', 'Payment'), ('AIRTIME', 'Airtime Purchase'), ('BILLPAY', 'Bill Payment')], max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fee', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed'), ('REVERSED', 'Reversed')], default='PENDING', max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='mpesa_application.agent')),
                ('receiver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='received_transactions', to='mpesa_application.mpesaaccount')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sent_transactions', to='mpesa_application.mpesaaccount')),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('SMS', 'SMS Notification'), ('APP', 'In-App Notification'), ('EMAIL', 'Email Notification')], max_length=5)),
                ('title', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='mpesa_application.transaction')),
            ],
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('biller_name', models.CharField(max_length=100)),
                ('bill_type', models.CharField(choices=[('ELECTRIC', 'Electricity'), ('WATER', 'Water'), ('TV', 'Television'), ('INTERNET', 'Internet'), ('OTHER', 'Other')], max_length=10)),
                ('account_number', models.CharField(max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('due_date', models.DateField()),
                ('is_paid', models.BooleanField(default=False)),
                ('payment_transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='mpesa_application.transaction')),
            ],
        ),
        migrations.CreateModel(
            name='AgentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'Customer Deposit'), ('WITHDRAWAL', 'Customer Withdrawal'), ('FLOAT', 'Float Increase')], max_length=10)),
                ('agent_commission', models.DecimalField(decimal_places=2, max_digits=8)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='agent_transactions', to='mpesa_application.agent')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agent_details', to='mpesa_application.transaction')),
            ],
        ),
        migrations.CreateModel(
            name='UserLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal'), ('TRANSFER', 'Transfer'), ('PAYMENT', 'Payment'), ('AIRTIME', 'Airtime Purchase'), ('BILLPAY', 'Bill Payment')], max_length=10)),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('daily_limit', models.DecimalField(decimal_places=2, max_digits=12)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_limits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'transaction_type')},
            },
        ),
    ]
