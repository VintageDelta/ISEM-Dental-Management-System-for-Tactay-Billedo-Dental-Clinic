from django.db import models

class Patient(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    telephone = models.CharField(max_length=20)
    age = models.PositiveIntegerField()
    occupation = models.CharField(max_length=100, blank=True, null=True)
 

    def __str__(self):
        return self.name