from django.urls import path

from . import views

app_name = "patient"

urlpatterns = [
    path("", views.patient_records, name="list"),
    path("delete/<int:pk>/", views.delete_patient, name="delete"),
    path("update/", views.update_patient, name="update"),
    path("<int:pk>/", views.medical_history, name="medical_history"),
    path("<int:patient_id>/add_history/", views.add_medical_history, name="add_medical_history"),
    path("<int:patient_id>/financial_history/", views.financial_history, name="financial_history"),
]