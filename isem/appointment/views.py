from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Dentist, Service, Appointment
#appoitnmetn form diffy name
from .forms import AppointmentForm

def appointment_page(request):
    dentists = Dentist.objects.all()
    services = Service.objects.all()

    if request.method == "POST":
        dentist_id = request.POST.get("dentist")
        service_id = request.POST.get("service")
        location = request.POST.get("location")
        date = request.POST.get("date")
        time = request.POST.get("time")
        reason = request.POST.get("reason")
        email = request.POST.get("email")
        id_no = request.POST.get("id_no")

        # fetch dentist and service from DB
        dentist = Dentist.objects.get(id=dentist_id) if dentist_id else None
        service = Service.objects.get(id=service_id) if service_id else None

        Appointment.objects.create(
            dentist_name=dentist.name if dentist else None,
            location=location,
            date=date,
            time=time,
            servicetype=service.service_name if service else None,
            reason=reason,
            email=email,
            id_no=id_no,
        )
        return redirect("appointment:list")

    return render(request, "appointment/appointment.html", {
        "dentists": dentists,
        "services": services
    })
        
# def appointment_events(request):
#     events = []
#     for appt in Appointment.objects.all():
#         events.append({
#             "title": f"{appt.servicetype}",
#             "start": f"{appt.date}T{appt.time}",
#             "extendedProps": {
#                 "dentist": appt.dentist_name,
#                 "location": appt.location,
#                 "date": str(appt.date),
#                 "time": str(appt.time),
#                 "service": appt.servicetype,
#                 "reason": appt.reason,
#             }
#         })
#     return JsonResponse(events, safe=False)

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
                "time": a.time.strftime("%I:%M %p"),
                "service": a.servicetype,
                "reason": a.reason,
            }
        })
    return JsonResponse(events, safe=False)

