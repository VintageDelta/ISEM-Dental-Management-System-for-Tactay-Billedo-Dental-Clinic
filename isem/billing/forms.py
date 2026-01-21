from django import forms
from .models import BillingRecord
from patient.models import Patient
from appointment.models import Appointment


class BillingRecordForm(forms.ModelForm):
    
    # Custom field for patient selection
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
        }),
        label="Patient"
    )
    
    # Custom field for appointment (optional)
    appointment = forms.ModelChoiceField(
        queryset=Appointment.objects.filter(status='done'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
        }),
        label="Appointment (Optional)",
        empty_label="-- None --"
    )
    
    class Meta:
        model = BillingRecord
        fields = ['patient', 'appointment', 'type', 'amount', 'payment_status']
        widgets = {
            'type': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Check-up, Cleaning, Extraction'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            }),
        }
        labels = {
            'type': 'Service Type',
            'amount': 'Amount (₱)',
            'payment_status': 'Payment Status',
        }
