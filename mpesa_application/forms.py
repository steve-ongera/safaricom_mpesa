from django import forms
from django.core.validators import RegexValidator, MinLengthValidator
from .models import User, MPesaAccount
import datetime

class CustomerRegistrationForm(forms.Form):
    """Form for registering a new M-PESA customer"""
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    id_number = forms.CharField(
        max_length=8,
        validators=[
            RegexValidator(r'^\d{7,8}$', 'Enter a valid Kenyan ID number (7-8 digits).')
        ],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Number'})
    )
    phone_number = forms.CharField(
        max_length=13,
        validators=[
            RegexValidator(r'^\+254\d{9}$', 'Enter a valid phone number (+254XXXXXXXXX).')
        ],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254XXXXXXXXX'})
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date',
            'max': datetime.date.today().strftime('%Y-%m-%d')
        })
    )
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if age < 18:
            raise forms.ValidationError("Customer must be at least 18 years old.")
        
        return dob

class MPesaAccountCreationForm(forms.Form):
    """Form for creating a new M-PESA account"""
    pin = forms.CharField(
        max_length=4,
        min_length=4,
        validators=[
            RegexValidator(r'^\d{4}$', 'PIN must be 4 digits.'),
            MinLengthValidator(4)
        ],
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '4-digit PIN'})
    )
    confirm_pin = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm PIN'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        confirm_pin = cleaned_data.get('confirm_pin')
        
        if pin and confirm_pin and pin != confirm_pin:
            raise forms.ValidationError("PINs do not match.")
            
        # Check for sequential or repeating digits
        if pin and (
            pin == '1234' or pin == '4321' or 
            pin == '0000' or pin == '1111' or pin == '2222' or 
            pin == '3333' or pin == '4444' or pin == '5555' or 
            pin == '6666' or pin == '7777' or pin == '8888' or pin == '9999'
        ):
            raise forms.ValidationError("PIN is too weak. Avoid sequential or repeating digits.")
            
        return cleaned_data
    




from django import forms
from decimal import Decimal
from django.core.validators import MinValueValidator

class AgentFloatForm(forms.Form):
    """Form for agent float management"""
    TRANSACTION_CHOICES = [
        ('increase', 'Increase Float'),
        ('decrease', 'Decrease Float'),
    ]
    
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('1.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Amount (KES)',
            'step': '0.01'
        })
    )
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        # Ensure amount is positive and has at most 2 decimal places
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        
        # Format to 2 decimal places
        return amount.quantize(Decimal('0.01'))

class InitialDepositForm(forms.Form):
    """Form for initial deposit into a new M-PESA account"""
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('50.00'),  # Minimum initial deposit
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Amount (KES)',
            'step': '0.01'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        
        # Minimum deposit validation 
        if amount < Decimal('50.00'):
            raise forms.ValidationError("Initial deposit must be at least KES 50.00")
        
        # Format to 2 decimal places
        return amount.quantize(Decimal('0.01'))