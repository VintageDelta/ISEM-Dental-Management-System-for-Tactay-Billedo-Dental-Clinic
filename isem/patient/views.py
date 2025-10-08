from sys import path
from django.contrib import messages                 
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Patient, MedicalHistory, FinancialHistory, Odontogram
def patient_records(request):
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        telephone = request.POST.get("telephone")
        age = request.POST.get("age")
        occupation = request.POST.get("occupation")
        email = request.POST.get("email")

        is_guest = request.POST.get("is_guest") == "true"  
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
            # Guest patient: temporary ID
            total = Patient.objects.filter(is_guest=True).count() + 1
            temp_id = f"P-{total:06d}-T"
            Patient.objects.create(
                name=name,
                address=address,
                telephone=telephone,
                age=age,
                occupation=occupation,
                email=email,  
                is_guest=True,
                guest_id=temp_id
            )

        return redirect("patient:list")
    if request.user.is_staff or request.user.is_superuser:
         patients = Patient.objects.all()
         return render(request, "patient/patient-records.html", {"patients": patients})
    else:
        patient = get_object_or_404(Patient, email=request.user.email)
    return render(request, "patient/medical_history.html", {"patient": patient})


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
    history = patient.medical_history.all() 
    tooth_num = range(1, 33)
    return render(request, "patient/medical_history.html", {"patient": patient, "history": history, "tooth_num": tooth_num  })

def add_medical_history(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        MedicalHistory.objects.create(
            patient=patient,
            date=request.POST.get("date"),
            dentist=request.POST.get("dentist"),
            reason=request.POST.get("reason"),
            diagnosis=request.POST.get("diagnosis"),
            service=request.POST.get("service"),
            treatment=request.POST.get("treatment"),
            prescriptions=request.POST.get("prescriptions"),
        )
        return redirect("patient:medical_history", pk=patient_id)
    return render(request, "patient/medical_history.html", {"patient": patient})

def financial_history(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    history = patient.financial_history.all()
    tooth_num = range(1, 33)
    return render(request, "patient/medical_history.html", {"patient": patient, "history": history, "tooth_num": tooth_num})

def add_financial_history(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        FinancialHistory.objects.create(
            patient=patient,
            date=request.POST.get("date"),
            description=request.POST.get("description"),
            time=request.POST.get("time"),
            type=request.POST.get("type"),
            amount=request.POST.get("amount"),
            balance=request.POST.get("balance"),
        )
        return redirect("patient:financial_history", patient_id=patient_id)
    return render(request, "patient/medical_history.html", {"patient": patient})
TOOTH_NAMES = {
  1: "Upper Right Third Molar (Wisdom Tooth)",
  2: "Upper Right Second Molar",
  3: "Upper Right First Molar",
  4: "Upper Right Second Premolar",
  5: "Upper Right First Premolar",
  6: "Upper Right Canine (Cuspid)",
  7: "Upper Right Lateral Incisor",
  8: "Upper Right Central Incisor",
  9: "Upper Left Central Incisor",
  10: "Upper Left Lateral Incisor",
  11: "Upper Left Canine (Cuspid)",
  12: "Upper Left First Premolar",
  13: "Upper Left Second Premolar",
  14: "Upper Left First Molar",
  15: "Upper Left Second Molar",
  16: "Upper Left Third Molar (Wisdom Tooth)",

  17: "Lower Left Third Molar (Wisdom Tooth)",
  18: "Lower Left Second Molar",
  19: "Lower Left First Molar",
  20: "Lower Left Second Premolar",
  21: "Lower Left First Premolar",
  22: "Lower Left Canine (Cuspid)",
  23: "Lower Left Lateral Incisor",
  24: "Lower Left Central Incisor",
  25: "Lower Right Central Incisor",
  26: "Lower Right Lateral Incisor",
  27: "Lower Right Canine (Cuspid)",
  28: "Lower Right First Premolar",
  29: "Lower Right Second Premolar",
  30: "Lower Right First Molar",
  31: "Lower Right Second Molar",
  32: "Lower Right Third Molar (Wisdom Tooth)"
}
def odontogram(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    tooth_num = range(1, 33)
    tooth_names = TOOTH_NAMES

    return render(request, "patient/medical_history.html", {"patient": patient, "tooth_num": tooth_num, "tooth_name": tooth_names})

def add_odontogram(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        Odontogram.objects.create(
            patient=patient,
            tooth_number=request.POST.get("tooth_number"),
            condition=request.POST.get("condition"),
        )
        return redirect("patient:odontogram", patient_id=patient_id)
    return render(request, "patient/medical_history.html", {"patient": patient})

def odontogram_history(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    odontogram = Odontogram.objects.filter(patient=patient, tooth_number=request.POST.get("tooth_number")).first()
    if odontogram: {
        "date": odontogram.date,
        "condition": odontogram.condition,
        "treatment": odontogram.treatment,
        "dentist": odontogram.dentist,
        "status": odontogram.status,
        "notes": odontogram.notes,
    }
    else:
        data = None
    return JsonResponse({"data": data})

def update_odontogram(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        tooth_number = request.POST.get("tooth_number")
        date = request.POST.get("date")
        condition = request.POST.get("condition")
        treatment = request.POST.get("treatment")
        dentist = request.POST.get("dentist")
        status = request.POST.get("status")
        notes = request.POST.get("notes")

        odontogram, _ = Odontogram.objects.get_or_create(
            patient=patient,
            tooth_number=tooth_number,
            defaults={
                "date": date,
                "condition": condition,
                "treatment": treatment,
                "dentist": dentist,
                "status": status,
                "notes": notes,
            }
        )

        return JsonResponse({
            "success" : True,
            "data": {
                "tooth_name": tooth_number,
                "date": odontogram.date,
                "condition": odontogram.condition,
                "treatment": odontogram.treatment,
                "dentist": odontogram.dentist,
                "status": odontogram.status,
                "notes": odontogram.notes,
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)