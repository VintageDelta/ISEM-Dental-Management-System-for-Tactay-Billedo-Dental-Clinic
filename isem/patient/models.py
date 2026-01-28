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

    created_at = models.DateTimeField(auto_now_add=True)

class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    date = models.DateField()
    dentist = models.CharField(max_length=200)
    services = models.TextField(default='', blank=True)  # Previously "service" or "treatment"
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    findings = models.TextField()  # Previously "diagnosis"
    prescriptions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Treatment History'
        verbose_name_plural = 'Treatment Histories'
    
    def __str__(self):
        return f"{self.patient.name} - {self.date} - {self.procedure}"
    
    


class FinancialHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='financial_history')
    date = models.DateField()
    bill_type = models.CharField(max_length=100, default="")  # e.g., "Consultation", "Treatment", "Cleaning"
    payment_mode = models.CharField(max_length=50, default="Cash")  # e.g., "Cash", "Card", "GCash"
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Amount paid
    total_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total bill amount
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Remaining balance
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Billing History'
        verbose_name_plural = 'Billing Histories'
    
    def __str__(self):
        return f"{self.patient.name} - {self.date} - ₱{self.amount}"


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
    
class Xray(models.Model):
    patient = models.ForeignKey(Patient, related_name = 'xrays', on_delete=models.CASCADE)
    file = models.FileField(upload_to='xrays/')
    description = models.TextField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

def __str__(self):
        return f"Xray for {self.patient.name} uploaded on {self.uploaded_at}"