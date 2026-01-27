from datetime import datetime
from django.utils import timezone
from urllib import request
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Q

from patient.models import Patient
from appointment.models import Appointment, Service
from .models import BillingRecord
from .forms import BillingRecordForm
from django.core.paginator import Paginator
# Create your views here.
def billing(request):
    bill = BillingRecord.objects.select_related('patient', 'appointment').all().order_by('-date_issued')

    print("=" * 50)
    print(f"Total billing records: {bill.count()}")
    for b in bill[:5]:  # Print first 5
        print(f"ID: {b.pk}, Patient: {b.patient.name if b.patient else 'None'}, Amount: {b.amount}, Appointment: {b.appointment.id if b.appointment else 'None'}")
    print("=" * 50)

    paginator = Paginator(bill, 5)  # Show 5 items per page
    page_number = request.GET.get('page')
    bill = paginator.get_page(page_number)
    page_obj = bill
    
    patients = Patient.objects.all().order_by('name')
    services = Service.objects.all().order_by('service_name') 

    return render(request, 'billing/billing.html', {
                                                        'bill': page_obj.object_list,
                                                        'page_obj': page_obj,
                                                        'patients': patients,
                                                        'services': services,
                                                        }) 

def billing_add(request):
    if request.method == 'POST':
        
        # Get form data
        patient_id = request.POST.get('patient')
        amount = request.POST.get('amount')
        type_service = request.POST.get('type')
        date_issued = request.POST.get('date_issued')
        
        print("=" * 50)
        print("BILLING_ADD CALLED")
        print(f"Patient ID: {patient_id}")
        print(f"Amount: {amount}")
        print(f"Type: {type_service}")
        print(f"Date: {date_issued}")
        print("=" * 50)

        if not patient_id:
            
            return redirect('billing:billing_view')
        
        try:
            patient = Patient.objects.get(id=patient_id)
            print(f"✓ Found patient: {patient.name}")

            billing = BillingRecord.objects.create(
                patient=patient,
                amount=amount if amount else 0,
                type=type_service if type_service else "N/A",
                payment_status='unpaid',
                date_issued=date_issued if date_issued else timezone.now()
            )
            
            print(f"✓ Billing record created: ID {billing.pk}")
            print(f"  Patient: {billing.patient.name}")
            print(f"  Amount: {billing.amount}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return redirect('billing:billing_view')

    return redirect('billing:billing_view')


def billing_detail(request, pk):
    """View a single billing record details"""
    billing = get_object_or_404(BillingRecord, pk=pk)
    
    return JsonResponse({
        "id": billing.id,
        "patient_id": billing.patient.id if billing.patient else None,
        "patient_name": billing.patient.name if billing.patient else "",
        "appointment_id": billing.appointment.id if billing.appointment else None,
        "type": billing.type,
        "amount": str(billing.amount),
        "payment_status": billing.payment_status,
        "date_issued": billing.date_issued.strftime("%Y-%m-%d") if billing.date_issued else "",
    })


def billing_edit(request, pk):
    """Edit a billing record"""
    billing = get_object_or_404(BillingRecord, pk=pk)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            "id": billing.id,
            "patient_id": billing.patient.id if billing.patient else None,
            "patient_name": billing.patient.name if billing.patient else "",
            "appointment_id": billing.appointment.id if billing.appointment else None,
            "type": billing.type,
            "amount": str(billing.amount),
            "payment_status": billing.payment_status,
            "date_issued": billing.date_issued.strftime("%Y-%m-%d") if billing.date_issued else "",
        })
    if request.method == "POST":
        billing.type = request.POST.get("type")
        billing.payment_status = request.POST.get("payment_status", "unpaid")
        
        amount = request.POST.get("amount")
        if amount:
            billing.amount = float(amount)
        
        date_issued = request.POST.get("date_issued")
        if date_issued:
            billing.date_issued = datetime.strptime(date_issued, "%Y-%m-%d").date()
        
        billing.save()
        messages.success(request, "Billing record updated successfully.")
        return redirect("billing:billing_view")

    return redirect("billing:billing_view")

def billing_delete(request, pk):
    """Delete a billing record"""
    if request.method == "POST":
        billing = get_object_or_404(BillingRecord, pk=pk)
        billing.delete()
        messages.success(request, "Billing record deleted successfully!")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)

def search_billing(request):
    """AJAX endpoint for live billing search"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_query = request.GET.get('search', '').strip()
        
        if search_query:
            # Search by patient name, patient ID, amount, or type
            billings = BillingRecord.objects.filter(
                Q(patient__name__icontains=search_query) |
                Q(patient__id__icontains=search_query) |
                Q(amount__icontains=search_query) |
                Q(type__icontains=search_query)
            ).select_related('patient')[:10]  # Limit to 10 results
            
            billings_data = []
            for billing in billings:
                billings_data.append({
                    'id': billing.id,
                    'patient_name': billing.patient.name,
                    'patient_id': billing.patient.id,
                    'amount': str(billing.amount),
                    'type': billing.type,
                    'date_issued': billing.date_issued.strftime('%b %d, %Y'),
                    'payment_status': billing.payment_status if hasattr(billing, 'payment_status') else 'unpaid'
                })
            
            return JsonResponse({'billings': billings_data})
        else:
            return JsonResponse({'billings': []})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
