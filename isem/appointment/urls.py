from django.urls import path

from . import views

app_name = 'appointment'

urlpatterns = [
    path('', views.appointment_record, name='list'),
    path("events/", views.appointment_events, name='events'),
    path('', views.Appointment, name='list'),
]