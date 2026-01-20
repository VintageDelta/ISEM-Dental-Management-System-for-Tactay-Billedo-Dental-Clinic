from django.db import models
from django.utils import timezone
from patient.models import Patient
from appointment.models import Appointment, Service

class BillingRecord(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='billing_records', null=True, blank=True, db_constraint=False)

    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='billing_records', db_constraint=False)
    
    patient_name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)   
    date_issued = models.DateTimeField(default=timezone.now)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    

def save(self, *args, **kwargs):
        # Auto-fill patient_name from patient FK
        if self.patient and not self.patient_name:
            self.patient_name = self.patient.name
        super().save(*args, **kwargs)
    
def __str__(self):
        return f"Bill for {self.patient_name} - {self.amount}"
