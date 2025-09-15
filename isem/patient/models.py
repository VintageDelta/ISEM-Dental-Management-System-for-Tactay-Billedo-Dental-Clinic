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
    patient = models.ForeignKey(Patient,
                                on_delete=models.CASCADE,
                                related_name='medical_history')  # or any name you prefer
    ...

class FinancialHistory(models.Model):
    patient = models.ForeignKey(Patient,
                                on_delete=models.CASCADE,
                                related_name='financial_history')  # or any name you prefer
    date = models.DateField()
    number = models.AutoField(primary_key=True)
    description = models.TextField()
    time = models.TimeField()
    type = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

def __str__(self):
        return f"Financial Record {self.number} for {self.patient.name}"