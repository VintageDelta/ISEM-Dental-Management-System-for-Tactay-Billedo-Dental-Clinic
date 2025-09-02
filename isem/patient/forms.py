from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'address', 'telephone', 'age', 'occupation', 'status', 'complaint']