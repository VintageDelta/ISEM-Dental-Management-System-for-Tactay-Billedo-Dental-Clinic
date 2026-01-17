from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Dentist, Service, Appointment
from datetime import datetime, timedelta
#appoitnmetn form diffy name
from .forms import AppointmentForm
from django.shortcuts import render, redirect, get_object_or_404
from .utils import find_next_available_slot
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
from patient.models import Patient
from django.db import transaction

@csrf_exempt
@require_POST
def update_status(request, appointment_id):
    try:
        data = json.loads(request.body)
        status = data.get("status")
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = status
        appointment.save()
        return JsonResponse({"success": True, "status": status})
    except Exception as e:
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
    )
    followup.services.set(selected_services)


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
    services = Service.objects.all()

    if request.method == "POST":
        dentist_id = request.POST.get("dentist")
        location = request.POST.get("location")
        date_str = request.POST.get("date")
        time_str = request.POST.get("time")
        email = request.POST.get("email")

        service_ids = request.POST.getlist("services")
        selected_services = Service.objects.filter(id__in=service_ids)

        dentist = Dentist.objects.get(id=dentist_id)

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        #Block any appointment date before today
        if date_obj < datetime.now().date():
            messages.error(request, "You cannot create an appointment in the past.")
            return redirect("appointment:appointment_page")

        preferred_time = datetime.strptime(time_str, "%H:%M").time()

        total_minutes = sum(s.duration for s in selected_services)

        start_time, end_time = find_next_available_slot(
            dentist,
            date_obj,
            total_minutes,
            preferred_time,
            location=location
        )
        
        if not start_time or not end_time:
            messages.error(
                request,
                "No available time slot for the selected date and services."
            )
            return redirect("appointment:appointment_page")

        # Create or find patient by email
        patient = None
        if email:
            patient = Patient.objects.filter(email=email).first()
            if not patient:
                # Create a guest patient for appointment
                total = Patient.objects.filter(is_guest=True).count() + 1
                temp_id = f"P-{total:06d}-T"
                patient = Patient.objects.create(
                    name=email.split("@")[0] or "Guest Patient",  # Use email prefix as default name
                    email=email,
                    address="TBD",  # Will be filled later in the done steps modal
                    telephone="00000000000",  # Default phone number (required field)
                    age=0,  # Will be filled later
                    occupation="",
                    is_guest=True,
                    guest_id=temp_id
                )

        with transaction.atomic():
            start_time, end_time = find_next_available_slot(
            dentist,
            date_obj,
            total_minutes,
            preferred_time,
            location=location
        )

        if not start_time or not end_time:
            messages.error(
                request,
                "No available time slot for the selected date and services."
            )
            return redirect("appointment:appointment_page")

        appointment = Appointment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            dentist_name=dentist.name,
            location=location,
            date=date_obj,
            time=start_time,
            end_time=end_time,
            preferred_date=date_obj,
            preferred_time=preferred_time,
            email=email,
        )
        appointment.services.set(selected_services)

        
        # Store patient_id in appointment (if you want to add a FK later)
        # For now, we'll use email to find patient when needed

        messages.add_message(
            request,
            messages.SUCCESS,
            "Appointment successfully created!",
            extra_tags="appointment_created"
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
        dentist_obj = Dentist.objects.filter(name=a.dentist_name).first()

        events.append({
            "id": str(a.id),
            "title": f"{service_names} - {a.dentist_name or 'N/A'}",
            "start": f"{a.date}T{a.time}",
            "end": f"{a.date}T{a.end_time}" if a.end_time else None,
            "color": color_map.get(a.status, "gray"),
            "extendedProps": {
                "dentist": a.dentist_name,
                "dentist_id": dentist_obj.id if dentist_obj else None,
                "location": a.location,
                "date": str(a.date),
                "time": a.time.strftime("%I:%M %p"),
                "preferred_date": str(a.preferred_date) if a.preferred_date else None,
                "preferred_time": a.preferred_time.strftime("%I:%M %p") if a.preferred_time else None,
                "service": service_names,
                "service_ids": service_ids,
                "email": a.email,
                "status": a.status,
                "can_manage": is_admin,
            }
        })

    return JsonResponse(events, safe=False)

#gets the booked time 
def get_booked_times(request):
    dentist_id = request.GET.get("dentist")
    date_str = request.GET.get("date")
    location = request.GET.get("location")

    if not (dentist_id and date_str and location):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return JsonResponse({"error": "Invalid date"}, status=400)

    # Filter appointments by dentist, date, and LOCATION (important)
    appointments = Appointment.objects.filter(
        dentist_name=Dentist.objects.get(id=dentist_id).name,
        date=date_obj,
        location=location  # ← This makes branches separate!
    ).exclude(status="cancelled")

    # Return start/end times so the front-end can block these
    booked = []
    for a in appointments:
        booked.append({
            "start": a.time.strftime("%H:%M"),
            "end": a.end_time.strftime("%H:%M") if a.end_time else None
        })

    return JsonResponse({"booked": booked})


@csrf_exempt
@require_POST
def reschedule_appointment(request, appointment_id):
    appt = Appointment.objects.get(id=appointment_id)

    dentist = Dentist.objects.get(id=request.POST.get("dentist"))
    location = request.POST.get("location")
    date_str = request.POST.get("date")
    time_str = request.POST.get("time")
    email = request.POST.get("email")

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


    messages.success(request, "Appointment rescheduled successfully!")
    return JsonResponse({"success": True})


@csrf_exempt
def get_appointment_details(request, appointment_id):
    """Get appointment details including patient info for the done steps modal"""
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Find or create patient by email
        patient = None
        patient_id = None
        if appointment.email:
            patient = Patient.objects.filter(email=appointment.email).first()
            if not patient:
                # Create patient if doesn't exist (for older appointments)
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
        
        service_names = ", ".join([s.service_name for s in appointment.services.all()])
        service_ids = list(appointment.services.values_list("id", flat=True))
        
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



