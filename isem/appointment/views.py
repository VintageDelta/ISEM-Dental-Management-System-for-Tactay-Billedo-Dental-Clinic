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
    for appt in Appointment.objects.all():
        events.append({
            "title": f"{appt.servicetype}",
            "start": f"{appt.date}T{appt.time}",
            "extendedProps": {
                "dentist": appt.dentist_name,
                "location": appt.location,
                "date": str(appt.date),
                "time": str(appt.time),
                "service": appt.servicetype,
                "reason": appt.reason,
            }
        })
    return JsonResponse(events, safe=False)

def events(request):
    appointments = Appointment.objects.all()
    events = []
    for a in appointments:
        events.append({
            "id": a.id,
            "title": f"{a.servicetype} - {a.dentist_name or 'N/A'}",
            "start": f"{a.date}T{a.time}",
            "extendedProps": {
                "dentist": a.dentist_name,
                "location": a.location,
                "date": a.date.strftime("%Y-%m-%d"),
                "time": a.time.strftime("%H:%M"),
                "service": a.servicetype,
                "reason": a.reason,
            }
        })
    return JsonResponse(events, safe=False)

