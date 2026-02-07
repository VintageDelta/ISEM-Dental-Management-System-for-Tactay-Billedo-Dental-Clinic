def find_next_available_slot(dentist, date, total_duration, preferred_time=None, location=None):
    """
    Greedy slot finder with a simple scoring (points) system.
    """
    from datetime import datetime, timedelta
    from .models import Appointment

    def round_up_to_interval(dt, minutes=5):
        remainder = dt.minute % minutes
        if remainder:
            dt += timedelta(minutes=(minutes - remainder))
        return dt.replace(second=0, microsecond=0)

    clinic_start = datetime.combine(date, datetime.strptime("08:00", "%H:%M").time())
    clinic_end   = datetime.combine(date, datetime.strptime("17:00", "%H:%M").time())
    now = datetime.now()

    # Hard stop: no past dates
    if date < now.date():
        print("[GREEDY] Date is in the past, no slot.")
        return None, None

    # Preferred datetime
    preferred_dt = None
    if preferred_time:
        preferred_dt = datetime.combine(date, preferred_time)
        if date == now.date() and preferred_dt < now:
            preferred_dt = now

    # Existing appointments for overlap check
    existing = Appointment.objects.filter(
        dentist_name=dentist.name,
        date=date,
        location=location,
        status__in=["not_arrived", "arrived", "ongoing"],
    ).order_by("time")

    print(f"[GREEDY] Existing appts for {dentist.name} @ {location} on {date}:")
    for appt in existing:
        appt_start = datetime.combine(date, appt.time)
        if appt.end_time:
            appt_end = datetime.combine(date, appt.end_time)
        else:
            appt_duration = sum((s.duration or 0) for s in appt.services.all())
            appt_end = appt_start + timedelta(minutes=appt_duration)
        print(f"    - #{appt.id}: {appt_start.time()}–{appt_end.time()} status={appt.status}")

    duration = timedelta(minutes=total_duration)
    print(f"[GREEDY] total_duration={total_duration} minutes")

    candidates = []

    current = round_up_to_interval(clinic_start)
    while current + duration <= clinic_end:
        # Skip past times if today
        if date == now.date() and current < now:
            current += timedelta(minutes=5)
            continue

        # Overlap check
        overlaps = False
        for appt in existing:
            appt_start = datetime.combine(date, appt.time)
            if appt.end_time:
                appt_end = datetime.combine(date, appt.end_time)
            else:
                appt_duration = sum((s.duration or 0) for s in appt.services.all())
                appt_end = appt_start + timedelta(minutes=appt_duration)

            if not (current + duration <= appt_start or current >= appt_end):
                print(f"[GREEDY] Candidate {current.time()}–{(current+duration).time()} OVERLAPS "
                      f"#{appt.id} {appt_start.time()}–{appt_end.time()}")
                overlaps = True
                break

        if not overlaps:
            # Candidate is feasible – compute score
            score = 0
            reason_bits = []

            # 1) After preferred
            if preferred_dt:
                if current >= preferred_dt:
                    score += 20
                    reason_bits.append("+20 after preferred")
                diff_minutes = abs((current - preferred_dt).total_seconds()) / 60.0
                if diff_minutes <= 60:
                    bonus = int(5 - diff_minutes // 12)
                    score += bonus
                    reason_bits.append(f"+{bonus} near preferred ({diff_minutes:.0f} min away)")

            # 3) Earlier in the day
            day_fraction = (current - clinic_start) / (clinic_end - clinic_start)
            early_bonus = int(10 * (1.0 - day_fraction))
            score += early_bonus
            reason_bits.append(f"+{early_bonus} earlier in day")

            print(f"[GREEDY] Candidate {current.time()}–{(current+duration).time()} "
                  f"score={score} ({', '.join(reason_bits)})")

            candidates.append((score, current))

        current += timedelta(minutes=15)

    if not candidates:
        print("[GREEDY] No feasible candidates.")
        return None, None

    # Pick best >= preferred if any
    if preferred_dt:
        after_pref = [c for c in candidates if c[1] >= preferred_dt]
        if after_pref:
            after_pref.sort(key=lambda x: x[0], reverse=True)
            best_score, best_start = after_pref[0]
            best_end = best_start + duration
            print(f"[GREEDY] Picked slot {best_start.time()}–{best_end.time()} (>= preferred, score={best_score})")
            return best_start.time(), best_end.time()

    # Fallback: earliest overall
    candidates.sort(key=lambda x: x[1])
    best_score, best_start = candidates[0]
    best_end = best_start + duration
    print(f"[GREEDY] Picked slot {best_start.time()}–{best_end.time()} (fallback earliest, score={best_score})")
    return best_start.time(), best_end.time()
