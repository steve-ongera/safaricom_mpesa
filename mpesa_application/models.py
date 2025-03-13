from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.contrib.auth.models import BaseUserManager
from datetime import date

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, id_number=None, phone_number=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        # Set a default date_of_birth if not provided
        if 'date_of_birth' not in extra_fields:
            extra_fields['date_of_birth'] = date(1900, 1, 1)  # Default date
            
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            id_number=id_number,  # Ensure ID number is saved
            phone_number=phone_number,  # Ensure phone number is saved
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Set a default date_of_birth if not provided
        if 'date_of_birth' not in extra_fields:
            extra_fields['date_of_birth'] = date(1900, 1, 1)  # Default date
            
        return self.create_user(username, email, password, **extra_fields)

# Custom validator for Kenyan ID
def validate_kenyan_id(value):
    if not (value.isdigit() and (len(value) == 8 or len(value) == 7)):
        raise ValidationError("Kenyan ID must be 7 or 8 digits")

# Custom validator for phone number
phone_regex = RegexValidator(
    regex=r'^\+?254\d{9}$',
    message="Phone number must be in the format: '+254XXXXXXXXX'"
)

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Extended user model for M-PESA system"""
    id_number = models.CharField(
        max_length=8, 
        unique=True, 
        null=True,  # Make this nullable for superusers
        blank=True
    )
    phone_number = models.CharField(
        max_length=13,  
        unique=True,
        null=True,  # Make this nullable for superusers
        blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)  # Make this optional
    is_verified = models.BooleanField(default=False)
    
    objects = CustomUserManager()  # Use the custom manager
    
    def __str__(self):
        return f"{self.username} - {self.phone_number or 'No phone'}"

class MPesaAccount(models.Model):
    """M-PESA account associated with a user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mpesa_account')
    account_number = models.CharField(max_length=10, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    pin_hash = models.CharField(max_length=128)  # Stored as a hash
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Account: {self.account_number} - {self.user.phone_number}"


from django.db import models
from decimal import Decimal
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date
from django.conf import settings  # Import the custom user model

class SavingsAccount(models.Model):
    """Model representing a user's savings account."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_account')
    account_number = models.CharField(max_length=10, unique=True, editable=False)  # Same as MPesaAccount
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    # Additional Fields
    email = models.EmailField(max_length=255 , blank=True , null=True)
    phone_number = models.CharField(max_length=13, blank=True , null=True)
    id_number = models.CharField(max_length=8, blank=True , null=True)

    # Next of Kin details
    next_of_kin_name = models.CharField(max_length=255, blank=True , null=True)
    next_of_kin_phone = models.CharField(max_length=13, blank=True , null=True)
    next_of_kin_relationship = models.CharField(max_length=50 , blank=True , null=True)

    def deposit(self, amount):
        """Deposit money into the savings account."""
        if amount > 0:
            self.balance += amount
            self.save()
            return True
        return False

    def withdraw(self, amount):
        """Withdraw money from the savings account if sufficient balance exists."""
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.save()
            return True
        return False

    def transfer_to_mpesa(self, amount):
        """Transfer funds from savings to MPesaAccount."""
        if self.withdraw(amount):  
            mpesa_account = self.user.mpesa_account  
            mpesa_account.balance += amount
            mpesa_account.save()
            return True
        return False

    def __str__(self):
        return f"{self.user.username} - {self.account_number}"

    def save(self, *args, **kwargs):
        """Fetch the account number from MPesaAccount when creating a savings account."""
        if not self.account_number:
            try:
                self.account_number = self.user.mpesa_account.account_number  # Use MPesa account number
            except AttributeError:
                raise ValidationError("User must have an MPesa account before opening a savings account.")

        # Auto-fill fields from the user model if available
        self.email = self.user.email
        self.phone_number = self.user.phone_number
        self.id_number = self.user.id_number

        super().save(*args, **kwargs)


class Agent(models.Model):
    """Model for M-PESA agents who handle deposits and withdrawals"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    business_name = models.CharField(max_length=100)
    business_number = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=255)
    float_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    
    def __str__(self):
        return f"{self.business_name} - {self.business_number}"

class PhoneLine(models.Model):
    """Model to track phone lines registered to a national ID"""
    id_number = models.CharField(max_length=8, validators=[validate_kenyan_id])
    phone_number = models.CharField(max_length=13, validators=[phone_regex], unique=True)
    is_active = models.BooleanField(default=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['id_number', 'phone_number'], 
                name='unique_id_phone_combination'
            )
        ]
    
    def __str__(self):
        return f"{self.id_number} - {self.phone_number}"
    
    def save(self, *args, **kwargs):
        # Check if this ID has more than 5 active lines
        active_lines = PhoneLine.objects.filter(
            id_number=self.id_number, 
            is_active=True
        ).count()
        
        # If this is a new line (not an update) and the ID already has 5 lines
        if not self.pk and active_lines >= 5:
            raise ValidationError("A National ID cannot have more than 5 active phone lines")
        
        super().save(*args, **kwargs)

class Transaction(models.Model):
    """Model for all M-PESA transactions"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
        ('PAYMENT', 'Payment'),
        ('AIRTIME', 'Airtime Purchase'),
        ('BILLPAY', 'Bill Payment'),
        ('LOAN', 'loan'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
    ]
    
    transaction_id = models.CharField(max_length=20, unique=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    sender = models.ForeignKey(MPesaAccount, on_delete=models.PROTECT, related_name='sent_transactions')
    receiver = models.ForeignKey(MPesaAccount, on_delete=models.PROTECT, related_name='received_transactions', null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.amount}"

class AgentTransaction(models.Model):
    """Model specifically for agent deposit and withdrawal transactions"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Customer Deposit'),
        ('WITHDRAWAL', 'Customer Withdrawal'),
        ('FLOAT', 'Float Increase'),
    ]
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='agent_details')
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='agent_transactions')
    customer = models.ForeignKey(User, on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    agent_commission = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.agent.business_name}"

class Bill(models.Model):
    """Model for bill payments"""
    BILL_TYPES = [
        ('ELECTRIC', 'Electricity'),
        ('WATER', 'Water'),
        ('TV', 'Television'),
        ('INTERNET', 'Internet'),
        ('OTHER', 'Other'),
    ]
    
    biller_name = models.CharField(max_length=100)
    bill_type = models.CharField(max_length=10, choices=BILL_TYPES)
    account_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    payment_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.biller_name} - {self.account_number} - {self.amount}"

class Notification(models.Model):
    """Model for sending notifications to users"""
    NOTIFICATION_TYPES = [
        ('SMS', 'SMS Notification'),
        ('APP', 'In-App Notification'),
        ('EMAIL', 'Email Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=5, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.username} - {self.timestamp}"

class Limit(models.Model):
    """Model for transaction limits"""
    transaction_type = models.CharField(max_length=10, choices=Transaction.TRANSACTION_TYPES)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    daily_limit = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.transaction_type} - Min: {self.min_amount} - Max: {self.max_amount}"

class UserLimit(models.Model):
    """Custom limits for specific users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_limits')
    transaction_type = models.CharField(max_length=10, choices=Transaction.TRANSACTION_TYPES)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    daily_limit = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        unique_together = ['user', 'transaction_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - Max: {self.max_amount}"


class Loan(models.Model):
    """Model to manage loans for users."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REPAID', 'Repaid'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.0'))  
    repayment_due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    is_paid = models.BooleanField(default=False)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # For new loans, set the remaining amount
        if not self.pk or (self.remaining_amount is None or self.remaining_amount == Decimal('0.00')) and self.status != "REPAID":
            self.remaining_amount = self.amount  # Only set initial amount if it's a new loan
        
        # Update status based on remaining amount
        if self.remaining_amount <= Decimal('0.00'):
            self.is_paid = True
            self.status = "REPAID"
        else:
            self.is_paid = False
            # Only reset to PENDING if not already APPROVED
            if self.status != "APPROVED" and self.status != "REJECTED":
                self.status = "PENDING"
                
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Loan of {self.amount} for {self.user.username} - {'Paid' if self.is_paid else 'Pending'}"
