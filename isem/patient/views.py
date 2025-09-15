from sys import path
from django.contrib import messages                 
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse

from .models import Patient, MedicalHistory


def patient_records(request):
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        telephone = request.POST.get("telephone")
        age = request.POST.get("age")
        occupation = request.POST.get("occupation")
        email = request.POST.get("email")

        is_guest = request.POST.get("is_guest") == "true"  # hidden field from JS

        if not is_guest:
            # Registered patient: check for existing email
            if email and Patient.objects.filter(email=email).exists():
                messages.error(request, "A patient with this email already exists.")
                return redirect("patient:list")
            Patient.objects.create(
                name=name,
                address=address,
                telephone=telephone,
                age=age,
                occupation=occupation,
                email=email,
                is_guest=False
            )
        else:
            # Guest patient: Unique Temporary ID generation
            total = Patient.objects.filter(is_guest=True).count() + 1
            temp_id = f"P-{total:06d}-T"
            Patient.objects.create(
                name=name,
                address=address,
                telephone=telephone,
                age=age,
                occupation=occupation,
                email=email,  # can be blank
                is_guest=True,
                guest_id=temp_id
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
        patient.email = request.POST.get("email")
        patient.address = request.POST.get("address")
        patient.telephone = request.POST.get("telephone")
        patient.age = request.POST.get("age")
        patient.occupation = request.POST.get("occupation")
        patient.save()
        return redirect("patient:list")

def medical_history(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    history = patient.medical_history.all()  # Assuming a related name
    return render(request, "patient/medical_history.html", {"patient": patient, "history": history})

def add_medical_history(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        description = request.POST.get("description")
        date = request.POST.get("date")
        # Assuming a MedicalHistory model with a foreign key to Patient
        patient.medical_history.create(description=description, date=date)
        return redirect("patient:medical_history", pk=patient_id)
    return render(request, "patient/add_medical_history.html", {"patient": patient})

def financial_history(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    # Assuming a FinancialHistory model with a foreign key to Patient
    history = patient.financial_history.all()
    return render(request, "patient/financial_history.html", {"patient": patient, "history": history})