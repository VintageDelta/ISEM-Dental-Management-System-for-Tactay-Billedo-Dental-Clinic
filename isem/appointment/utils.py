# appointment/utils.py
def find_next_available_slot(dentist, service, date, preferred_time=None):
    from datetime import datetime, timedelta
    from .models import Appointment

    # Clinic working hours
    clinic_start = datetime.combine(date, datetime.strptime("08:00", "%H:%M").time())
    clinic_end = datetime.combine(date, datetime.strptime("17:00", "%H:%M").time())

    # Start from preferred time or clinic start
    current = datetime.combine(date, preferred_time) if preferred_time else clinic_start

    # Get dentist's appointments that day
    existing = Appointment.objects.filter(
        dentist_name=dentist.name, date=date
    ).order_by("time")

    # Iterate until closing time
    while current + timedelta(minutes=service.duration) <= clinic_end:
        overlap = False
        for appt in existing:
            appt_start = datetime.combine(date, appt.time)
            appt_end = datetime.combine(date, appt.end_time)

            # Check if proposed slot overlaps with an existing one
            if not (current + timedelta(minutes=service.duration) <= appt_start or current >= appt_end):
                overlap = True
                current = appt_end  # jump to end of conflict
                break

        if not overlap:
            return current.time(), (current + timedelta(minutes=service.duration)).time()

    # No slots available
    return None, None