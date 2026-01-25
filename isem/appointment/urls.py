from django.urls import path
from . import views


app_name = 'appointment'

urlpatterns = [
    path('', views.appointment_page, name='list'),
    path("appointment/", views.appointment_page, name="appointment_page"),
    path("events/", views.events, name='events'),
    path("update-status/<int:appointment_id>/", views.update_status, name="update_status"),
    path("get-booked-times/", views.get_booked_times, name="get_booked_times"),
    path("create-followup/", views.create_followup, name="create_followup"),
    path("reschedule_appointment/<int:appointment_id>/", views.reschedule_appointment, name="reschedule_appointment"),
    path("get-appointment-details/<int:appointment_id>/", views.get_appointment_details, name="get_appointment_details"),
    path("precompute-slot/", views.precompute_appointment_slot, name="precompute_slot"),
    # emailing 
    path(
        "notify-email/<int:appointment_id>/",
        views.notify_patient_email,
        name="notify_patient_email",
    ),
]