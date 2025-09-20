from django.db import models

# table for Dentist
class Dentist(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# table for services
class Service(models.Model):
    service_name = models.CharField(max_length=255)
    duration = models.TimeField()

    def __str__(self):
        return self.service_name
    
class Appointment(models.Model):
    
    dentist_name = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=20, null=False)
    date = models.DateField(null=False, blank=False)
    time = models.TimeField(null=False, blank=False)
    servicetype = models.CharField(max_length=255)
    reason = models.TextField()
    email = models.EmailField(null=False, blank=False)
    id_no = models.CharField(max_length=255,null=False, blank=False)
    
    def __str__(self):
        return self.id
    