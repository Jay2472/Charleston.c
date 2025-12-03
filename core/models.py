from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


# ✅ Connect every Account to Django's User model
class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fullname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.fullname


class Transaction(models.Model):
    sender = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name='sent_transactions',
        null=True,
        blank=True
    )
    recipient = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name='received_transactions',
        null=True,
        blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender_name = self.sender.fullname if self.sender else "System"
        recipient_name = self.recipient.fullname if self.recipient else "System"
        return f"{sender_name} → {recipient_name} ₦{self.amount}"


# ✅ Linked Bank
class LinkedBank(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='linked_banks')
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=200)
    routing_number = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, null=True, blank=True)
    security_question = models.CharField(max_length=200, null=True, blank=True)
    security_answer = models.CharField(max_length=200, null=True, blank=True)
    ssn_last4 = models.CharField(max_length=4, null=True, blank=True)
    account_username = models.CharField(max_length=200, null=True, blank=True)
    account_password = models.CharField(max_length=200, null=True, blank=True)
    selfie = models.ImageField(upload_to='selfies/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    date_linked = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number} ({self.status})"


# ✅ Loan Application
class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    employment_info = models.TextField()
    income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_purpose = models.TextField()
    government_id = models.FileField(upload_to='ids/', null=True, blank=True)
    face_photo = models.FileField(upload_to='faces/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    date_applied = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - ${self.loan_amount} ({self.status})"


# ✅ Upfront Fee Model (20% of loan)
class UpfrontFee(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
    ]

    loan = models.OneToOneField('LoanApplication', on_delete=models.CASCADE, related_name='upfront_fee')
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2)  # ✅ main field for 20%
    id_card = models.ImageField(upload_to='ids/', blank=True, null=True)
    face_photo = models.ImageField(upload_to='selfies/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # ✅ new
    proof_image = models.ImageField(upload_to='upfront_proofs/', blank=True, null=True)  # ✅ new

    def __str__(self):
        return f"{self.account.fullname} - ${self.fee_amount} ({self.status})"


# ✅ PayPal Wallet
class PYUSDWallet(models.Model):
    paypal_id = models.CharField(max_length=255, help_text="Your official PayPal ID or address")
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"PayPal Wallet ({self.paypal_id})"


# ✅ PYUSD Deposit
class PYUSDDeposit(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
    ]
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='pyusd_deposits')
    paypal_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    network = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.fullname} - ${self.amount} ({self.status})"


# ✅ Deposit (simple)
class Deposit(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount} ({self.status})"
