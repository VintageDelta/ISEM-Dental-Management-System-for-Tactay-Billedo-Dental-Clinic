from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
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

def delete_patient(request, pk):
    if request.method == "POST":
        patient = get_object_or_404(Patient, pk=pk)
        patient.delete()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)

def update_patient(request):
    if request.method == "POST":
        pk = request.POST.get("id")
        patient = get_object_or_404(Patient, pk=pk)
        patient.name = request.POST.get("name")
        patient.address = request.POST.get("address")
        patient.telephone = request.POST.get("telephone")
        patient.age = request.POST.get("age")
        patient.occupation = request.POST.get("occupation")
        patient.status = request.POST.get("status")
        patient.complaint = request.POST.get("complaint")
        patient.save()
        return redirect("patient:list")