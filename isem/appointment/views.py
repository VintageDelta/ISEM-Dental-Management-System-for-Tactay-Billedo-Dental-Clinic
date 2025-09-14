from django.shortcuts import render, redirect
from .forms import Appointment

# Create your views here.
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
        
    
        


# def patient_records(request):
#     if request.method == "POST":
#         name = request.POST.get("name")
#         address = request.POST.get("address")
#         telephone = request.POST.get("telephone")
#         age = request.POST.get("age")
#         occupation = request.POST.get("occupation")
#         status = request.POST.get("status")
#         complaint = request.POST.get("complaint")

#         Patient.objects.create(
#             name=name,
#             address=address,
#             telephone=telephone,
#             age=age,
#             occupation=occupation,
#             status=status,
#             complaint=complaint
#         )
#         return redirect("patient:list")  # redirect after saving

#     patients = Patient.objects.all()
#     return render(request, "patient/patient-records.html", {"patients": patients})