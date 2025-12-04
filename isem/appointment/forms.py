from django import forms
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['dentist_name', 'location', 'date', 'time', 'services', 'reason', 'email']
        widgets = {
            'services': forms.CheckboxSelectMultiple()
        }
