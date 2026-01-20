from django.shortcuts import get_object_or_404, render
from .models import BillingRecord
from django.core.paginator import Paginator
# Create your views here.
def billing(request):
    bill = BillingRecord.objects.select_related('patient', 'appointment').all().order_by('-date_issued')

    paginator = Paginator(bill, 5)  # Show 5 items per page
    page_number = request.GET.get('page')
    bill = paginator.get_page(page_number)
    page_obj = bill

    return render(request, 'billing/billing.html', {
                                                        'bill': page_obj.object_list,
                                                        'page_obj': page_obj,
                                                        }) 


def billing_detail(request, pk):
    """View a single billing record details"""
    billing = get_object_or_404(BillingRecord, pk=pk)
    
    return render(request, 'billing/billing_detail.html', {
        'billing': billing,
        'patient': billing.patient,
        'appointment': billing.appointment,
    })

def billing_edit(request, pk):
    """Edit a billing record"""
    billing = get_object_or_404(BillingRecord, pk=pk)
    
    if request.method == 'POST':
        billing.patient_name = request.POST.get('patient_name', billing.patient_name)
        billing.type = request.POST.get('type', billing.type)
        billing.amount = request.POST.get('amount', billing.amount)
        billing.payment_status = request.POST.get('payment_status', billing.payment_status)
        billing.save()
        
        return render(request, 'billing/billing_detail.html', {
            'billing': billing,
            'patient': billing.patient,
            'appointment': billing.appointment,
            'message': 'Billing record updated successfully.'
        })
    
    return render(request, 'billing/billing_edit.html', {
        'billing': billing,
    })

def billing_delete(request, pk):
    """Delete a billing record"""
    billing = get_object_or_404(BillingRecord, pk=pk)
    
    if request.method == 'POST':
        billing.delete()
        return render(request, 'billing/billing_deleted.html', {
            'message': 'Billing record deleted successfully.'
        })
    
    return render(request, 'billing/billing_confirm_delete.html', {
        'billing': billing,
    })