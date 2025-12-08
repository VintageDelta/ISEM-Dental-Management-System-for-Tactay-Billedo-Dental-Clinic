def find_next_available_slot(dentist, date, total_duration, preferred_time=None, location=None):
    from datetime import datetime, timedelta
    from .models import Appointment

    clinic_start = datetime.combine(date, datetime.strptime("08:00", "%H:%M").time())
    clinic_end = datetime.combine(date, datetime.strptime("17:00", "%H:%M").time())

    current = datetime.combine(date, preferred_time) if preferred_time else clinic_start

    now = datetime.now()

    # 🔒 Hard stop: never return a slot for a past date
    if date < now.date():
        print("Date is in the past, no slot allowed")
        return None, None

    # If today and chosen time is earlier than now, start from now
    if date == now.date() and current < now:
        current = now.replace(second=0, microsecond=0)

    print("DEBUG")
    print("Preferred:", preferred_time)
    print("Date:", date)
    print("Now:", now)
    print("Current starts at:", current)

    existing = Appointment.objects.filter(
        dentist_name=dentist.name,
        date=date,
        location=location
    ).order_by("time")

    print("Existing appointments:", [(a.time, a.end_time) for a in existing])

    duration = timedelta(minutes=total_duration)

    while current + duration <= clinic_end:
        print("Trying slot:", current.time(), "-", (current + duration).time())

        overlap = False
        for appt in existing:
            appt_start = datetime.combine(date, appt.time)
            appt_end = datetime.combine(date, appt.end_time)

            if not (current + duration <= appt_start or current >= appt_end):
                print("Overlap with:", appt_start.time(), "-", appt_end.time())
                overlap = True
                current = appt_end
                break

        if not overlap:
            print("Found slot")
            return current.time(), (current + duration).time()

        current += timedelta(minutes=1)

    print("No slot found")
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
