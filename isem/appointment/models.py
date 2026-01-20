from django.db import models
from datetime import datetime, timedelta
from django.contrib.auth.models import User


class Branch(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    CATEGORY_CHOICES = [
        ("GENERAL", "General / Consultation"),
        ("ENDO", "Endodontics"),
        ("EXTRACTION", "Tooth Extraction"),
        ("IMPLANT", "Implants"),
        ("WHITENING", "Whitening / Bleaching"),
        ("RESTORATION", "Restoration"),
        ("SURGERY", "Surgery"),
        ("REMOVABLE_ARCH", "Removable Prosthodontics (per arch)"),
        ("COMPLETE_DENTURE", "Complete Denture"),
        ("THERMOSENS", "Thermosens"),
        ("IVOCAP", "Ivocap"),
        ("REMOVABLE_WHITE", "Removable Prostho (White Plastic)"),
        ("RPD_METAL", "RPD Metal Framework"),
        ("ORTHO", "Orthodontics"),
        ("FIXED", "Fixed Prosthodontics"),
        ("DENTURE_REPAIR", "Denture Repair"),
    ]

    service_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="GENERAL")
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.service_name


class Dentist(models.Model):
    name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DentistService(models.Model):
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name="dentist_services")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="service_dentists")

    def __str__(self):
        return f"{self.dentist.name} - {self.service.service_name}"


class DentistAvailability(models.Model):
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, related_name="availabilities")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="dentist_availabilities")

    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.dentist.name} @ {self.branch.name} - {self.get_day_of_week_display()}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("not_arrived", "Not Yet Arrived"),
        ("arrived", "Arrived"),
        ("ongoing", "On Going"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
    )

    # NEW: link appointment to actual dentist and branch
    dentist = models.ForeignKey(
        Dentist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
    )
    branch = models.ForeignKey(
        Branch,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
    )

    # keep dentist_name for now if you already have data;
    # later you can remove this after data migration
    dentist_name = models.CharField(max_length=255, null=True, blank=True)

    location = models.CharField(max_length=20, null=False)
    date = models.DateField(null=False, blank=False)
    time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=True, blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    services = models.ManyToManyField(Service, related_name="appointments")
    reason = models.TextField(blank=True)
    email = models.EmailField(null=False, blank=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_arrived",
    )

    @property
    def display_id(self):
        return f"APT-{self.id:06d}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        total_duration = sum(s.duration for s in self.services.all())
        if self.time and self.date and total_duration > 0:
            start_datetime = datetime.combine(self.date, self.time)
            end_datetime = start_datetime + timedelta(minutes=total_duration)
            self.end_time = end_datetime.time()
            super().save(update_fields=["end_time"])

    def __str__(self):
        # prefer real dentist FK if present
        name = self.dentist.name if self.dentist else self.dentist_name
        return f"{name} - {self.date} {self.time} [{self.get_status_display()}]"


class AppointmentLog(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("status_changed", "Status Changed"),
        ("cancelled", "Cancelled"),
    ]

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)
    note = models.TextField(blank=True)
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointment_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.appointment.display_id} - {self.action} at {self.created_at}"
