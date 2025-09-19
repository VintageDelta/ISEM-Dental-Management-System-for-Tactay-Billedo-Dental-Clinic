from django.db import models


class Patient(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    telephone = models.CharField(max_length=11, null=False, blank=False)
    age = models.PositiveIntegerField()
    occupation = models.CharField(max_length=100, blank=True, null=True)
 
 
    is_guest = models.BooleanField(default=False)  # New field to identify guest patients
    guest_id = models.CharField(max_length=50, blank=True, null=True)  # New field for guest ID
    

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

def __str__(self):
        return f"Financial Record {self.number} for {self.patient.name}"