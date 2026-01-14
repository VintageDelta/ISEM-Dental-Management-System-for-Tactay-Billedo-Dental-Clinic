from django.db import models
from django.contrib.auth.models import User

from appointment.models import Service


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_patient', 
                                null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    telephone = models.CharField(max_length=11, null=False, blank=False)
    age = models.PositiveIntegerField()
    occupation = models.CharField(max_length=100, blank=True, null=True)
 
 
    is_guest = models.BooleanField(default=False)  
    guest_id = models.CharField(max_length=50, blank=True, null=True)  
    
    #Medical data fields
    particular_condition = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    allergy = models.CharField(max_length=255, blank=True, null=True)
    pregnancy_status = models.CharField(max_length=255, blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    abnormal_bleeding_history = models.TextField(blank=True, null=True)

class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, related_name="medical_history", on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    dentist = models.CharField(max_length=255, blank=True)
    reason = models.TextField(blank=True)
    diagnosis = models.TextField(null=True, blank=True)
    service = models.CharField(blank=True, max_length=255)
    treatment = models.TextField(blank=True)
    prescriptions = models.TextField(blank=True)   
    


class FinancialHistory(models.Model):
    patient = models.ForeignKey(Patient,
                                on_delete=models.CASCADE,
                                related_name='financial_history')  
    date = models.DateField(blank=True, null=True)
    number = models.AutoField(primary_key=True) 
    description = models.TextField(blank=True, null=True)
    time = models.TimeField()
    type = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class Odontogram(models.Model):
    patient = models.ForeignKey(Patient, related_name="odontograms", on_delete=models.CASCADE)
    tooth_number = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)
    service = models.ManyToManyField(Service, blank=True)
    # condition = models.CharField(max_length=255)
    # treatment = models.CharField(max_length=255, blank=True, null=True)
    dentist = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    # notes = models.TextField(blank=True, null=True)
    

def __str__(self):
        return f"Odontogram for {self.patient.name} - Tooth {self.tooth_number}"