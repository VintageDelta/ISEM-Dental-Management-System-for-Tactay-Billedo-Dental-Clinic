from django.urls import path

from . import views

app_name = "patient"

urlpatterns = [
    path("", views.patient_records, name="list"),
    path("delete/<int:pk>/", views.delete_patient, name="delete"),
    path("update/", views.update_patient, name="update"),
]