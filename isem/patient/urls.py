from django.urls import path

from . import views

app_name = "patient"

urlpatterns = [
    path("", views.patient_records, name="list"),  # now it matches your view
]