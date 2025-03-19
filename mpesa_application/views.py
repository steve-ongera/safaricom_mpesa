from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.contrib.auth import logout
from django.contrib import messages
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect , JsonResponse
from django.urls import reverse
import hashlib
import random
from decimal import Decimal

from .models import User, MPesaAccount, Agent, PhoneLine
from .forms import CustomerRegistrationForm, MPesaAccountCreationForm

# Helper function to check if user is an agent
def is_agent(user):
    return hasattr(user, 'agent_profile') and user.agent_profile.is_active

# Helper to generate a unique account number
def generate_account_number():
    while True:
        # Generate a random 10-digit number
        account_number = ''.join(random.choices('0123456789', k=10))
        
        # Check if it already exists
        if not MPesaAccount.objects.filter(account_number=account_number).exists():
            return account_number

# Helper to hash PIN
def hash_pin(pin):
    # In production, use a proper password hashing library like bcrypt
    return hashlib.sha256(pin.encode()).hexdigest()

@login_required
@user_passes_test(is_agent)

def agent_dashboard(request):
    """Dashboard for agents showing recent registrations and stats"""
    agent = request.user.agent_profile  # Ensure `agent_profile` exists

    # Get recent accounts where the agent handled a deposit
    recent_accounts = MPesaAccount.objects.filter(
        sent_transactions__agent=agent,
        sent_transactions__transaction_type='DEPOSIT',
    ).distinct().order_by('-created_at')[:5]

    total_registrations = recent_accounts.count()

    context = {
        'agent': agent,
        'recent_accounts': recent_accounts,
        'total_registrations': total_registrations,
    }

    return render(request, 'agent/dashboard.html', context)

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect

import re
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect

def normalize_phone_number(phone_number):
    """Convert phone number to standard format starting with 254"""
    phone_number = phone_number.strip().replace(" ", "").replace("-", "")  # Remove spaces and dashes
    
    if phone_number.startswith("+254"):
        return "254" + phone_number[4:]
    elif phone_number.startswith("07"):
        return "254" + phone_number[1:]
    elif phone_number.startswith("011"):
        return "254" + phone_number[1:]
    else:
        return phone_number  # Assume it's already in correct format

@login_required
@user_passes_test(is_agent)
def register_customer(request):
    """View for agents to register new customers"""
    if request.method == 'POST':
        user_form = CustomerRegistrationForm(request.POST)
        account_form = MPesaAccountCreationForm(request.POST)
        
        if user_form.is_valid() and account_form.is_valid():
            try:
                with transaction.atomic():
                    # Get form data
                    id_number = user_form.cleaned_data['id_number']
                    phone_number = normalize_phone_number(user_form.cleaned_data['phone_number'])  # Normalize phone
                    email = user_form.cleaned_data['email']
                    first_name = user_form.cleaned_data['first_name']
                    last_name = user_form.cleaned_data['last_name']
                    pin = account_form.cleaned_data['pin']  # Use as password

                    # Check if phone number (username) is already registered
                    if User.objects.filter(username=phone_number).exists():
                        messages.error(request, "This phone number is already registered.")
                        return redirect('register_customer')

                    # Create the user
                    user = User.objects.create_user(
                        username=phone_number,  # Normalized phone as username
                        email=email,  # User's actual email
                        password=pin,  # PIN as password
                        first_name=first_name,
                        last_name=last_name,
                        id_number=id_number,  # Ensure ID number is saved
                        phone_number=phone_number,  # Ensure phone number is saved
                        is_active=True,
                       
                    )

                    # Create M-PESA account
                    account_number = generate_account_number()

                    mpesa_account = MPesaAccount.objects.create(
                        user=user,
                        account_number=account_number,
                        balance=0.00,
                        pin_hash=hash_pin(pin),
                        is_active=True
                    )

                    # Send login details via email
                    send_mail(
                        subject="Your M-Pesa Account Details",
                        message=f"Dear {first_name},\n\nYour M-Pesa account has been created.\nUsername: {phone_number}\nPassword: {pin}\n\nPlease log in and change your password.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )

                    messages.success(request, f"Customer {first_name} {last_name} registered successfully. Login details sent to {email}.")
                    return redirect('registration_success', account_id=mpesa_account.id)

            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
    else:
        user_form = CustomerRegistrationForm()
        account_form = MPesaAccountCreationForm()
    
    return render(request, 'agent/register_customer.html', {'user_form': user_form, 'account_form': account_form})




@login_required
@user_passes_test(is_agent)
def registration_success(request, account_id):
    """Registration success page with account details"""
    account = get_object_or_404(MPesaAccount, id=account_id)
    
    # Security check to ensure only the registering agent can see this
    if not hasattr(account.user, 'agent_profile'):
        # This ensures we only show accounts that were just created by agents
        messages.error(request, "Account not found or access denied")
        return redirect('agent_dashboard')
    
    context = {
        'account': account,
        'agent': request.user.agent_profile
    }
    
    return render(request, 'agent/registration_success.html', context)

@login_required
@user_passes_test(is_agent)
def verify_customer_id(request):
    """AJAX view to verify customer ID before registration"""
    if request.method == 'POST':
        id_number = request.POST.get('id_number')
        
        # In a real system, this would check against a government database
        # For this example, we'll just check if the ID exists in our system
        
        user_exists = User.objects.filter(id_number=id_number).exists()
        
        # Check number of active lines for this ID
        active_lines = PhoneLine.objects.filter(
            id_number=id_number, 
            is_active=True
        ).count()
        
        data = {
            'user_exists': user_exists,
            'active_lines': active_lines,
            'can_register': active_lines < 5
        }
        
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
import uuid
from decimal import Decimal

from .models import (
    User, MPesaAccount, Agent, Transaction, 
    AgentTransaction, Limit, Notification
)
from .forms import AgentFloatForm, InitialDepositForm

# Helper function to check if user is an agent (already defined in previous code)
def is_agent(user):
    return hasattr(user, 'agent_profile') and user.agent_profile.is_active

# Generate unique transaction ID
def generate_transaction_id():
    # Format: MP + randomized alphanumeric (real M-PESA uses specific formats)
    return f"MP{uuid.uuid4().hex[:10].upper()}"

@login_required
@user_passes_test(is_agent)
def agent_transactions(request):
    """View for agents to see their transaction history"""
    agent = request.user.agent_profile
    
    # Get all transactions for this agent
    agent_txns = AgentTransaction.objects.filter(
        agent=agent
    ).select_related('transaction', 'customer').order_by('-transaction__timestamp')
    
    # Handle filtering
    txn_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if txn_type:
        agent_txns = agent_txns.filter(transaction_type=txn_type)
    
    if date_from:
        agent_txns = agent_txns.filter(transaction__timestamp__date__gte=date_from)
    
    if date_to:
        agent_txns = agent_txns.filter(transaction__timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(agent_txns, 20)  # 20 transactions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals for display
    total_deposits = sum(
        txn.transaction.amount 
        for txn in agent_txns.filter(transaction_type='DEPOSIT')
    )
    total_withdrawals = sum(
        txn.transaction.amount 
        for txn in agent_txns.filter(transaction_type='WITHDRAWAL')
    )
    total_commission = sum(txn.agent_commission for txn in agent_txns)
    
    context = {
        'agent': agent,
        'transactions_page': page_obj,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_commission': total_commission,
        'filters': {
            'txn_type': txn_type,
            'date_from': date_from,
            'date_to': date_to,
        },
    }
    
    return render(request, 'agent/transactions.html', context)

@login_required
@user_passes_test(is_agent)
def agent_float(request):
    """View for agents to manage their float balance"""
    agent = request.user.agent_profile
    
    if request.method == 'POST':
        form = AgentFloatForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            transaction_type = form.cleaned_data['transaction_type']
            
            try:
                with transaction.atomic():
                    # Create the transaction record
                    txn_id = generate_transaction_id()
                    
                    # Find the system account (in a real system this would be predefined)
                    # For demo purposes we'll use the first superuser's account or create one
                    system_user = User.objects.filter(is_superuser=True).first()
                    system_account, _ = MPesaAccount.objects.get_or_create(
                        user=system_user,
                        defaults={
                            'account_number': '0000000000',
                            'pin_hash': 'system',
                            'is_active': True
                        }
                    )
                    
                    # Handle different transaction types
                    if transaction_type == 'increase':
                        # Increase float (money from agent to system)
                        txn = Transaction.objects.create(
                            transaction_id=txn_id,
                            transaction_type='FLOAT',
                            sender=system_account,  # System gives float
                            receiver=None,
                            agent=agent,
                            amount=amount,
                            fee=Decimal('0.00'),
                            status='COMPLETED',
                            description=f"Float increase for agent {agent.business_name}"
                        )
                        
                        # Update agent float balance
                        agent.float_balance += amount
                        agent.save()
                        
                        messages.success(request, f"Float successfully increased by KES {amount}")
                        
                    elif transaction_type == 'decrease':
                        # Check if agent has enough float
                        if agent.float_balance < amount:
                            messages.error(request, "Insufficient float balance for this operation")
                            return redirect('agent_float')
                        
                        # Decrease float (money from system to agent)
                        txn = Transaction.objects.create(
                            transaction_id=txn_id,
                            transaction_type='FLOAT',
                            sender=None,
                            receiver=system_account,  # System receives float back
                            agent=agent,
                            amount=amount,
                            fee=Decimal('0.00'),
                            status='COMPLETED',
                            description=f"Float decrease for agent {agent.business_name}"
                        )
                        
                        # Update agent float balance
                        agent.float_balance -= amount
                        agent.save()
                        
                        messages.success(request, f"Float successfully decreased by KES {amount}")
                    
                    # Create agent transaction record
                    AgentTransaction.objects.create(
                        transaction=txn,
                        agent=agent,
                        customer=system_user,  # The "customer" is the system in this case
                        transaction_type='FLOAT',
                        agent_commission=Decimal('0.00')  # No commission on float adjustments
                    )
                    
                return redirect('agent_float')
                    
            except Exception as e:
                messages.error(request, f"Error processing float adjustment: {str(e)}")
    else:
        form = AgentFloatForm()
    
    # Get float history
    float_history = AgentTransaction.objects.filter(
        agent=agent,
        transaction_type='FLOAT'
    ).select_related('transaction').order_by('-transaction__timestamp')[:10]
    
    context = {
        'agent': agent,
        'form': form,
        'float_history': float_history,
    }
    
    return render(request, 'agent/float.html', context)

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import MPesaAccount, Transaction, AgentTransaction, Notification, Limit
from .forms import InitialDepositForm
from .utils import generate_transaction_id


@login_required
@user_passes_test(is_agent)
def search_tenant_deposit(request):
    """Search for a customer's MPesa account by phone number."""
    query = request.GET.get('phone_number')
    accounts = None

    if query:
        accounts = MPesaAccount.objects.filter(user__phone_number__icontains=query)

    context = {
        'accounts': accounts,
        'query': query
    }
    return render(request, 'agent/search_tenant_deposit.html', context)


@login_required
@user_passes_test(is_agent)
def initial_deposit(request, account_id):
    """View for agents to deposit funds into a customer's M-Pesa account."""
    agent = request.user.agent_profile
    account = get_object_or_404(MPesaAccount, id=account_id)
    
    if request.method == 'POST':
        form = InitialDepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Check if agent has enough float balance
            if agent.float_balance < amount:
                messages.error(request, "Insufficient float balance to process this deposit.")
                return redirect('initial_deposit', account_id=account_id)
            
            try:
                with transaction.atomic():
                    # Get transaction limits
                    deposit_limit = Limit.objects.filter(
                        transaction_type='DEPOSIT',
                        is_active=True
                    ).first()
                    
                    if deposit_limit and (amount < deposit_limit.min_amount or amount > deposit_limit.max_amount):
                        messages.error(
                            request, 
                            f"Deposit amount must be between KES {deposit_limit.min_amount} and KES {deposit_limit.max_amount}."
                        )
                        return redirect('initial_deposit', account_id=account_id)
                    
                    # Generate unique transaction ID
                    txn_id = generate_transaction_id()
                    
                    # Find or create the agent's MPesa account
                    agent_account, _ = MPesaAccount.objects.get_or_create(
                        user=agent.user,
                        defaults={
                            'account_number': f"AG{agent.business_number[-8:]}",
                            'pin_hash': 'agent',  # Ideally, this should be encrypted securely
                            'is_active': True
                        }
                    )
                    
                    # Create deposit transaction
                    txn = Transaction.objects.create(
                        transaction_id=txn_id,
                        transaction_type='DEPOSIT',
                        sender=agent_account,
                        receiver=account,
                        agent=agent,
                        amount=amount,
                        fee=Decimal('0.00'),  # No fee for deposits
                        status='COMPLETED',
                        description=f"Deposit by agent {agent.business_name}"
                    )
                    
                    # Calculate agent commission (usually none for deposits)
                    commission = Decimal('0.00')
                    
                    # Log agent's transaction
                    AgentTransaction.objects.create(
                        transaction=txn,
                        agent=agent,
                        customer=account.user,
                        transaction_type='DEPOSIT',
                        agent_commission=commission
                    )
                    
                    # Update customer's account balance
                    account.balance += amount
                    account.save()
                    
                    # Deduct from agent's float balance
                    agent.float_balance -= amount
                    agent.save()
                    
                    # Send notification to customer
                    Notification.objects.create(
                        user=account.user,
                        notification_type='SMS',
                        title="M-PESA Deposit",
                        message=f"Your M-PESA account has been credited with KES {amount}. New balance: KES {account.balance}.",
                        transaction=txn
                    )
                    
                    messages.success(
                        request, 
                        f"Deposit of KES {amount} successfully processed. New account balance: KES {account.balance}."
                    )
                    return redirect('agent_dashboard')
                    
            except Exception as e:
                messages.error(request, f"Error processing deposit: {str(e)}")
    else:
        form = InitialDepositForm()
    
    context = {
        'agent': agent,
        'account': account,
        'customer': account.user,
        'form': form,
    }
    
    return render(request, 'agent/initial_deposit.html', context)


from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

def login_view(request):
    if request.method == "POST":
        phone_number = request.POST.get("phone_number")
        pin = request.POST.get("pin")

        try:
            # Check if user exists
            user = User.objects.get(username=phone_number)

            # Authenticate
            authenticated_user = authenticate(request, username=user.username, password=pin)

            if authenticated_user is not None:
                login(request, authenticated_user)

                # Check if user is staff
                if authenticated_user.is_staff:
                    return redirect("agent_dashboard")  # Agent dashboard
                else:
                    return redirect("customer_dashboard")  # Normal user dashboard

            else:
                messages.error(request, "Invalid phone number or PIN")

        except User.DoesNotExist:
            messages.error(request, "Account with this phone number does not exist")

    return render(request, "auth/login.html")


def user_logout(request):
    """Logs out the user and redirects to the login page"""
    logout(request)
    return redirect('login')  # Redirect to your login page or home page


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db import models
from django.db.models import Count
import json


@login_required
def customer_dashboard(request):
    # Get the user's M-Pesa account (if exists)
    mpesa_account = MPesaAccount.objects.select_related("user").filter(user=request.user).first()
    
    # Initialize empty lists
    latest_transactions = []
    transaction_partners = []
    transaction_types_data = []
    
    if mpesa_account:
        # Get the latest transactions where user is either sender or receiver
        # and transaction type is TRANSFER (money sent to or received from others)
        latest_transactions = Transaction.objects.filter(
            models.Q(sender=mpesa_account) | models.Q(receiver=mpesa_account),
            transaction_type='TRANSFER'  # Only include transfers between users
        ).order_by('-timestamp')[:6]


        # Get transaction type statistics
        transaction_types = Transaction.objects.filter(
            models.Q(sender=mpesa_account) | models.Q(receiver=mpesa_account)
        ).values('transaction_type').annotate(
            count=Count('transaction_type')
        ).order_by('-count')

        # Format data for the donut chart
        transaction_types_data = []
        for item in transaction_types:
            # Get the display name for the transaction type
            display_name = dict(Transaction.TRANSACTION_TYPES).get(item['transaction_type'], item['transaction_type'])
            transaction_types_data.append({
                'type': display_name,
                'count': item['count']
            })
        
        # For each transaction, get the other party (the person you transacted with)
        for transaction in latest_transactions:
            partner = None
            transaction_type = ""
            
            if transaction.sender == mpesa_account:
                # You sent money
                partner = transaction.receiver
                transaction_type = "Sent"
                transaction.is_outgoing = True  # Add flag for template
            else:
                # You received money
                partner = transaction.sender
                transaction_type = "Received"
                transaction.is_outgoing = False  # Add flag for template
                
            if partner:
                transaction_partners.append({
                    'transaction': transaction,
                    'partner': partner,
                    'type': transaction_type
                })
    
    context = {
        "user": request.user,
        "mpesa_account": mpesa_account,
        "latest_transactions": latest_transactions,
        "transaction_partners": transaction_partners[:6] , # Limit to 6 items
        "transaction_types_json": json.dumps(transaction_types_data)  # Convert to JSON for JavaScript
    }
    return render(request, "customer/customer_dashboard.html", context)



from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Agent
@login_required
def search_agents(request):
    """Handle AJAX search requests and render the search page."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
        query = request.GET.get('query', '').strip()
        results = []

        if query:
            agents = Agent.objects.filter(Q(business_number__icontains=query) | Q(business_name__icontains=query))[:10]

            results = [
                {
                    'id': agent.id, 
                    'business_name': agent.business_name, 
                    'business_number': agent.business_number,
                    'withdraw_url': f"/withdraw-from-agent/{agent.id}/"  # Link to withdraw money
                }
                for agent in agents
            ]

        return JsonResponse({'results': results})

    return render(request, 'customer/search_agent.html')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import random
import string
from .models import MPesaAccount, Agent, Transaction

def generate_unique_txn():
    """Generate a unique 10-character alphanumeric uppercase transaction ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def calculate_withdrawal_fee(amount):
    """Calculate withdrawal fee based on transaction amount."""
    fee_structure = [
        (50, 90, 0),
        (91, 200, 12),
        (201, 500, 15),
        (501, 1000, 28),
        (1001, 1500, 40),
        (1501, 2500, 50),
        (2501, 3500, 55),
        (3501, 5000, 60),
        (5001, 7500, 75),
        (7501, 10000, 85),
        (10001, 15000, 100),
        (15001, 20000, 110),
        (20001, 35000, 120),
        (35001, 50000, 150),
        (50001, 100000, 200),
        (100001, 150000, 250),
        (150001, 300000, 300),
    ]
    
    for min_amount, max_amount, fee in fee_structure:
        if min_amount <= amount <= max_amount:
            return Decimal(fee)
    return Decimal(0)  # Default fee (shouldn't happen)

@login_required
def withdraw_money(request, agent_id):
    """Allow a logged-in customer to withdraw money from a specific agent."""
    agent = get_object_or_404(Agent, id=agent_id)
    customer = request.user  # Get the logged-in user

    try:
        mpesa_account = customer.mpesa_account  # Get user's MPESA account
    except MPesaAccount.DoesNotExist:
        messages.error(request, "You don't have an active MPesa account.")
        return redirect('search_agents')

    if request.method == 'POST':
        amount = request.POST.get('amount')

        try:
            amount = Decimal(amount)
            if amount < 50:
                messages.error(request, "Minimum withdrawal amount is KES 50.")
                return redirect('withdraw_money', agent_id=agent.id)

            fee = calculate_withdrawal_fee(amount)
            total_deduction = amount + fee  # Amount to be deducted from customer's balance

            if total_deduction > mpesa_account.balance:
                messages.error(request, "Insufficient balance.")
                return redirect('withdraw_money', agent_id=agent.id)

            if amount > agent.float_balance:
                messages.error(request, "Agent does not have enough float balance.")
                return redirect('withdraw_money', agent_id=agent.id)

            # Perform the withdrawal in an atomic transaction
            with transaction.atomic():
                mpesa_account.balance -= total_deduction
                agent.float_balance -= amount  # Agent only loses the withdrawn amount, not the fee
                mpesa_account.save()
                agent.save()

                # Generate unique transaction ID
                txn_id = generate_unique_txn()

                # Save transaction record
                Transaction.objects.create(
                    transaction_id=txn_id,
                    transaction_type='WITHDRAWAL',
                    sender=mpesa_account,
                    receiver=None,  # No specific receiver for withdrawals
                    agent=agent,
                    amount=amount,
                    fee=fee,
                    status='COMPLETED',
                    description=f"Withdrawal of KES {amount} (Fee: KES {fee}) by {customer.username} from agent {agent.business_name}"
                )

            messages.success(request, f"Withdrawal of KES {amount} successful. Fee: KES {fee}. TXN ID: {txn_id}")
            return redirect('search_agents')

        except (ValueError, TypeError):
            messages.error(request, "Invalid amount entered.")

    return render(request, 'customer/withdraw_money.html', {'agent': agent})



from decimal import Decimal

def calculate_transaction_fee(amount):
    """Calculate the transaction fee based on amount being sent."""
    amount = Decimal(amount)
    
    if amount < 100:
        return Decimal(0)  # No fee for amounts less than 100
    elif 101 <= amount <= 500:
        return Decimal(7)
    elif 501 <= amount <= 1000:
        return Decimal(13)
    elif 1001 <= amount <= 5000:
        return Decimal(25)
    elif 5001 <= amount <= 10000:
        return Decimal(50)
    else:
        return Decimal(100)  # Flat fee for amounts above 10,000

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import MPesaAccount, Transaction
from decimal import Decimal
import uuid

def generate_transaction_id():
    """Generate a unique transaction ID."""
    return str(uuid.uuid4().hex[:12]).upper()

@login_required
def send_money(request):
    """Allow a customer to send money to another registered customer."""
    sender = request.user  # Logged-in user is the sender

    try:
        sender_account = sender.mpesa_account  # Get sender's M-PESA account
    except MPesaAccount.DoesNotExist:
        messages.error(request, "You don't have an active M-Pesa account.")
        return redirect('send_money')

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')

        try:
            amount = Decimal(amount)

            if amount <= 0:
                raise ValueError("Invalid amount.")

            # Fetch recipient's user object first
            recipient_user = get_object_or_404(User, phone_number=phone_number)

            # Fetch recipient's MPesa account
            recipient_account = get_object_or_404(MPesaAccount, user=recipient_user)

            # Calculate transaction fee
            transaction_fee = calculate_transaction_fee(amount)
            total_deduction = amount + transaction_fee  # Total deduction from sender

            if total_deduction > sender_account.balance:
                messages.error(request, "Insufficient balance for this transaction.")
                return redirect('send_money')

            # Perform the transaction
            sender_account.balance -= total_deduction
            recipient_account.balance += amount
            sender_account.save()
            recipient_account.save()

            # Save transaction in the database
            transaction = Transaction.objects.create(
                transaction_id=generate_transaction_id(),
                transaction_type='TRANSFER',
                sender=sender_account,
                receiver=recipient_account,
                amount=amount,
                fee=transaction_fee,
                status='COMPLETED',
                description=f"Money transfer from {sender.username} to {recipient_user.username}"
            )

            messages.success(request, f"Transaction successful! Sent KES {amount} to {recipient_user.get_full_name()} (Fee: KES {transaction_fee}).")
            return redirect('send_money')

        except (ValueError, TypeError):
            messages.error(request, "Invalid amount entered.")

    return render(request, 'customer/send_money.html')


from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()  # Get the correct User model

def check_recipient(request):
    """AJAX view to fetch recipient's name based on phone number."""
    phone_number = request.GET.get('phone_number')

    if not phone_number or len(phone_number) != 12:
        return JsonResponse({"error": "Invalid phone number"}, status=400)

    try:
        recipient_user = User.objects.get(phone_number=phone_number)
        return JsonResponse({"name": recipient_user.get_full_name()})
    except User.DoesNotExist:
        return JsonResponse({"error": "No user found with this number"}, status=404)


@login_required
def check_balance(request):
    """Display the logged-in user's M-Pesa balance."""
    try:
        mpesa_account = request.user.mpesa_account  # Get user's M-Pesa account
        balance = mpesa_account.balance
    except AttributeError:
        balance = None  # If no account exists

    return render(request, 'customer/check_balance.html', {'balance': balance})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Transaction

@login_required
def transaction_history(request):
    """Display the logged-in user's transaction history."""
    try:
        mpesa_account = request.user.mpesa_account  # Get the user's M-Pesa account
        sent_transactions = Transaction.objects.filter(sender=mpesa_account).order_by("-timestamp")  # Transactions sent
        received_transactions = Transaction.objects.filter(receiver=mpesa_account).order_by("-timestamp")  # Transactions received
    except AttributeError:
        sent_transactions = []
        received_transactions = []

    return render(request, 'customer/transaction_history.html', {
        'sent_transactions': sent_transactions,
        'received_transactions': received_transactions
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SavingsAccount, MPesaAccount
from .forms import SavingsAccountForm  # Import the form

@login_required
def create_savings_account(request):
    """Allow a logged-in user to create a savings account if they don’t have one."""
    user = request.user

    # Check if user already has a savings account
    if hasattr(user, 'savings_account'):
        messages.info(request, "You already have a savings account.")
        return redirect('savings_dashboard')  # Redirect to savings dashboard

    # Check if user has an MPesa account
    try:
        mpesa_account = user.mpesa_account
    except MPesaAccount.DoesNotExist:
        messages.error(request, "You need an MPesa account before opening a savings account.")
        return redirect('customer_dashboard')  # Redirect to customer dashboard

    if request.method == 'POST':
        form = SavingsAccountForm(request.POST)
        if form.is_valid():
            savings_account = form.save(commit=False)
            savings_account.user = user
            savings_account.account_number = mpesa_account.account_number  # Auto-set MPesa account number

            # Auto-fill fields from user model
            savings_account.email = user.email
            savings_account.phone_number = user.phone_number
            savings_account.id_number = user.id_number

            savings_account.save()
            messages.success(request, "Savings account created successfully!")
            return redirect('customer_dashboard')  # Redirect to customer dashboard
        else:
            messages.error(request, "Error creating savings account. Please check the details.")

    else:
        form = SavingsAccountForm()  # Empty form for GET request

    return render(request, 'savings/create_savings.html', {'form': form})


@login_required
def savings_dashboard(request):
    """Display the user's savings account details."""
    user = request.user

    # Check if user has a savings account
    try:
        savings_account = user.savings_account
    except SavingsAccount.DoesNotExist:
        messages.error(request, "You do not have a savings account. Please create one first.")
        return redirect('create_savings_account')

    return render(request, 'savings/savings_dashboard.html', {'savings_account': savings_account})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
import uuid
from .models import SavingsAccount, MPesaAccount, Transaction

@login_required
def deposit_savings(request):
    """Allow the user to deposit money into their savings account from MPesa and record the transaction."""
    user = request.user

    # Ensure the user has both a savings and MPesa account
    if not hasattr(user, 'savings_account'):
        messages.error(request, "You do not have a savings account.")
        return redirect('savings_dashboard')

    if not hasattr(user, 'mpesa_account'):
        messages.error(request, "You need an MPesa account to deposit money.")
        return redirect('customer_dashboard')

    savings_account = user.savings_account
    mpesa_account = user.mpesa_account

    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = Decimal(amount)
            if 0 < amount <= mpesa_account.balance:
                # Perform deposit
                savings_account.deposit(amount)
                mpesa_account.balance -= amount  # Deduct from MPesa
                mpesa_account.save()

                # Generate unique transaction ID
                transaction_id = f"TXN{uuid.uuid4().hex[:10].upper()}"

                # Save transaction record
                Transaction.objects.create(
                    transaction_id=transaction_id,
                    transaction_type="DEPOSIT",
                    sender=mpesa_account,  # Money is leaving the MPesa account
                    receiver=None,  # Not transferring to another MPesa account
                    amount=amount,
                    fee=0,  # No fee for savings deposit
                    status="COMPLETED",
                    description=f"Deposit to savings from MPesa by {user.username}",
                )

                messages.success(request, f"Deposited {amount} successfully!")
                return redirect('savings_dashboard')
            else:
                messages.error(request, "Insufficient MPesa balance or invalid amount.")
        except:
            messages.error(request, "Invalid amount entered.")

    return render(request, 'savings/deposit_savings.html')


from decimal import Decimal, InvalidOperation
import uuid

@login_required
def withdraw_savings(request):
    """Allow the user to withdraw money from their savings account to MPesa and record the transaction."""
    user = request.user

    # Ensure the user has both a savings and MPesa account
    if not hasattr(user, 'savings_account'):
        messages.error(request, "You do not have a savings account.")
        return redirect('savings_dashboard')

    if not hasattr(user, 'mpesa_account'):
        messages.error(request, "You need an MPesa account to withdraw money.")
        return redirect('customer_dashboard')

    savings_account = user.savings_account
    mpesa_account = user.mpesa_account

    if request.method == 'POST':
        amount = request.POST.get('amount', '').strip()  # Strip spaces

        try:
            # Convert amount safely to Decimal
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero.")
                return redirect('withdraw_savings')

            if amount > savings_account.balance:
                messages.error(request, "Insufficient savings balance.")
                return redirect('withdraw_savings')

            # Perform withdrawal
            savings_account.withdraw(amount)
            mpesa_account.balance += amount  # Add to MPesa
            mpesa_account.save()

            # Generate unique transaction ID
            transaction_id = f"TXN{uuid.uuid4().hex[:10].upper()}"

            # Save transaction record
            Transaction.objects.create(
                transaction_id=transaction_id,
                transaction_type="WITHDRAWAL",
                sender=mpesa_account,  # ✅ Fix: Set sender as user's MPesa account
                receiver=mpesa_account,  # ✅ MPesa account receives money
                amount=amount,
                fee=0,  # No withdrawal fee for this transaction
                status="COMPLETED",
                description=f"Withdrawal from savings to MPesa by {user.username}",
            )

            messages.success(request, f"Withdrew {amount} successfully!")
            return redirect('savings_dashboard')

        except (ValueError, InvalidOperation):
            messages.error(request, "Invalid amount entered. Please enter a valid number.")

    return render(request, 'savings/withdraw_savings.html')


from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model  # Use the custom User model
from .models import Loan, MPesaAccount, Transaction
from .forms import LoanRequestForm

# Use the custom User model
User = get_user_model()

# Loan tiers
LOAN_TIERS = [
    (100, 0),
    (300, 50),
    (500, 100),
    (1000, 200),
    (2000, 500),
    (5000, 1000),
    (10000, 2000),
]

INTEREST_RATE = Decimal("0.02")  # 2% per day

def request_loan(request):
    """Handle loan requests based on eligibility."""

    user = request.user
    try:
        mpesa_account = MPesaAccount.objects.get(user=user)
    except MPesaAccount.DoesNotExist:
        messages.error(request, "You do not have an M-Pesa account linked.")
        return redirect("customer_dashboard")

    # Get the superuser 'mpesa' as the loan provider
    try:
        mpesa_user = User.objects.get(username="mpesa")  
        system_account = MPesaAccount.objects.get(user=mpesa_user)
    except (User.DoesNotExist, MPesaAccount.DoesNotExist):
        messages.error(request, "System error: M-Pesa account not set up.")
        return redirect("customer_dashboard")

    balance = mpesa_account.balance
    max_loan = 0

    # Check if user has an active loan
    active_loan = Loan.objects.filter(user=user, status="PENDING").exists()
    if active_loan:
        messages.error(request, "You must fully repay your existing loan before taking a new one.")
        return redirect("customer_dashboard")

    # Determine maximum loan based on balance
    for tier_balance, loan_amount in LOAN_TIERS:
        if balance >= tier_balance:
            max_loan = loan_amount

    if request.method == "POST":
        form = LoanRequestForm(user, request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]

            if amount > max_loan:
                messages.error(request, f"You can only borrow up to KES {max_loan}.")
                return redirect("request_loan")

            # Ensure the system has enough funds to issue the loan
            if system_account.balance < amount:
                messages.error(request, "M-Pesa system does not have enough funds to issue this loan.")
                return redirect("request_loan")

            due_date = date.today() + timedelta(days=30)

            # Create Loan object
            loan = Loan.objects.create(
                user=user,
                amount=amount,
                interest_rate=Decimal("2.0"),  
                repayment_due_date=due_date,
                status="PENDING"
            )

            # Deduct loan amount from M-Pesa superuser account
            system_account.balance -= amount
            system_account.save()

            # Add loan amount to borrower's M-Pesa account
            mpesa_account.balance += amount
            mpesa_account.save()

            # Record the transaction
            transaction = Transaction.objects.create(
                transaction_id=f"LN{loan.id}{date.today().strftime('%Y%m%d')}",
                transaction_type="LOAN",
                sender=system_account,  
                receiver=mpesa_account,
                amount=amount,
                status="COMPLETED",
                description=f"Loan issued: KES {amount}"
            )

            messages.success(request, f"Loan request of KES {amount} approved. Due by {due_date}.")
            return redirect("customer_dashboard")  

    else:
        form = LoanRequestForm(user)

    return render(request, "loans/request_loan.html", {"form": form, "max_loan": max_loan})



from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Loan, MPesaAccount, Transaction

User = get_user_model()

from datetime import datetime
import uuid  # Import uuid for unique identifiers

@login_required
def repay_loan(request):
    """Allows users to repay their outstanding loans, updating M-Pesa balances correctly."""

    user = request.user

    try:
        mpesa_account = MPesaAccount.objects.get(user=user)
    except MPesaAccount.DoesNotExist:
        messages.error(request, "You do not have an M-Pesa account linked.")
        return redirect("customer_dashboard")

    try:
        mpesa_user = User.objects.get(username="mpesa")  
        system_account = MPesaAccount.objects.get(user=mpesa_user)
    except (User.DoesNotExist, MPesaAccount.DoesNotExist):
        messages.error(request, "System error: M-Pesa account not set up.")
        return redirect("customer_dashboard")

    active_loan = Loan.objects.filter(user=user, is_paid=False).order_by("-repayment_due_date").first()
    if not active_loan:
        messages.info(request, "You have no active loans to repay.")
        return redirect("customer_dashboard")

    if request.method == "POST":
        amount = request.POST.get("amount")

        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, "Invalid repayment amount.")
                return redirect("repay_loan")

            if amount > mpesa_account.balance:
                messages.error(request, "Insufficient balance in M-Pesa account.")
                return redirect("repay_loan")

            # Deduct from borrower's M-Pesa account
            mpesa_account.balance -= amount
            mpesa_account.save()

            # Credit the amount back to the system M-Pesa account
            system_account.balance += amount
            system_account.save()

            # Debugging: Print loan details before update
            print(f"Before update: Remaining Amount: {active_loan.remaining_amount}, Status: {active_loan.status}, Is Paid: {active_loan.is_paid}")

            # Update the loan balance
            
            active_loan.remaining_amount = max(Decimal(0), active_loan.remaining_amount - amount)

            # If loan is fully repaid
            if active_loan.remaining_amount <= Decimal('0.00'):  # Use Decimal comparison for precision
                active_loan.is_paid = True
                active_loan.status = "REPAID"
                print("Setting loan as REPAID")  # Add more debugging

            # Save all fields at once rather than specifying update_fields
            active_loan.save()  

            # Verify the changes were saved
            active_loan.refresh_from_db()
            print(f"After DB refresh: Remaining Amount: {active_loan.remaining_amount}, Status: {active_loan.status}, Is Paid: {active_loan.is_paid}")

            # Generate a **unique** transaction ID
            unique_id = uuid.uuid4().hex[:8]  # Generate a short unique ID
            transaction_id = f"RP{active_loan.id}{user.id}{unique_id}"  # Ensure uniqueness

            # Save the repayment transaction
            Transaction.objects.create(
                transaction_id=transaction_id,
                transaction_type="PAYMENT",
                sender=mpesa_account,
                receiver=system_account,
                amount=amount,
                status="COMPLETED",
                description=f"Loan repayment of KES {amount}"
            )

            messages.success(request, f"Loan repayment of {amount} was successful!")
            return redirect("customer_dashboard")

        except ValueError:
            messages.error(request, "Invalid amount entered.")

    return render(request, "loans/repay_loan.html", {"loan": active_loan})
