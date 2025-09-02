from django.shortcuts import render, redirect
from .models import Patient

def patient_records(request):
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        telephone = request.POST.get("telephone")
        age = request.POST.get("age")
        occupation = request.POST.get("occupation")
        status = request.POST.get("status")
        complaint = request.POST.get("complaint")

        Patient.objects.create(
            name=name,
            address=address,
            telephone=telephone,
            age=age,
            occupation=occupation,
            status=status,
            complaint=complaint
        )
        return redirect("patient:list")  # redirect after saving

    patients = Patient.objects.all()
    return render(request, "patient/patient-records.html", {"patients": patients})