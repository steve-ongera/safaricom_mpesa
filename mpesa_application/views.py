from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
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
                    phone_number = user_form.cleaned_data['phone_number']
                    date_of_birth = user_form.cleaned_data['date_of_birth']
                    first_name = user_form.cleaned_data['first_name']
                    last_name = user_form.cleaned_data['last_name']
                    pin = account_form.cleaned_data['pin']
                    
                    # Check if the phone is already registered
                    if User.objects.filter(phone_number=phone_number).exists():
                        messages.error(request, "This phone number is already registered.")
                        return redirect('register_customer')
                    
                    # Check if this ID has too many phone lines
                    active_lines = PhoneLine.objects.filter(
                        id_number=id_number, 
                        is_active=True
                    ).count()
                    
                    if active_lines >= 5:
                        messages.error(request, "This ID number already has 5 active phone lines.")
                        return redirect('register_customer')
                    
                    # Create the user
                    username = phone_number.replace('+', '')  # Use phone number as username without +
                    email = f"{username}@mpesa.example.com"  # Generate a placeholder email
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=get_random_string(12),  # Generate a random password
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone_number,
                        id_number=id_number,
                        date_of_birth=date_of_birth,
                        is_verified=True  # Agent-verified user
                    )
                    
                    # Create M-PESA account
                    account_number = generate_account_number()
                    pin_hash = hash_pin(pin)
                    
                    mpesa_account = MPesaAccount.objects.create(
                        user=user,
                        account_number=account_number,
                        balance=Decimal('0.00'),
                        pin_hash=pin_hash,
                        is_active=True
                    )
                    
                    # Register the phone line
                    PhoneLine.objects.create(
                        id_number=id_number,
                        phone_number=phone_number,
                        is_active=True
                    )
                    
                    messages.success(request, f"Successfully registered customer {first_name} {last_name} with account number {account_number}")
                    return redirect('registration_success', account_id=mpesa_account.id)
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
    else:
        user_form = CustomerRegistrationForm()
        account_form = MPesaAccountCreationForm()
    
    context = {
        'user_form': user_form,
        'account_form': account_form,
        'agent': request.user.agent_profile
    }
    
    return render(request, 'agent/register_customer.html', context)

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

@login_required
@user_passes_test(is_agent)
def initial_deposit(request, account_id):
    """View for agents to make initial deposit for new customer"""
    agent = request.user.agent_profile
    account = get_object_or_404(MPesaAccount, id=account_id)
    
    # For security, check the account is new with zero balance
    if account.balance > 0:
        messages.warning(request, "This account already has funds and is not eligible for initial deposit")
        return redirect('agent_dashboard')
    
    if request.method == 'POST':
        form = InitialDepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Check if agent has enough float
            if agent.float_balance < amount:
                messages.error(request, "Insufficient float balance to process this deposit")
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
                            f"Deposit amount must be between KES {deposit_limit.min_amount} and KES {deposit_limit.max_amount}"
                        )
                        return redirect('initial_deposit', account_id=account_id)
                    
                    # Create transaction
                    txn_id = generate_transaction_id()
                    
                    # Find or create the agent's own MPesa account 
                    agent_account, _ = MPesaAccount.objects.get_or_create(
                        user=agent.user,
                        defaults={
                            'account_number': f"AG{agent.business_number[-8:]}",
                            'pin_hash': 'agent',  # In a real system, this would be properly secured
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
                        fee=Decimal('0.00'),  # No fee for initial deposit
                        status='COMPLETED',
                        description=f"Initial deposit by agent {agent.business_name}"
                    )
                    
                    # Calculate agent commission (usually none for initial deposit, but can be configured)
                    commission = Decimal('0.00')
                    
                    # Create agent transaction record
                    AgentTransaction.objects.create(
                        transaction=txn,
                        agent=agent,
                        customer=account.user,
                        transaction_type='DEPOSIT',
                        agent_commission=commission
                    )
                    
                    # Update account balance
                    account.balance += amount
                    account.save()
                    
                    # Update agent float
                    agent.float_balance -= amount
                    agent.save()
                    
                    # Create notification for customer
                    Notification.objects.create(
                        user=account.user,
                        notification_type='SMS',
                        title="M-PESA Deposit",
                        message=f"Your M-PESA account has been credited with KES {amount}. New balance: KES {account.balance}. Thank you for using M-PESA!",
                        transaction=txn
                    )
                    
                    messages.success(
                        request, 
                        f"Initial deposit of KES {amount} successfully processed. New account balance: KES {account.balance}"
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