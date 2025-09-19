from django.db import models
from django.utils import timezone

class BillingRecrd(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    )

    patient_name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)   
    date_issued = models.DateTimeField(default=timezone.now)

# Create your models here.
