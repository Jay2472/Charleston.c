from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('open-account/', views.open_account, name='open_account'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('transfer/', views.transfer, name='transfer'),

    # Bank linking
    path('link-bank/', views.linked_bank, name='link_bank'),
    path('link-status/<int:bank_id>/', views.link_status, name='link_status'),

    # Deposits
    path('deposit/', views.deposit_view, name='deposit'),
    path('deposit/pyusd/', views.deposit_pyusd, name='deposit_pyusd'),
    path('deposit/status/', views.deposit_status, name='deposit_status'),
    path('withdraw/', views.withdraw_view, name='withdraw'),

    # Loans
    path('loan/', views.loan, name='loan'),
    path('loan/<int:loan_id>/fee/', views.upfront_fee, name='upfront_fee'),
    path('loan/<int:loan_id>/status/', views.loan_status, name='loan_status'),
    path('loan/terms/', views.loan_terms, name='loan_terms'),  # ✅ new page

    # Support
    path('support/', views.support, name='support'),

    
    

]
