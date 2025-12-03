from django import forms
from .models import LinkedBank

class LinkedBankForm(forms.ModelForm):
    class Meta:
        model = LinkedBank
        fields = [
            'bank_name',
            'account_number',
            'routing_number',
            'phone_number',
            'security_question',
            'security_answer',
            'ssn_last4',
            'account_username',
            'account_password',
            'selfie'
        ]
