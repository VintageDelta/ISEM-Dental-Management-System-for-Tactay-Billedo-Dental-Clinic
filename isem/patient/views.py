from django.shortcuts import render

# Create your views here.
def patient(request):
    return render(request, 'patient/patient-records.html')