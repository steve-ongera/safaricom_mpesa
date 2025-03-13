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
    path('agent/initial-deposit/<int:account_id>/', views.initial_deposit, name='initial_deposit'),

    #user views

    path("login/", views.login_view, name="login"),
    path('logout/', views.user_logout, name='logout'),
    path("customer_dashboard/", views.customer_dashboard, name="customer_dashboard"),
    path('search-agent/', views.search_agents, name='search_agents'),
    path('withdraw/<int:agent_id>/', views.withdraw_money, name='withdraw_money'),
    path('send-money/', views.send_money, name='send_money'),
    path('check-recipient/', views.check_recipient, name='check_recipient'),
    path("check-balance/", views.check_balance, name="check_balance"),
    path("transaction-history/", views.transaction_history, name="transaction_history"),

]