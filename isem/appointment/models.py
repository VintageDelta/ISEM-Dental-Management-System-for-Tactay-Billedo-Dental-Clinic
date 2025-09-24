from django.db import models
from datetime import datetime, timedelta

# table of Dentist
class Dentist(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# table of services
class Service(models.Model):
    service_name = models.CharField(max_length=255)
    duration = models.IntegerField(help_text="Duration in minutes")  # store clean minutes

    def __str__(self):
        return self.service_name
    
class Appointment(models.Model):
    STATUS_CHOICES = [
        ("not_arrived", "Not Yet Arrived"),
        ("arrived", "Arrived"),
        ("ongoing", "On Going"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    dentist_name = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=20, null=False)
    date = models.DateField(null=False, blank=False)
    time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=True, blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    servicetype = models.ForeignKey(Service, on_delete=models.CASCADE)
    reason = models.TextField()
    email = models.EmailField(null=False, blank=False)
    id_no = models.CharField(max_length=255, null=False, blank=False)

    # NEW FIELD
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_arrived"
    )

    def save(self, *args, **kwargs):
        if self.time and self.servicetype and self.date:
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(self.date, self.time)
            end_datetime = start_datetime + timedelta(minutes=self.servicetype.duration)
            self.end_time = end_datetime.time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dentist_name} - {self.date} {self.time} [{self.get_status_display()}]"

    