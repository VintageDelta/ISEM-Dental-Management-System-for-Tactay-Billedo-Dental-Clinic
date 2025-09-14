from django.db import models

class Patient(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    telephone = models.CharField(max_length=20)
    age = models.PositiveIntegerField()
    occupation = models.CharField(max_length=100, blank=True, null=True)
 
    is_guest = models.BooleanField(default=False)  # New field to identify guest patients
    guest_id = models.CharField(max_length=50, blank=True, null=True)  # New field for guest ID
    
    def __str__(self):
        return self.name