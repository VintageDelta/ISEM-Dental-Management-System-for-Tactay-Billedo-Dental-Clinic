from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Dentist, Service, Appointment
from datetime import datetime
#appoitnmetn form diffy name
from .forms import AppointmentForm
from .utils import find_next_available_slot
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse

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
        service_id = request.POST.get("service")
        location = request.POST.get("location")
        date_str = request.POST.get("date")
        time_str = request.POST.get("time") 
        reason = request.POST.get("reason")
        email = request.POST.get("email")
        id_no = request.POST.get("id_no")

        dentist = Dentist.objects.get(id=dentist_id) if dentist_id else None
        service = Service.objects.get(id=service_id) if service_id else None
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        preferred_time = datetime.strptime(time_str, "%H:%M").time()

        # Call greedy algorithm with preferred time
        start_time, end_time = find_next_available_slot(dentist, service, date_obj, preferred_time)

        if not start_time:
            # Optional: handle "no available slot"
            return render(request, "appointment/appointment.html", {
                "dentists": dentists,
                "services": services,
                "error": "No available slots for this day."
            })
        
        # Save appointment with computed slot
        try:
            Appointment.objects.create(
                dentist_name=dentist.name if dentist else None,
                location=location,
                date=date_obj,
                time=start_time,
                end_time=end_time,
                preferred_date=date_obj,
                preferred_time=preferred_time,
                servicetype=service if service else None,
                reason=reason,
                email=email,
                id_no=id_no,
            )
            print("Appointment saved!")
        except Exception as e:
            print("Error saving appointment:", e)

        return render(request, "appointment/appointment.html", {
            "dentists": dentists,
            "services": services
        })
    
    return render(request, "appointment/appointment.html", {
        "dentists": dentists,
        "services": services
    })


# Mainly for Displaying Sruff, REQUEST
def events(request):
    appointments = Appointment.objects.all()
    events = []
    for a in appointments:
        # pick color based on status
        color_map = {
            "not_arrived": "gray",
            "arrived": "blue",
            "ongoing": "yellow",
            "done": "green",
            "cancelled": "red",
        }
        events.append({
            "id": a.id,
            "title": f"{a.servicetype.service_name} - {a.dentist_name or 'N/A'}",
            "start": f"{a.date.strftime('%Y-%m-%d')}T{a.time.strftime('%H:%M:%S')}",
            "end": f"{a.date.strftime('%Y-%m-%d')}T{a.end_time.strftime('%H:%M:%S')}" if a.end_time else None,
            "color": color_map.get(a.status, "gray"),
            "extendedProps": {
                "dentist": a.dentist_name,
                "location": a.location,
                "date": a.date.strftime("%Y-%m-%d"),
                "time": a.time.strftime("%I:%M %p"),
                "service": a.servicetype.service_name,
                "reason": a.reason,
                "status": a.status,
                "preferred_date": a.preferred_date.strftime("%Y-%m-%d") if a.preferred_date else None,
                "preferred_time": a.preferred_time.strftime("%I:%M %p") if a.preferred_time else None,
            }
        })
    return JsonResponse(events, safe=False)



