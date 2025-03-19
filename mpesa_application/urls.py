# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Agent dashboard and registration URLs
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/register-customer/', views.register_customer, name='register_customer'),
    path('agent/registration-success/<int:account_id>/', views.registration_success, name='registration_success'),
    path('agent/verify-customer-id/', views.verify_customer_id, name='verify_customer_id'),
    
    # These routes would be implemented in other view modules
    path('agent/transactions/', views.agent_transactions, name='agent_transactions'),
    path('agent/float/', views.agent_float, name='agent_float'),
    path('search-tenant-deposit/', views.search_tenant_deposit, name='search_tenant_deposit'),
    path('agent/initial-deposit/<int:account_id>/', views.initial_deposit, name='initial_deposit'),

    #user views

    path("login/", views.login_view, name="login"),
    path('logout/', views.user_logout, name='logout'),
    path("customer_dashboard/", views.customer_dashboard, name="customer_dashboard"),
    path('search-agent/', views.search_agents, name='search_agents'),
    path('withdraw-from-agent/<int:agent_id>/', views.withdraw_money, name='withdraw_money'),
    path('send-money/', views.send_money, name='send_money'),
    path('check-recipient/', views.check_recipient, name='check_recipient'),
    path("check-balance/", views.check_balance, name="check_balance"),
    path("transaction-history/", views.transaction_history, name="transaction_history"),


    #savings
    path('create-savings/', views.create_savings_account, name='create_savings_account'),
    path('savings-dashboard/', views.savings_dashboard, name='savings_dashboard'),
    path('deposit/', views.deposit_savings, name='deposit_savings'),
    path('withdraw-from-saving-account/', views.withdraw_savings, name='withdraw_savings'),

    #loans
    path('request-loan/', views.request_loan, name='request_loan'),
    path('repay-loan/', views.repay_loan, name='repay_loan'),

]