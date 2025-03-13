from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, MPesaAccount, Agent, PhoneLine, Transaction,
    AgentTransaction, Bill, Notification, Limit, UserLimit
)

# Register the custom User model with a custom admin class
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'id_number', 'is_verified', 'is_staff')
    list_filter = ('is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone_number', 'id_number')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom User Fields', {'fields': ('phone_number', 'id_number', 'date_of_birth', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom User Fields', {'fields': ('phone_number', 'id_number', 'date_of_birth', 'is_verified')}),
    )

class MPesaAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'balance', 'is_active', 'created_at', 'last_activity')
    list_filter = ('is_active',)
    search_fields = ('account_number', 'user__username', 'user__phone_number')
    readonly_fields = ('created_at', 'last_activity')

class AgentAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'business_number', 'user', 'location', 'float_balance', 'is_active', 'commission_rate')
    list_filter = ('is_active',)
    search_fields = ('business_name', 'business_number', 'user__username', 'location')

class PhoneLineAdmin(admin.ModelAdmin):
    list_display = ('id_number', 'phone_number', 'is_active', 'registration_date')
    list_filter = ('is_active',)
    search_fields = ('id_number', 'phone_number')
    readonly_fields = ('registration_date',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'transaction_type', 'sender', 'receiver', 'amount', 'fee', 'status', 'timestamp')
    list_filter = ('transaction_type', 'status', 'timestamp')
    search_fields = ('transaction_id', 'sender__account_number', 'receiver__account_number', 'description')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

class AgentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'agent', 'customer', 'transaction_type', 'agent_commission')
    list_filter = ('transaction_type', 'agent')
    search_fields = ('transaction__transaction_id', 'agent__business_name', 'customer__username')

class BillAdmin(admin.ModelAdmin):
    list_display = ('biller_name', 'bill_type', 'account_number', 'amount', 'due_date', 'is_paid')
    list_filter = ('bill_type', 'is_paid', 'due_date')
    search_fields = ('biller_name', 'account_number', 'payment_transaction__transaction_id')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'timestamp')
    list_filter = ('notification_type', 'is_read', 'timestamp')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('timestamp',)

class LimitAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'min_amount', 'max_amount', 'daily_limit', 'is_active')
    list_filter = ('transaction_type', 'is_active')

class UserLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'max_amount', 'daily_limit')
    list_filter = ('transaction_type',)
    search_fields = ('user__username',)



from django.contrib import admin
from .models import SavingsAccount

@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'balance', 'created_at')
    search_fields = ('user__username', 'account_number')
    list_filter = ('created_at',)
    readonly_fields = ('account_number', 'created_at')  # Prevent modifications


from django.contrib import admin
from .models import Loan, Transaction

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status',  'created_at')
    list_filter = ('status', )
    search_fields = ('user__username', 'amount')
    ordering = ('-created_at',)



# Register all models with their respective admin classes
admin.site.register(User, CustomUserAdmin)
admin.site.register(MPesaAccount, MPesaAccountAdmin)
admin.site.register(Agent, AgentAdmin)
admin.site.register(PhoneLine, PhoneLineAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(AgentTransaction, AgentTransactionAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Limit, LimitAdmin)
admin.site.register(UserLimit, UserLimitAdmin)