def find_next_available_slot(dentist, date, total_duration, preferred_time=None, location=None):
    from datetime import datetime, timedelta
    from .models import Appointment

    def round_up_to_interval(dt, minutes=15):
        remainder = dt.minute % minutes
        if remainder:
            dt += timedelta(minutes=(minutes - remainder))
        return dt.replace(second=0, microsecond=0)

    clinic_start = datetime.combine(date, datetime.strptime("08:00", "%H:%M").time())
    clinic_end = datetime.combine(date, datetime.strptime("17:00", "%H:%M").time())

    now = datetime.now()

    # Hard stop: no past dates
    if date < now.date():
        return None, None

    # Starting point
    current = datetime.combine(date, preferred_time) if preferred_time else clinic_start

    # If today, don’t allow past times
    if date == now.date() and current < now:
        current = now

    # Enforce 15-minute slots
    current = round_up_to_interval(current)

    duration = timedelta(minutes=total_duration)

    existing = Appointment.objects.filter(
        dentist_name=dentist.name,
        date=date,
        location=location,
        status__in=["not_arrived", "arrived", "ongoing"]
    ).order_by("time")

    # GAP-BASED SCANNING
    for appt in existing:
        appt_start = datetime.combine(date, appt.time)
        appt_end = datetime.combine(date, appt.end_time)

        # If there’s enough space before this appointment
        if current + duration <= appt_start:
            return current.time(), (current + duration).time()

        # Otherwise jump to the end of this appointment
        current = max(current, appt_end)
        current = round_up_to_interval(current)

    # Check after the last appointment
    if current + duration <= clinic_end:
        return current.time(), (current + duration).time()

    return None, None




    # while current + timedelta(minutes=service.duration) <= clinic_end:
    #     print("Trying slot:", current.time(), "-", (current + timedelta(minutes=service.duration)).time())

    #     overlap = False
    #     for appt in existing:
    #         appt_start = datetime.combine(date, appt.time)
    #         appt_end = datetime.combine(date, appt.end_time)
    #         if not (current + timedelta(minutes=service.duration) <= appt_start or current >= appt_end):
    #             print("Overlap with:", appt_start.time(), "-", appt_end.time())
    #             overlap = True
    #             current = appt_end
    #             break

    #     if not overlap:
    #         print("Found slot")
    #         return current.time(), (current + timedelta(minutes=service.duration)).time()

    #     current += timedelta(minutes=1)

    # print("No slot found")
    # return None, None
