from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Appointment
from .forms import Appointment

# POST!! iykyk
def appointment_record(request):
    if request.method == "POST":
        dentist_name = request.POST.get("dentist_name")
        location = request.POST.get("location")
        date = request.POST.get("date")
        time = request.POST.get("time")
        servicetype = request.POST.get("servicetype")
        reason = request.POST.get("reason")
        email = request.POST.get("email")
        id_no = request.POST.get("id_no")

        Appointment.objects.create(
            dentist_name = dentist_name,
            location = location,
            date = date,
            time = time,
            servicetype = servicetype,
            reason = reason,
            email = email,
            id_no = id_no,
        )
        return redirect("appointment:list")
    
    appointment = Appointment.objects.all()
    return render(request, "appointment/appointment.html", {"appointments": appointment})
        
def appointment_events(request):
    events = []
    appointments = Appointment.objects.all()
    

    for appt in appointments:
        events.append({
            "title": f"{appt.servicetype} - {appt.reason}",
            "start": f"{appt.date}T{appt.time}",
        })

    return JsonResponse(events, safe=False)

        

