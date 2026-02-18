# views.py

import json
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Case, When, IntegerField
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test

from decimal import Decimal

from billing.models import BillingRecord
from patient.models import Patient

from .forms import AppointmentForm
from .models import Dentist, Service, Appointment, AppointmentLog,Branch
from .utils import find_next_available_slot

def is_staff_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_staff_or_superuser)
def appointment_logs(request):
    logs = (
        AppointmentLog.objects
        .select_related("appointment", "actor")
        .order_by("-created_at")
    )
    return render(request, "appointment/appointment_logs.html", {"logs": logs})

@csrf_exempt
@require_POST
def update_status(request, appointment_id):
    try:
        # DEBUGS
        print("=" * 50)
        print("UPDATE_STATUS VIEW CALLED")
        print(f"Appointment ID: {appointment_id}")
        print(f"Request body: {request.body}")
        print(f"Content-Type: {request.META.get('CONTENT_TYPE')}")

        data = json.loads(request.body)
        status = data.get("status")
        note = data.get("note") 
        print(f"Parsed status: {status}")
        amount_paid_raw = data.get("amount_paid")
        amount_paid = Decimal(amount_paid_raw) if amount_paid_raw is not None else Decimal("0")

        print("Parsed amount_paid:", amount_paid)

        appointment = Appointment.objects.get(id=appointment_id)

        old_status = appointment.status
        new_status = status

        appointment.status = new_status
        print(f"Found appointment: {appointment}")
        appointment.save()

        # create log only if status actually changed
        if old_status != new_status:
            log_note = None
            if new_status == "cancelled" and note:
                log_note = f"Status changed from {old_status or '-'} to cancelled. Reason: {note}"
            else:
                log_note = f"Status changed from {old_status or '-'} to {new_status}"

            AppointmentLog.objects.create(
                appointment=appointment,
                action="status_changed",
                old_status=old_status,
                new_status=new_status,
                actor=request.user if request.user.is_authenticated else None,
                note=log_note,
            )


        print(f"✓ Appointment status updated to: {status}")

        # If status is 'done', create a billing record
        if status == "done":
            if not BillingRecord.objects.filter(appointment=appointment).exists():
                print("No existing billing record, creating one...")
                patient = None

                if appointment.email:
                    patient = Patient.objects.filter(email=appointment.email).first()
                    print(f"Found patient: {patient}")

                if patient:
                    total_amount = sum(
                        (service.price or 0)
                        for service in appointment.services.all()
                    )

                    service_names = ", ".join(
                        [s.service_name for s in appointment.services.all()]
                    )
                    print(
                        f"Creating billing: amount={total_amount}, "
                        f"type={service_names}"
                    )

                    BillingRecord.objects.create(
                        patient=patient,
                        appointment=appointment,
                        type=service_names,
                        amount=total_amount,
                        amount_paid=amount_paid,
                        date_issued=timezone.now(),
                    )
                    print("✓ Billing record created")
                else:
                    print("⚠ No patient found, billing not created")
            else:
                print("Billing record already exists.")

        print(">>> Returning success response")
        return JsonResponse({"success": True, "status": status})

    except Appointment.DoesNotExist:
        print(f"❌ Appointment {appointment_id} not found")
        return JsonResponse(
            {"success": False, "error": "Appointment not found"}, status=404
        )
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def notify_patient_email(request, appointment_id):
    try:
        appt = Appointment.objects.get(id=appointment_id)

        # Use the appointment's stored email, date, time
        to_email = appt.email
        if not to_email:
            return JsonResponse(
                {"success": False, "error": "No patient email on this appointment."},
                status=400,
            )

        date_str = appt.date.strftime("%B %d, %Y")  # e.g. January 22, 2026
        time_str = appt.time.strftime("%I:%M %p")   # e.g. 09:30 AM

        branch_name = appt.branch.name if appt.branch else "Tactay Billedo Dental Clinic"
        branch_addr = appt.branch.address if appt.branch and appt.branch.address else "our clinic"

        subject = "Your appointment schedule"
        message = (
            "Good day!\n\n"
            f"This is a reminder that you have an appointment at {branch_name} "
            f"({branch_addr}) on {date_str} at {time_str}.\n\n"
            "Please be in time. If you need to reschedule, please contact the clinic.\n\n"
            "Thank you."
        )

        send_mail(
            subject,
            message,
            None,        # uses DEFAULT_FROM_EMAIL from settings.py
            [to_email],
            fail_silently=False,
        )

        # Optionally log this action
        AppointmentLog.objects.create(
            appointment=appt,
            action="updated",
            note="Patient notified by email",
            actor=request.user if request.user.is_authenticated else None,
        )

        return JsonResponse({"success": True})
    except Appointment.DoesNotExist:
        return JsonResponse({"success": False, "error": "Appointment not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def notify_patient_sms(request, appointment_id):
    try:
        appt = Appointment.objects.get(id=appointment_id)

        patient = appt.patient or Patient.objects.filter(email=appt.email).first()
        number = patient.telephone if patient and patient.telephone else None

        if not number:
            return JsonResponse(
                {"success": False, "error": "No patient mobile number available."},
                status=400,
            )

        date_str = appt.date.strftime("%B %d, %Y")
        time_str = appt.time.strftime("%I:%M %p")

        branch_name = appt.branch.name if appt.branch else "Tactay Billedo Dental Clinic"
        branch_addr = appt.branch.address if appt.branch and appt.branch.address else "our clinic"

        message = (
            f"Reminder: You have an appointment at {branch_name} "
            f"({branch_addr}) on {date_str} at {time_str}. "
            f"Please be in time. If you need to reschedule, please contact us."
        )
        payload = {
            "apikey": settings.SEMAPHORE_API_KEY,
            "number": number,
            "message": message,
            "sendername": settings.SEMAPHORE_SENDER_NAME,
        }

        if settings.SEMAPHORE_SENDER_NAME:
            payload["sendername"] = settings.SEMAPHORE_SENDER_NAME

        resp = requests.post("https://api.semaphore.co/api/v4/messages", data=payload)

        try:
            data = resp.json()
        except Exception:
            data = None

        if resp.status_code == 200 and isinstance(data, list) and data and data[0].get("status") != "failed":
            AppointmentLog.objects.create(
                appointment=appt,
                action="updated",
                note="Patient notified by SMS",
                actor=request.user if request.user.is_authenticated else None,
            )
            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {"success": False, "error": "SMS sending failed."},
                status=400,
            )
    except Appointment.DoesNotExist:
        return JsonResponse({"success": False, "error": "Appointment not found."}, status=404)
    except Exception as e:
        print("SMS notify exception:", e)
        return JsonResponse({"success": False, "error": str(e)}, status=400)


def create_followup(request):
    """
    Create a follow-up appointment based on an existing appointment.
    Expects POST with: original_id, date (YYYY-MM-DD), time (HH:MM 24h).
    """
    if request.method != "POST":
        return redirect("appointment:appointment_page")

    original_id = request.POST.get("original_id")
    date_str = request.POST.get("date")
    time_str = request.POST.get("time")

    # Safety: make sure these exist
    if not (original_id and date_str and time_str):
        messages.error(request, "Missing follow-up date or time.")
        return redirect("appointment:appointment_page")

    original = get_object_or_404(Appointment, pk=original_id)

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        time_obj = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        messages.error(request, "Invalid follow-up date or time.")
        return redirect("appointment:appointment_page")

    # Block any follow-up date before today (same rule as main create)
    if date_obj < datetime.now().date():
        messages.error(request, "You cannot create a follow-up in the past.")
        return redirect("appointment:appointment_page")

    # Reuse original dentist/location/services/email
    dentist_name = original.dentist_name
    location = original.location
    selected_services = list(original.services.all())
    total_minutes = sum(s.duration for s in selected_services)

    # Find a valid slot using your existing util
    with transaction.atomic():
        start_time, end_time = find_next_available_slot(
        Dentist.objects.get(name=dentist_name),
        date_obj,
        total_minutes,
        time_obj,
        location=location,
    )

    if not start_time or not end_time:
        messages.error(
            request,
            "No available time slot for the selected follow-up date and services.",
        )
        return redirect("appointment:appointment_page")

    followup = Appointment.objects.create(
        user=request.user if request.user.is_authenticated else original.user,
        dentist_name=dentist_name,
        location=location,
        date=date_obj,
        time=start_time,
        end_time=end_time,
        preferred_date=date_obj,
        preferred_time=time_obj,
        email=original.email,
        followup_of=original,  # NEW: link child to original
    )
    followup.services.set(selected_services)
    
    AppointmentLog.objects.create(
        appointment=followup,
        action="created",
        new_status=followup.status,
        actor=request.user if request.user.is_authenticated else None,
        note=f"Follow-up created from appointment {original.id}",
    )

    # NEW: if this was an AJAX follow-up creation, return JSON with IDs/date
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "followup_id": followup.id,
            "followup_date": followup.date.strftime("%Y-%m-%d"),
        })

    messages.add_message(
        request,
        messages.SUCCESS,
        "Follow-up appointment successfully created!",
        extra_tags="appointment_created",
    )
    return redirect("appointment:appointment_page")


# POSTTTT Saves yo shi in the database FRFR
def appointment_page(request):
    dentists = Dentist.objects.all()
    # ordered + only active
    services = (
        Service.objects.filter(is_active=True)
        .annotate(
            category_order=Case(
                When(category="GENERAL", then=0),
                default=1,
                output_field=IntegerField(),
            )
        )
        .order_by("category_order", "category", "service_name")
    )

    branches = Branch.objects.filter(is_active=True)

    if request.method == "POST":
        dentist_id = request.POST.get("dentist")
        branch_id = request.POST.get("location")      # <-- now this is BRANCH ID
        date_str = request.POST.get("date")
        time_str = request.POST.get("time")
        email = request.POST.get("email")

        service_ids = request.POST.getlist("services")
        if len(service_ids) > 4:
            messages.error(request, "You can select at most 4 services per appointment.")
            return redirect("appointment:appointment_page")
        
        selected_services = Service.objects.filter(id__in=service_ids)

        dentist = Dentist.objects.get(id=dentist_id)
        branch_obj = Branch.objects.get(id=branch_id)   # <-- get Branch instance

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        if date_obj < datetime.now().date():
            messages.error(request, "You cannot create an appointment in the past.")
            return redirect("appointment:appointment_page")

        preferred_time = datetime.strptime(time_str, "%H:%M").time()
        total_minutes = sum(s.duration for s in selected_services)

        # We will use branch name as the location key for your greedy util
        location_key = branch_obj.name

        with transaction.atomic():
            start_time, end_time = find_next_available_slot(
                dentist,
                date_obj,
                total_minutes,
                preferred_time,
                location=location_key,
            )

        if not start_time or not end_time:
            messages.error(
                request,
                "No available time slot for the selected date and services.",
            )
            return redirect("appointment:appointment_page")

        appointment = Appointment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            dentist=dentist,                 # <-- set FK
            branch=branch_obj,               # <-- set FK
            dentist_name=dentist.name,       # legacy text
            location=location_key,           # branch name string
            date=date_obj,
            time=start_time,
            end_time=end_time,
            preferred_date=date_obj,
            preferred_time=preferred_time,
            email=email,
        )
        appointment.services.set(selected_services)

        AppointmentLog.objects.create(
            appointment=appointment,
            action="created",
            new_status=appointment.status,
            actor=request.user if request.user.is_authenticated else None,
            note="Appointment created from appointment_page",
        )

        messages.add_message(
            request,
            messages.SUCCESS,
            "Appointment successfully created!",
            extra_tags="appointment_created",
        )
        return redirect("appointment:appointment_page")


    # Import here to avoid circular imports
    from patient.models import Patient as PatientModel
    
    # Get tooth numbers for odontogram (1-32)
    tooth_num = range(1, 33)
    
    return render(request, "appointment/appointment.html", {
        "dentists": dentists,
        "services": services,
        "tooth_num": tooth_num,
        "branches": branches,
    })


# Mainly for pre-Displaying or-prefilling Sruff, REQUEST
def events(request):
    branch = request.GET.get("branch")

    # Decide if this user can manage appointments
    user = request.user
    is_admin = user.is_authenticated and (user.is_superuser or user.is_staff)

    # Base queryset: nothing if not logged in
    if not user.is_authenticated:
        appointments = Appointment.objects.none()
    else:
        # Admin/staff see all, normal users see only their own
        if is_admin:
            appointments = Appointment.objects.all()
        else:
            appointments = Appointment.objects.filter(user=user)

    if branch:
        appointments = appointments.filter(location=branch)
        appointments = appointments.filter(branch__name=branch)

    events = []
    for a in appointments:
        color_map = {
            "not_arrived": "gray",
            "arrived": "blue",
            "ongoing": "gold",
            "done": "green",
            "cancelled": "red",
        }

        service_names = ", ".join([s.service_name for s in a.services.all()])
        service_ids = list(a.services.values_list("id", flat=True))

        # NEW: build full datetime for start
        start_dt = datetime.combine(a.date, a.time)

        # NEW: decide end_dt
        if a.end_time:
            # If end_time is stored in DB, use it
            end_dt = datetime.combine(a.date, a.end_time)
        else:
            # Fallback: compute from total service duration (in minutes)
            total_minutes = sum((s.duration or 0) for s in a.services.all())
            end_dt = start_dt + timedelta(minutes=total_minutes)

        # NEW: get the first follow-up appointment (if any)
        followup = a.followups.order_by("date", "time").first()

        events.append({
            "id": str(a.id),
            "title": f"{service_names} - {(a.dentist.name if a.dentist else a.dentist_name) or 'N/A'}",

            "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),

            "color": color_map.get(a.status, "gray"),
            "extendedProps": {
                "dentist": a.dentist.name if a.dentist else a.dentist_name,
                "dentist_id": a.dentist.id if a.dentist else None,
                "location": a.branch.name if a.branch else a.location,
                "branch_id": a.branch.id if a.branch else None,
                "date": str(a.date),
                "time": a.time.strftime("%I:%M %p"),
                "preferred_date": str(a.preferred_date) if a.preferred_date else None,
                "preferred_time": a.preferred_time.strftime("%I:%M %p") if a.preferred_time else None,
                "service": service_names,
                "service_ids": service_ids,
                "email": a.email,
                "status": a.status,
                "can_manage": is_admin,

                # NEW: follow‑up info
                "followup_id": followup.id if followup else None,
                "followup_date": str(followup.date) if followup else None,
            }
        })


    return JsonResponse(events, safe=False)

#gets the booked time 
def get_booked_times(request):
    dentist_id = request.GET.get("dentist")
    date_str = request.GET.get("date")
    branch_id = request.GET.get("location")  # this is now a BRANCH ID from the form

    if not (dentist_id and date_str and branch_id):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Invalid date"}, status=400)

    # Filter by FK ids instead of name + location string
    appointments = Appointment.objects.filter(
        dentist_id=dentist_id,
        branch_id=branch_id,
        date=date_obj,
    ).exclude(status__in=["cancelled", "done"])

    booked = [
        {
            "start": a.time.strftime("%H:%M"),
            "end": a.end_time.strftime("%H:%M") if a.end_time else None,
        }
        for a in appointments
    ]

    return JsonResponse({"booked": booked})


@csrf_exempt
@require_POST
def reschedule_appointment(request, appointment_id):
    appt = Appointment.objects.get(id=appointment_id)

    # store old values BEFORE changing appt
    old_date = appt.date
    old_time = appt.time
    old_start_dt = datetime.combine(old_date, old_time)

    dentist = Dentist.objects.get(id=request.POST.get("dentist"))
    location = request.POST.get("location")
    date_str = request.POST.get("date")
    time_str = request.POST.get("time")
    email = request.POST.get("email")
    reason = request.POST.get("reason", "").strip()

    service_ids = request.POST.getlist("services")
    selected_services = Service.objects.filter(id__in=service_ids)

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        preferred_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid date or time"}, status=400)

    if date_obj < datetime.now().date():
        return JsonResponse({"success": False, "error": "You cannot reschedule in the past."}, status=400)

    total_minutes = sum(s.duration for s in selected_services)

    with transaction.atomic():
        start_time, end_time = find_next_available_slot(
            dentist,
            date_obj,
            total_minutes,
            preferred_time,
            location=location,
        )

    if not start_time or not end_time:
        return JsonResponse({
            "success": False,
            "error": "No available time slot for the selected date and services."
        }, status=400)

    # update appointment
    appt.dentist_name = dentist.name
    appt.location = location
    appt.date = date_obj
    appt.time = start_time
    appt.end_time = end_time
    appt.preferred_date = date_obj
    appt.preferred_time = preferred_time
    appt.email = email
    appt.services.set(selected_services)
    appt.save()

    # build new datetime for "to" side
    new_start_dt = datetime.combine(date_obj, start_time)

    # Windows-safe strftime: "%b %d, %Y %I:%M %p"
    # example raw: "Feb 05, 2036 08:00 AM"
    fmt = "%b %d, %Y %I:%M %p"
    old_str = old_start_dt.strftime(fmt)
    new_str = new_start_dt.strftime(fmt)

    # remove leading zero in day: "Feb 05, ..." -> "Feb 5, ..."
    def strip_day_leading_zero(s: str) -> str:
        # month (3 chars) + space = first 4, then day starts at index 4
        # e.g. "Feb 05, 2036 ..." -> "Feb 5, 2036 ..."
        if s[4] == "0":
            s = s[:4] + s[5:]
        return s

    old_str = strip_day_leading_zero(old_str)
    new_str = strip_day_leading_zero(new_str)

    # convert "AM"/"PM" -> "a.m." / "p.m."
    old_str = old_str.replace("AM", "a.m.").replace("PM", "p.m.")
    new_str = new_str.replace("AM", "a.m.").replace("PM", "p.m.")

    note_text = f"Rescheduled from {old_str} to {new_str}."

    log_note = None
    if reason:
        log_note = (
            f"{note_text} Reason: {reason}"
        )
    else:
        log_note = note_text

    AppointmentLog.objects.create(
        appointment=appt,
        action="rescheduled",
        old_status=None,
        new_status=appt.status,
        actor=request.user if request.user.is_authenticated else None,
        note=log_note,
    )

    messages.success(request, "Appointment rescheduled successfully!")
    return JsonResponse({"success": True})



@csrf_exempt
def get_appointment_details(request, appointment_id):
    """Get appointment details including patient info for the done steps modal"""
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Prefer the FK if set, otherwise fall back to email lookup
        patient = appointment.patient
        patient_id = patient.id if patient else None

        if not patient and appointment.email:
            patient = Patient.objects.filter(email=appointment.email).first()
            if not patient:
                total = Patient.objects.filter(is_guest=True).count() + 1
                temp_id = f"P-{total:06d}-T"
                patient = Patient.objects.create(
                    name=appointment.email.split("@")[0] or "Guest Patient",
                    email=appointment.email,
                    address="TBD",
                    telephone="00000000000",
                    age=0,
                    occupation="",
                    is_guest=True,
                    guest_id=temp_id
                )
            if patient:
                patient_id = patient.id
                # Back‑fill appointment.patient so next time it's direct
                if appointment.patient_id is None:
                    appointment.patient = patient
                    appointment.save(update_fields=["patient"])
        
        # Services and prices
        service_qs = appointment.services.all()
        service_names = ", ".join([s.service_name for s in service_qs])
        service_ids = list(service_qs.values_list("id", flat=True))
        # Sum of prices for Total Amount Due
        total_price = sum((s.price or 0) for s in service_qs)

        dentist_obj = Dentist.objects.filter(name=appointment.dentist_name).first()
        
        # Check if user is admin or staff
        is_admin_or_staff = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
        
        return JsonResponse({
            "success": True,
            "appointment": {
                "id": appointment.id,
                "dentist": appointment.dentist_name,
                "dentist_id": dentist_obj.id if dentist_obj else None,
                "location": appointment.location,
                "date": str(appointment.date),
                "time": appointment.time.strftime("%H:%M"),
                "preferred_date": str(appointment.preferred_date) if appointment.preferred_date else None,
                "preferred_time": appointment.preferred_time.strftime("%I:%M %p") if appointment.preferred_time else None,
                "email": appointment.email,
                "services": service_names,
                "service_ids": service_ids,
                "total_price": float(total_price),
            },
            "patient": {
                "id": patient_id,
                "name": patient.name if patient else None,
                "email": appointment.email,
                "telephone": patient.telephone if patient else "",
                "address": patient.address if patient else "",
                "age": patient.age if patient else "",
                "occupation": patient.occupation if patient else "",
            },
            "user_role": {
                "is_admin_or_staff": is_admin_or_staff,
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@require_POST
def precompute_appointment_slot(request):
    """
    Given dentist, services, date, preferred time, location,
    return the actual start/end time that the algorithm will pick.
    """
    try:
        dentist_id = request.POST.get("dentist")
        branch_id  = request.POST.get("location")  # BRANCH ID from form
        date_str   = request.POST.get("date")
        time_str   = request.POST.get("time")      # "HH:MM" 24h, from hidden field
        service_ids = request.POST.getlist("services")

        print("DEBUG precompute POST:", request.POST.dict())

        if not (dentist_id and branch_id and date_str and time_str and service_ids):
            return JsonResponse({"success": False, "error": "Missing fields"}, status=400)

        dentist   = Dentist.objects.get(id=dentist_id)
        branch_obj = Branch.objects.get(id=branch_id)
        # Use the SAME location key as appointment_page: branch name string
        location_key = branch_obj.name

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        preferred_time = datetime.strptime(time_str, "%H:%M").time()
        selected_services = Service.objects.filter(id__in=service_ids)
        total_minutes = sum(s.duration for s in selected_services)

        print(
            "DEBUG precompute:",
            "dentist", dentist,
            "location_key", location_key,
            "total_minutes", total_minutes,
        )

        with transaction.atomic():
            start_time, end_time = find_next_available_slot(
                dentist,
                date_obj,
                total_minutes,
                preferred_time,
                location=location_key,  # <-- pass branch name, not id
            )

        print("DEBUG precompute result:", start_time, end_time)

        if not start_time or not end_time:
            return JsonResponse({
                "success": False,
                "error": "No available time slot for the selected date and services."
            }, status=400)

        return JsonResponse({
            "success": True,
            "date": date_obj.strftime("%Y-%m-%d"),
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@require_GET
@login_required
def autocomplete_patients(request):
    """
    Return up to 10 patients matching the query in ?q=...
    Search by email, name, or guest_id/id.
    """
    q = request.GET.get("q", "").strip()
    results = []

    if q:
        qs = (
            Patient.objects
            .filter(
                Q(email__icontains=q) |
                Q(name__icontains=q) |
                Q(guest_id__icontains=q) |   # if you use guest_id
                Q(id__icontains=q)          # numeric id, cast to text by DB
            )
            .order_by("name", "email")[:10]
        )

        for p in qs:
            results.append({
                "id": p.id,
                "name": p.name or "",
                "email": p.email or "",
                "guest_id": getattr(p, "guest_id", "") or "",
            })

    return JsonResponse({"results": results})