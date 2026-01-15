from datetime import date, timedelta
from django.shortcuts import render
from appointment.models import Appointment
from inventory.models import InventoryItem
from patient.models import Patient

# Create your views here.
def dashboard(request):
    today = date.today()

    todays_appointments = Appointment.objects.all()
    upcoming_appointments = Appointment.objects.filter(
        date__gt=today,
        date__lte=today + timedelta(days=7)
    )

    new_patients_today = Patient.objects.filter(created_at__date=today)

    cancelled = Appointment.objects.filter(
        # date=today,
        status__in=['cancelled']
    )

    low_stock_items = InventoryItem.objects.filter(
    status__in=['low_stock', 'out_of_stock']
    )

    context = {
        'todays_count': todays_appointments.count(),
        'upcoming_count': upcoming_appointments.count(),
        'new_patients_count': new_patients_today.count(),
        'cancelled_count': cancelled.count(),
        'todays_appointments': todays_appointments,
        'low_stock_items': low_stock_items,
    }
    
    return render(request, 'dashboard/dashboard.html', context)