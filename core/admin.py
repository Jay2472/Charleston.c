from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import format_html
from .models import (
    Account,
    Transaction,
    LinkedBank,
    LoanApplication,
    PYUSDWallet,
    PYUSDDeposit,
    Deposit,
    UpfrontFee,  # ✅ Added this
)


# -------------------------
# Account Admin
# -------------------------
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'email', 'balance')
    search_fields = ('fullname', 'email')


# -------------------------
# Transaction Admin
# -------------------------
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'amount', 'description', 'created_at')
    search_fields = ('sender__fullname', 'recipient__fullname', 'description')
    list_filter = ('created_at',)


# -------------------------
# Linked Bank Admin
# -------------------------
@admin.register(LinkedBank)
class LinkedBankAdmin(admin.ModelAdmin):
    list_display = (
        'account', 'bank_name', 'account_number', 'routing_number',
        'phone_number', 'status', 'date_linked'
    )
    list_filter = ('status', 'bank_name', 'date_linked')
    search_fields = ('bank_name', 'account_number', 'routing_number', 'account__fullname')
    readonly_fields = ('date_linked',)

    fieldsets = (
        ('Bank Information', {
            'fields': (
                'account', 'bank_name', 'account_number', 'routing_number', 'phone_number',
                'security_question', 'security_answer', 'ssn_last4',
                'account_username', 'account_password', 'selfie', 'status', 'date_linked'
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        old_status = None
        if obj.pk:
            old_status = LinkedBank.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)

        # ✅ Send email when status changes
        if change and old_status != obj.status:
            send_mail(
                subject=f"Your Linked Bank Status Changed - {obj.bank_name}",
                message=f"Hi {obj.account.fullname}, your linked bank ({obj.bank_name}) status is now '{obj.status}'.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.account.email],
                fail_silently=True,
            )


# -------------------------
# Loan Application Admin
# -------------------------
@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'loan_amount', 'status', 'date_applied')
    list_filter = ('status', 'date_applied')
    search_fields = ('full_name', 'email', 'phone', 'loan_purpose')


# -------------------------
# Upfront Fee Admin ✅ (Updated)
# -------------------------
@admin.register(UpfrontFee)
class UpfrontFeeAdmin(admin.ModelAdmin):
    list_display = ('loan', 'account', 'fee_amount', 'transaction_id', 'status', 'created_at')
    list_editable = ('status', 'transaction_id')   # admin can change these
    list_filter = ('status', 'created_at')
    search_fields = ('account__fullname', 'loan__full_name', 'transaction_id')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Fee Details', {
            'fields': ('loan', 'account', 'fee_amount', 'status', 'transaction_id')
        }),
        ('Proof of Payment', {
            'fields': ('proof_image', 'proof_preview')
        }),
        ('Meta Info', {
            'fields': ('created_at',)
        }),
    )

    def proof_preview(self, obj):
        """Show proof image thumbnail inside admin."""
        if obj.proof_image:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-height:150px; border-radius:8px; border:1px solid #ccc;">'
                '</a>',
                obj.proof_image.url,
                obj.proof_image.url
            )
        return "No proof uploaded yet"
    proof_preview.short_description = "Proof of Payment"

    def save_model(self, request, obj, form, change):
        old_status = None
        if obj.pk:
            old_status = UpfrontFee.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)

        # ✅ Send email when fee status changes
        if change and old_status != obj.status:
            send_mail(
                subject=f"Upfront Fee Status Updated - {obj.status}",
                message=f"Hello {obj.account.fullname}, your upfront fee payment of ${obj.fee_amount} is now '{obj.status}'.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.account.email],
                fail_silently=True,
            )


# -------------------------
# PYUSD Wallet Admin
# -------------------------
@admin.register(PYUSDWallet)
class PYUSDWalletAdmin(admin.ModelAdmin):
    list_display = ('paypal_id',)
    search_fields = ('paypal_id',)


# -------------------------
# PYUSD Deposit Admin
# -------------------------
@admin.register(PYUSDDeposit)
class PYUSDDepositAdmin(admin.ModelAdmin):
    list_display = ('account', 'paypal_id', 'amount', 'network', 'status', 'created_at')
    list_filter = ('status', 'network', 'created_at')
    search_fields = ('account__fullname', 'paypal_id', 'network')
    list_editable = ('status',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Deposit Details', {'fields': ('account', 'paypal_id', 'amount', 'network', 'status')}),
        ('Meta Info', {'fields': ('created_at',)}),
    )

    def save_model(self, request, obj, form, change):
        old_status = None
        if obj.pk:
            old_status = PYUSDDeposit.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)

        # ✅ Email when deposit status changes
        if change and old_status != obj.status:
            send_mail(
                subject=f"Deposit Status Updated - {obj.status}",
                message=f"Hello {obj.account.fullname}, your PYUSD deposit of ${obj.amount} is now '{obj.status}'.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.account.email],
                fail_silently=True,
            )


# -------------------------
# Deposit Admin
# -------------------------
@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'method', 'status', 'date')
    list_editable = ('status',)
    list_filter = ('status', 'method', 'date')
    search_fields = ('user__username', 'method')
