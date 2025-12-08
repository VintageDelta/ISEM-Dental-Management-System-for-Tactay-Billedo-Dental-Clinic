from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Dentist, Service, Appointment
from datetime import datetime, timedelta
#appoitnmetn form diffy name
from .forms import AppointmentForm
from .utils import find_next_available_slot
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
import json

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

        # 🔒 Block any appointment date before today
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

        messages.success(request, "Appointment successfully created!")
        return redirect("appointment:appointment_page")

    return render(request, "appointment/appointment.html", {
        "dentists": dentists,
        "services": services
    })


# Mainly for pre-Displaying or-prefilling Sruff, REQUEST
def events(request):
    branch = request.GET.get("branch")

    # Base queryset: nothing if not logged in
    if not request.user.is_authenticated:
        appointments = Appointment.objects.none()
    else:
        # Admin/staff see all, normal users see only their own
        if request.user.is_superuser or request.user.is_staff:
            appointments = Appointment.objects.all()
        else:
            appointments = Appointment.objects.filter(user=request.user)

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
            "id": a.id,
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
    )

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
    date = request.POST.get("date")
    time_str = request.POST.get("time")

    service_ids = request.POST.getlist("services")

    appt.dentist_name = dentist.name
    appt.location = location
    appt.date = date
    appt.time = time_str
    appt.services.set(service_ids)
    appt.save()

    messages.success(request, "Appointment rescheduled successfully!")
    return JsonResponse({"success": True})
