from django.db import models
from django.utils import timezone
from patient.models import Patient
from appointment.models import Appointment, Service

class BillingRecord(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='billing_records', null=True, blank=True, db_constraint=False)

    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='billing_records', db_constraint=False)
    
    patient_name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)    
    date_issued = models.DateTimeField(default=timezone.now)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    
    @property
    def balance(self):
        """Calculate remaining balance"""
        return self.amount - self.amount_paid
    
    def update_payment_status(self):
        """Auto-update payment status based on paid amount"""
        if self.amount_paid >= self.amount:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'unpaid'
    def save(self, *args, **kwargs):
        # Auto-fill patient_name from patient FK
        if self.patient and not self.patient_name:
            self.patient_name = self.patient.name

        self.update_payment_status()
        super().save(*args, **kwargs)
    
    def __str__(self):
         return f"Bill for {self.patient_name} - ₱{self.amount} (Balance: ₱{self.balance})"
