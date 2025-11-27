from django import forms
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['dentist_name', 'location', 'date', 'time', 'services', 'reason', 'email', 'id_no']
        widgets = {
            'services': forms.CheckboxSelectMultiple()
        }
