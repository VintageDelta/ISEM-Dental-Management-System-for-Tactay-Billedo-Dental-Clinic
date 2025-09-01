from django.shortcuts import render

# Create your views here.
def appointment(request):
    return render(request, 'appointment/appointment.html')