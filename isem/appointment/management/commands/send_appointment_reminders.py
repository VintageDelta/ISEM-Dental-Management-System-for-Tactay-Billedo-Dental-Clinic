# appointment/management/commands/send_appointment_reminders.py

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from appointment.models import Appointment, GlobalReminderSetting
from patient.models import Patient
from django.core.mail import send_mail
import requests


class Command(BaseCommand):
    help = "Send scheduled email/SMS reminders for upcoming appointments."

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()

        # Look at appointments in the next 21 days (just a safe window)
        upcoming = Appointment.objects.filter(
            date__gte=today,
            date__lte=today + timedelta(days=21),
            status__in=["not_arrived", "arrived", "ongoing"],
        ).select_related("branch", "patient")

        # Load global reminder settings once
        setting = GlobalReminderSetting.get_solo()
        offsets = setting.get_offsets()
        send_email = setting.send_email
        send_sms = setting.send_sms

        # If no offsets configured, nothing to do
        if not offsets:
            return

        for appt in upcoming:
            # compute how many days remain until appointment date
            days_left = (appt.date - today).days
            if days_left < 0:
                continue

            # if this days_left matches one of the configured offsets, send reminders
            if days_left not in offsets:
                continue

            # actually send notifications (global toggles)
            if send_email:
                self._send_email_reminder(appt)
            if send_sms:
                self._send_sms_reminder(appt)

    def _send_email_reminder(self, appt):
        to_email = appt.email
        if not to_email:
            # fallback from patient FK
            if appt.patient and appt.patient.email:
                to_email = appt.patient.email

        if not to_email:
            return

        date_str = appt.date.strftime("%B %d, %Y")
        time_str = appt.time.strftime("%I:%M %p")

        branch_name = appt.branch.name if appt.branch else "Tactay Billedo Dental Clinic"
        branch_addr = appt.branch.address if appt.branch and appt.branch.address else "our clinic"

        subject = "Upcoming dental appointment reminder"
        message = (
            "Good day!\n\n"
            f"This is a reminder that you have an upcoming appointment at {branch_name} "
            f"({branch_addr}) on {date_str} at {time_str}.\n\n"
            "If you need to reschedule, please contact the clinic.\n\n"
            "Thank you."
        )

        send_mail(
            subject,
            message,
            None,
            [to_email],
            fail_silently=True,
        )

    def _send_sms_reminder(self, appt):
        patient = appt.patient or Patient.objects.filter(email=appt.email).first()
        number = patient.telephone if patient and patient.telephone else None
        if not number:
            return

        date_str = appt.date.strftime("%B %d, %Y")
        time_str = appt.time.strftime("%I:%M %p")

        branch_name = appt.branch.name if appt.branch else "Tactay Billedo Dental Clinic"
        branch_addr = appt.branch.address if appt.branch and appt.branch.address else "our clinic"

        message = (
            f"Reminder: You have an upcoming appointment at {branch_name} "
            f"({branch_addr}) on {date_str} at {time_str}. "
            f"To reschedule, please contact us."
        )

        payload = {
            "apikey": settings.SEMAPHORE_API_KEY,
            "number": number,
            "message": message,
            "sendername": settings.SEMAPHORE_SENDER_NAME,
        }

        requests.post("https://api.semaphore.co/api/v4/messages", data=payload)
