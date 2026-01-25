# utils.py
def find_next_available_slot(dentist, date, total_duration, preferred_time=None, location=None):
    """
    Greedy slot finder with a simple scoring (points) system.

    Greedy idea:
    - Generate candidate start times from clinic_start to clinic_end in 15-min steps.
    - For each candidate, if it fits (no overlap), compute a score:
        +10 if >= preferred_time (if provided)
        + up to +5 the closer it is to preferred_time
        + higher score for earlier in the day (so we fill earlier slots first)
    - Return the feasible slot with the highest score (most 'greedy' according to our criteria).
    """
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

    # Starting point baseline
    baseline = clinic_start

    # If a preferred_time is provided, use it as a reference for scoring
    preferred_dt = None
    if preferred_time:
        preferred_dt = datetime.combine(date, preferred_time)
        # if today and preferred is in the past, clamp to now
        if date == now.date() and preferred_dt < now:
            preferred_dt = now

    # Fetch existing relevant appointments once (greedy interval check)
    existing = Appointment.objects.filter(
        dentist_name=dentist.name,
        date=date,
        location=location,
        status__in=["not_arrived", "arrived", "ongoing"]
    ).order_by("time")

    duration = timedelta(minutes=total_duration)

    candidates = []

    # Generate all 15-min candidate starts within clinic hours
    current = round_up_to_interval(clinic_start)
    while current + duration <= clinic_end:
        # Skip past times if date is today
        if date == now.date() and current < now:
            current += timedelta(minutes=15)
            continue

        # Check overlap with existing appointments
        overlaps = False
        for appt in existing:
            appt_start = datetime.combine(date, appt.time)
            appt_end = datetime.combine(date, appt.end_time)
            # overlap if they intersect
            if not (current + duration <= appt_start or current >= appt_end):
                overlaps = True
                break

        if not overlaps:
                # Candidate is feasible – compute greedy score (points)
            score = 0

            # 1) Prefer starting at or after preferred time (if any)
            if preferred_dt:
                if current >= preferred_dt:
                    score += 20  # strong preference: do not go earlier than requested

                # 2) Closeness to preferred time: closer gets more points
                diff_minutes = abs((current - preferred_dt).total_seconds()) / 60.0
                if diff_minutes <= 60:
                    # 0, 5, 4, 3, 2, 1 as it moves away in 12‑minute steps
                    score += int(5 - diff_minutes // 12)

            # 3) Strong preference for earlier in the day
            # Map 08:00 -> +10, 17:00 -> 0
            day_fraction = (current - clinic_start) / (clinic_end - clinic_start)
            score += int(10 * (1.0 - day_fraction))

            candidates.append((score, current))


        current += timedelta(minutes=15)

    if not candidates:
        return None, None

    # If we have a preferred time, first try to pick the earliest feasible slot >= preferred
    if preferred_dt:
        after_pref = [c for c in candidates if c[1] >= preferred_dt]
        if after_pref:
            after_pref.sort(key=lambda x: x[1])  # earliest time
            best_score, best_start = after_pref[0]
            best_end = best_start + duration
            print(f"[GREEDY] Picked slot {best_start.time()}–{best_end.time()} (>= preferred)")
            return best_start.time(), best_end.time()

    # Fallback: no slot >= preferred; pick earliest overall
    candidates.sort(key=lambda x: x[1])
    best_score, best_start = candidates[0]
    best_end = best_start + duration
    print(f"[GREEDY] Picked slot {best_start.time()}–{best_end.time()} (fallback earliest)")
    return best_start.time(), best_end.time()

