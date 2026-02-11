from sys import path
from django.contrib import messages                 
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Patient, MedicalHistory, FinancialHistory, Odontogram
from appointment.models import Dentist, Service

#pagination import
from django.core.paginator import Paginator
from django.shortcuts import render

from django.views.decorators.cache import never_cache

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
            messages.success(request, "Patient record created successfully.")
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
        qs = Patient.objects.all().order_by('id')

        search_query = request.GET.get('search', '')  # Get search parameter
        
        if search_query:
            # Search by name, email, telephone, or address
            qs = Patient.objects.filter(
                name__icontains=search_query
            ) | Patient.objects.filter(
                email__icontains=search_query
            ) | Patient.objects.filter(
                telephone__icontains=search_query
            ) | Patient.objects.filter(
                address__icontains=search_query
            )
            qs = qs.order_by('id')
        else:
            qs = Patient.objects.all().order_by('name')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            patients_data = list(qs[:10].values('id', 'name', 'email', 'telephone', 'address'))

            return JsonResponse({'patients': patients_data})
        paginator = Paginator(qs, 5)  # 5 records per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(
            request,
            "patient/patient-records.html",
            {
                "patients": page_obj.object_list,  
                "page_obj": page_obj,            
                "search_query": search_query,
            },
        )
    else:
        patient = get_object_or_404(Patient, email=request.user.email)
    return medical_history(request, pk=patient.id)

def delete_patient(request, pk):
    if request.method == "POST":
        patient = get_object_or_404(Patient, pk=pk)
        patient.delete()
        messages.success(request, "Patient record deleted successfully.")
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

        # Sync telephone to Profile if user exists
        if patient.user:
            try:
                profile = patient.user.profile
                profile.mobile = patient.telephone
                profile.save()
                print(f" Synced Patient → Profile: {patient.telephone}")
            except Exception as e:
                print(f" Profile sync failed: {e}")

        messages.success(request, "Patient information updated successfully.")
        return redirect("patient:list")

def medical_history(request, pk):
    patient = get_object_or_404(Patient, pk=pk)


    if request.method == "POST" and 'update_patient_info' in request.POST:
        age = request.POST.get("age")
        if age:
            try:
                patient.age = int(age)
            except ValueError:
                    pass
            
        patient.gender = request.POST.get("gender") or patient.gender
        patient.occupation = request.POST.get("occupation") or patient.occupation
        patient.telephone = request.POST.get("telephone") or patient.telephone
        patient.address = request.POST.get("address") or patient.address
        patient.email = request.POST.get("email") or patient.email
        
        patient.particular_condition = request.POST.get("particular_condition") or patient.particular_condition
        patient.allergy = request.POST.get("allergy") or patient.allergy
        patient.pregnancy_status = request.POST.get("pregnancy_status") or patient.pregnancy_status
        patient.medications = request.POST.get("medications") or patient.medications
        patient.abnormal_bleeding_history = request.POST.get("abnormal_bleeding_history") or patient.abnormal_bleeding_history
        
        patient.save()

         #Sync telephone to Profile if user exists
        if patient.user:
            try:
                from userprofile.models import Profile
                profile, created = Profile.objects.get_or_create(user=patient.user)
                profile.mobile = patient.telephone
                profile.save()
                print(f"     Synced Patient → Profile: {patient.telephone}")
            except Exception as e:
                print(f" Profile sync failed: {e}")

        xray_files = request.FILES.getlist('xray_images')
        if xray_files:
            from .models import Xray
            for xray_file in xray_files:
                Xray.objects.create(
                    patient=patient,
                    file=xray_file,
                    description=request.POST.get("xray_description", "")
                )
                messages.success(request, f"Patient information and {len(xray_files)} X-ray images updated successfully.")
            else:
                messages.success(request, "Patient information updated successfully.")
        return redirect("patient:medical_history", pk=pk)


    medical_history_qs = patient.medical_history.all()
    financial_history_qs = patient.financial_history.all()

    from appointment.models import Appointment
    appointments = Appointment.objects.filter(
        email=patient.email,
        status__in=['done', 'completed']
    ).order_by('-date')
    
    # Combine treatment history
    treatment_history = []
    
    for record in medical_history_qs:
        treatment_history.append({
            'source': 'manual',
            'id': record.id,
            'date': record.date,
            'dentist': record.dentist,
            'services': record.services,
            'amount': record.amount,
            'findings': record.findings,
            'prescriptions': record.prescriptions,
        })
    
    for appt in appointments:
        services_text = ", ".join([s.service_name for s in appt.services.all()])
        total_amount = sum((s.price or 0) for s in appt.services.all())
        
        # Convert datetime to date if needed
        appt_date = appt.date.date() if hasattr(appt.date, 'date') else appt.date
        
        treatment_history.append({
            'source': 'appointment',
            'id': appt.id,
            'date': appt_date,  # ← Ensure it's a date object
            'dentist': appt.dentist.name if appt.dentist else appt.dentist_name,
            'services': services_text,
            'amount': total_amount,
            'findings': '',
            'prescriptions': '',
        })
    
    treatment_history.sort(key=lambda x: x['date'], reverse=True)
        # ===== FETCH BILLING HISTORY =====
    financial_history_qs = patient.financial_history.all()
    
    from billing.models import BillingRecord
    billing_records = BillingRecord.objects.filter(patient=patient).order_by('-date_issued')
    
    # Combine billing history
    billing_history = []
    
    # Add manual financial history
    for record in financial_history_qs:
        billing_history.append({
            'source': 'manual',
            'id': record.id,
            'date': record.date,  # This is already a date object
            'bill_type': record.bill_type,
            'payment_mode': record.payment_mode,
            'amount': record.amount,
            'total_bill': record.total_bill,
            'balance': record.balance,
        })
    
    # Add billing records from appointments
    for bill in billing_records:
        # Convert datetime to date for consistent sorting
        bill_date = bill.date_issued.date() if hasattr(bill.date_issued, 'date') else bill.date_issued
        
        billing_history.append({
            'source': 'appointment',
            'id': bill.id,
            'date': bill_date,  
            'bill_type': 'Services',
            'payment_mode': 'N/A',
            'amount': bill.amount_paid,     
            'total_bill': bill.amount,       
            'balance': bill.balance, 
        })
    
    billing_history.sort(key=lambda x: x['date'], reverse=True)

    tooth_num = range(1, 33)

    return render(request, "patient/medical_history.html", {
        "patient": patient,
        "treatment_history": treatment_history,
        "billing_history": billing_history,
        "tooth_num": tooth_num,
        "services": Service.objects.all(),
        "dentists": Dentist.objects.all()
    })
@never_cache
def add_medical_history(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == "POST":
        # Get form data first
        date = request.POST.get("date")
        dentist = request.POST.get("dentist")
        service_ids = request.POST.getlist("services")
        amount = request.POST.get("amount")
        findings = request.POST.get("findings")
        prescriptions = request.POST.get("prescriptions")
        
        # DEBUG prints (keep these!)
        print("=" * 50)
        print("POST DATA:", request.POST)
        print("Service IDs:", service_ids)
        
        # Get service names from IDs
        from appointment.models import Service
        
        # DEBUG: Check what services exist
        all_services = Service.objects.all()
        print(f"Total services in database: {all_services.count()}")
        for s in all_services:
            print(f"  - ID: {s.id}, Name: {s.service_name}")
        
        selected_services = Service.objects.filter(id__in=service_ids)
        
        # DEBUG: Print what services were found
        print(f"Selected Services Objects: {selected_services}")
        print(f"Found {selected_services.count()} services")
        for s in selected_services:
            print(f"  - ID: {s.id}, Name: {s.service_name}")
        
        services_text = ", ".join([s.service_name for s in selected_services])
        
        print("Final Services Text to Save:", services_text)
        print("=" * 50)
        
        # Convert empty amount to 0
        amount = amount if amount and amount.strip() else "0"

        # Create medical history record
        med_record = MedicalHistory.objects.create(
            patient=patient,
            date=date,
            dentist=dentist,
            services=services_text,
            amount=amount,
            findings=findings,
            prescriptions=prescriptions or "",
        )
        
        # # QUICK FIX: Auto-create billing record (assumes paid in full)
        # FinancialHistory.objects.create(
        #     patient=patient,
        #     date=date,
        #     bill_type="Services",
        #     payment_mode="Cash",  # Default
        #     amount=amount,         # Paid amount = treatment total
        #     total_bill=amount,     # Total bill = treatment amount
        #     balance=0              # Fully paid
        # )
        # print(" AUTO-CREATED BILLING FROM TREATMENT")
        
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": True, "message": "Treatment + Billing added successfully"}
            )

        messages.success(request, "Treatment and billing added successfully")
        return redirect("patient:medical_history", pk=patient_id)

    return redirect("patient:medical_history", pk=patient_id)

# def financial_history(request, patient_id):
#     patient = get_object_or_404(Patient, pk=patient_id)
    
#     history = patient.financial_history.all()
#     tooth_num = range(1, 33)
#     return render(request, "patient/medical_history.html", {"patient": patient, "history": history, "tooth_num": tooth_num})
@never_cache
def add_financial_history(request, patient_id):
    # Debugging logs (keep these!)
    print("=" * 50)
    print("ADD_FINANCIAL_HISTORY VIEW CALLED")
    print(f"Patient ID: {patient_id}")
    print(f"Method: {request.method}")
    print(f"POST data: {request.POST}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    print("=" * 50)

    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == "POST":
        # Get form data
        date = request.POST.get("date")
        bill_type = request.POST.get("bill_type")
        payment_mode = request.POST.get("payment_mode")
        amount = request.POST.get("amount")
        total_bill = request.POST.get("total_bill")
        balance = request.POST.get("balance")
        
        # Convert empty strings to 0 for decimal fields
        amount = amount if amount and amount.strip() else "0"
        total_bill = total_bill if total_bill and total_bill.strip() else "0"
        balance = balance if balance and balance.strip() else "0"

        print(f"Creating FinancialHistory with: date={date}, bill_type={bill_type}, payment_mode={payment_mode}, amount={amount}, total_bill={total_bill}, balance={balance}")

        # Create billing record
        bill_record = FinancialHistory.objects.create(
            patient=patient,
            date=date,
            bill_type=bill_type,
            payment_mode=payment_mode,
            amount=amount,
            total_bill=total_bill,
            balance=balance,
        )
        
        # # Auto-create treatment only for non-AJAX/manual billing, not for Done Steps wizard
        # is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # if bill_type == "Services" and not is_ajax:
        #     MedicalHistory.objects.create(
        #         patient=patient,
        #         date=date,
        #         dentist="",  # TODO: expose dentist in manual billing form
        #         services=bill_type,
        #         amount=total_bill,
        #         findings="",
        #         prescriptions=""
        #     )
        #     print(" AUTO-CREATED TREATMENT FROM BILLING (manual)")

        
        # print("FinancialHistory created successfully")
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print("RETURNING JSON SUCCESS")
            return JsonResponse({"success": True, "message": "Billing + Treatment added successfully"})
        
        messages.success(request, "Billing and treatment added successfully")
        return redirect("patient:medical_history", pk=patient_id)
    
    return redirect("patient:medical_history", pk=patient_id)


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

    services = Service.objects.all()
    dentists = Dentist.objects.all()

    return render(request, "patient/medical_history.html", {"patient": patient, "tooth_num": tooth_num, "tooth_name": tooth_names, "services": services, "dentists": dentists})
@never_cache
def add_odontogram(request, patient_id):
    
    #idk why but shits not posting on my part!
    print("=" * 50)
    print("ADD_ODONTOGRAM VIEW CALLED")
    print(f"Patient ID: {patient_id}")
    print(f"Method: {request.method}")
    print(f"POST data: {request.POST}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    print("=" * 50)

    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        index = 0
        created_any= False

        while True:
            date_key = f"date_{index}"
            if date_key not in request.POST:

                break

            date_val = request.POST.get(date_key)
            status_val = request.POST.get(f"status_{index}")  
            dentist_id = request.POST.get(f"dentist_{index}")
            tooth_numbers = request.POST.getlist(f"tooth_number_{index}")
            services_ids = request.POST.getlist(f"services_{index}")

            if not date_val or not status_val or not dentist_id or not tooth_numbers:
                index += 1
                continue

            dentist = dentist_id

            print(f"ROW {index} TEETH:", tooth_numbers)

            for tooth_number in tooth_numbers:
                odontogram = Odontogram.objects.create(
                    patient=patient,
                    tooth_number=int(tooth_number),
                    date=date_val,
                    dentist=dentist,
                    status=status_val,
                )

                if services_ids:
                    odontogram.service.add(*services_ids)
                
                messages.success(request,f"Tooth {tooth_number} added successfully with services.")
                created_any = True
            index += 1
        if not created_any:
            messages.error(request, "No valid odontogram entries were provided.")
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if created_any:
                return JsonResponse({"success": True, "message": "Odontogram saved successfully"})
            else:
                return JsonResponse({"success": False, "error": "No valid odontogram entries were provided."}, status=400)
        return redirect("patient:odontogram", patient_id=patient_id)
    return render(request, "patient/medical_history.html", {"patient": patient})


def odontogram_history(request, patient_id, tooth_number):
    patient = get_object_or_404(Patient, pk=patient_id)
    records = Odontogram.objects.filter(patient=patient, tooth_number=tooth_number)
    data = []
    for record in records:
        data.append({
            "tooth_name": TOOTH_NAMES.get(record.tooth_number, "Unknown Tooth"),
            "date": record.date.strftime("%Y-%m-%d"),
            "services": [service.service_name for service in record.service.all()],
            "dentist": record.dentist,
            "status": record.status,
        })
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

def delete_xray(request, xray_id):
    """Delete an X-ray image"""
    if request.method == "POST":
        try:
            from .models import Xray
            xray = Xray.objects.get(id=xray_id)
            patient_id = xray.patient.id
            
            # Delete the file from disk
            if xray.file:
                xray.file.delete()
            
            # Delete the database record
            xray.delete()
            
            messages.success(request, "X-ray deleted successfully.")
            return redirect('patient:medical_history', pk=patient_id)
        except Xray.DoesNotExist:
            messages.error(request, "X-ray not found.")
            return redirect('patient:list')
    
    return redirect('patient:list')



