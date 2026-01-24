from django.urls import path

from . import views

app_name = "patient"

urlpatterns = [
    path("", views.patient_records, name="list"),
    path("delete/<int:pk>/", views.delete_patient, name="delete"),
    path("update/", views.update_patient, name="update"),
    path("<int:pk>/", views.medical_history, name="medical_history"),
    path("<int:patient_id>/add_history/", views.add_medical_history, name="add_medical_history"),
    path("<int:pk>/financial_history/", views.medical_history, name="financial_history"),
    path("<int:patient_id>/add_financial_history/", views.add_financial_history, name="add_financial_history"),
    path("<int:patient_id>/odontogram/", views.odontogram, name="odontogram"),
    path("<int:patient_id>/add_odontogram/", views.add_odontogram, name="add_odontogram"),
    path("<int:patient_id>/odontogram_history/", views.odontogram_history, name="odontogram_history"),
    path("<int:patient_id>/update_odontogram/", views.update_odontogram, name="update_odontogram"),
    path("<int:patient_id>/odontogram/history/<int:tooth_number>/", views.odontogram_history, name="odontogram_tooth_history"),
    path('<int:xray_id>/delete-xray/', views.delete_xray, name='delete_xray'),

]