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
from appointment.models import Branch
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation
from django.views.decorators.cache import never_cache


def billing(request):
    bill = BillingRecord.objects.select_related('patient', 'appointment').all().order_by('-date_issued')
    
    paginator = Paginator(bill, 5)
    page_number = request.GET.get('page')
    bill = paginator.get_page(page_number)
    page_obj = bill
    
    patients = Patient.objects.all().order_by('name')
    services = Service.objects.all().order_by('service_name')
    branches = Branch.objects.filter(is_active=True)

    return render(request, 'billing/billing.html', {
        'bill': page_obj.object_list,
        'page_obj': page_obj,
        'patients': patients,
        'services': services,
        'branches': branches,
    })


@never_cache
def billing_add(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        branch_id = request.POST.get('branch')
        amount = request.POST.get('amount')
        amount_paid = request.POST.get('amount_paid', '0')
        type_service = request.POST.get('type')
        date_issued = request.POST.get('date_issued')

        if not patient_id:
            return redirect('billing:billing_view')
        
        try:
            patient = Patient.objects.get(id=patient_id)
            amount_decimal = Decimal(amount) if amount else Decimal('0')
            amount_paid_decimal = Decimal(amount_paid) if amount_paid else Decimal('0')
            
            branch = None
            if branch_id:
                branch = Branch.objects.get(id=branch_id)

            billing = BillingRecord.objects.create(
                patient=patient,
                branch=branch,
                amount=amount_decimal,
                amount_paid=amount_paid_decimal,
                type=type_service if type_service else "N/A",
                date_issued=date_issued if date_issued else timezone.now()
            )
            
            messages.success(request, "Billing record added successfully!")
            
        except Exception as e:
            messages.error(request, f"Error creating billing record: {str(e)}")
        
        return redirect('billing:billing_view')

    return redirect('billing:billing_view')


def billing_detail(request, pk):
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
    billing = get_object_or_404(BillingRecord, pk=pk)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
        branch_id = None
        if billing.branch:
            branch_id = billing.branch.id
        elif billing.appointment and billing.appointment.branch:
            branch_id = billing.appointment.branch.id
        
        return JsonResponse({
            'id': billing.id,
            'patient_id': billing.patient.id if billing.patient else None,
            'patient_name': billing.patient_name,
            'branch_id': branch_id,
            'amount': str(billing.amount),
            'amount_paid': str(billing.amount_paid),
            'type': billing.type,
            'date_issued': billing.date_issued.strftime('%Y-%m-%d'),
            'payment_status': billing.payment_status
        })
    
    if request.method == "POST":
        patient_id = request.POST.get("patient")
        branch_id = request.POST.get("branch")
        amount_str = request.POST.get("amount", "0")
        amount_paid_str = request.POST.get("amount_paid", "0")
        service_type = request.POST.get("type")
        date_issued = request.POST.get("date_issued")
        
        if patient_id:
            patient = get_object_or_404(Patient, pk=patient_id)
            billing.patient = patient
            billing.patient_name = patient.name
        
        if branch_id:
            branch = get_object_or_404(Branch, pk=branch_id)
            billing.branch = branch
        
        try:
            billing.amount = Decimal(str(amount_str).strip()) if amount_str else Decimal('0')
            billing.amount_paid = Decimal(str(amount_paid_str).strip()) if amount_paid_str else Decimal('0')
        except (ValueError, InvalidOperation):
            billing.amount = Decimal('0')
            billing.amount_paid = Decimal('0')
        
        billing.type = service_type
        
        if date_issued:
            billing.date_issued = date_issued
        
        billing.save()
        
        messages.success(request, "Billing record updated successfully!")
        return redirect("billing:billing_view")
    
    return redirect("billing:billing_view")


def billing_delete(request, pk):
    if request.method == "POST":
        billing = get_object_or_404(BillingRecord, pk=pk)
        billing.delete()
        messages.success(request, "Billing record deleted successfully!")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


def search_billing(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_query = request.GET.get('search', '').strip()
        
        if search_query:
            billings = BillingRecord.objects.filter(
                Q(patient__name__icontains=search_query) |
                Q(patient__id__icontains=search_query) |
                Q(amount__icontains=search_query) |
                Q(type__icontains=search_query)
            ).select_related('patient', 'appointment')[:10]
            
            billings_data = []
            for billing in billings:
                billings_data.append({
                    'id': billing.id,
                    'patient_name': billing.patient.name if billing.patient else 'N/A',
                    'patient_id': billing.patient.id if billing.patient else '',
                    'amount': str(billing.amount),
                    'type': billing.type,
                    'date_issued': billing.date_issued.strftime('%b %d, %Y'),
                    'payment_status': billing.payment_status if hasattr(billing, 'payment_status') else 'unpaid'
                })
            
            return JsonResponse({'billings': billings_data})
        else:
            return JsonResponse({'billings': []})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
