# Django M-Pesa System

A robust Django application for integrating with Safaricom's M-Pesa payment gateway, allowing seamless mobile payments in your Django projects.

## Features

- **STK Push**: Initiate payment requests directly to customer phones
- **C2B Integration**: Receive payments from customers to business
- **B2C Integration**: Send payments from business to customers
- **Transaction Query API**: Check transaction status
- **Account Balance API**: Query your M-Pesa account balance
- **Transaction Reversal**: Reverse completed transactions
- **Webhook Processing**: Handle M-Pesa callbacks automatically
- **Admin Dashboard**: Monitor transactions through Django admin

## Installation

```bash
pip install django-mpesa
```

Add to your installed apps in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'django_mpesa',
    # ...
]
```

## Configuration

Create the following variables in your project's `settings.py` file:

```python
# M-Pesa API credentials
MPESA_ENVIRONMENT = 'sandbox'  # or 'production'
MPESA_CONSUMER_KEY = 'your_consumer_key'
MPESA_CONSUMER_SECRET = 'your_consumer_secret'
MPESA_SHORTCODE = 'your_shortcode'
MPESA_EXPRESS_SHORTCODE = 'your_express_shortcode'
MPESA_PASSKEY = 'your_passkey'

# Optional configurations
MPESA_INITIATOR_NAME = 'your_initiator_name'
MPESA_SECURITY_CREDENTIAL = 'your_security_credential'
MPESA_CALLBACK_URL = 'https://yourdomain.com/api/mpesa/callback/'
```

## Usage

### STK Push (Lipa Na M-Pesa Online)

```python
from django_mpesa.api import MpesaClient

def initiate_payment(request):
    mpesa = MpesaClient()
    phone_number = '254700000000'
    amount = 1
    account_reference = 'reference'
    transaction_desc = 'Description'
    
    response = mpesa.stk_push(phone_number, amount, account_reference, transaction_desc)
    return JsonResponse(response)
```

### C2B Registration

```python
from django_mpesa.api import MpesaClient

def register_urls(request):
    mpesa = MpesaClient()
    validation_url = 'https://yourdomain.com/api/mpesa/validation/'
    confirmation_url = 'https://yourdomain.com/api/mpesa/confirmation/'
    
    response = mpesa.c2b_register_urls(validation_url, confirmation_url)
    return JsonResponse(response)
```

### B2C Payment

```python
from django_mpesa.api import MpesaClient

def send_money(request):
    mpesa = MpesaClient()
    phone_number = '254700000000'
    amount = 1
    remarks = 'Salary payment'
    occasion = 'End month'
    
    response = mpesa.b2c_payment(phone_number, amount, 'SalaryPayment', remarks, occasion)
    return JsonResponse(response)
```

## Handling Callbacks

Create URL patterns in your `urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    # ...
    path('api/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('api/mpesa/validation/', views.mpesa_validation, name='mpesa_validation'),
    path('api/mpesa/confirmation/', views.mpesa_confirmation, name='mpesa_confirmation'),
    # ...
]
```

Create the corresponding views:

```python
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Process STK push callback data
        # Save transaction details to your database
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})

@csrf_exempt
def mpesa_validation(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Validate the transaction
        # You can reject the transaction by returning an error response
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})

@csrf_exempt
def mpesa_confirmation(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Process C2B confirmation data
        # Save transaction details to your database
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})
```

## Models

The package provides models for storing transaction data:

- `MpesaPayment`: Stores STK push payment details
- `C2BPayment`: Stores C2B transaction details
- `B2CPayment`: Stores B2C transaction details

## Admin Integration

View and manage all M-Pesa transactions through the Django admin interface.

## Testing

The package includes test tools for sandbox environment:

```python
from django_mpesa.test import MpesaTestCase

class MyMpesaTest(MpesaTestCase):
    def test_stk_push(self):
        result = self.mpesa_client.stk_push('254700000000', 1, 'test', 'test')
        self.assertEqual(result['ResponseCode'], '0')
```

## Troubleshooting

### Common Issues

1. **Invalid credentials**: Ensure your consumer key and secret are correct.
2. **Wrong phone number format**: Use the format `254XXXXXXXXX` without the plus sign.
3. **Callback URL not accessible**: Ensure your callback URL is publicly accessible.

### Debug Mode

Enable debug mode to get detailed logs:

```python
MPESA_DEBUG = True
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- Safaricom Developer Portal
- Django Rest Framework