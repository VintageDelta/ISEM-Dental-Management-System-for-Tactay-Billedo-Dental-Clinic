from django.shortcuts import render

# Create your views here.
def billing(request):
    return render(request, 'billing/billing.html')