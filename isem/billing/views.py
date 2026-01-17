from django.shortcuts import render
from .models import BillingRecord
from django.core.paginator import Paginator
# Create your views here.
def billing(request):
    bill = BillingRecord.objects.all().order_by('-date_issued')

    paginator = Paginator(bill, 5)  # Show 5 items per page
    page_number = request.GET.get('page')
    bill = paginator.get_page(page_number)
    page_obj = bill

    return render(request, 'billing/billing.html', {
                                                        'bill': page_obj.object_list,
                                                        'page_obj': page_obj,
                                                        }) 