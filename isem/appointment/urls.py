from django.urls import path

from . import views

app_name = 'appointment'

urlpatterns = [
    path('', views.appointment_page, name='list'),
    path("events/", views.events, name='events'),
   path("update-status/<int:appointment_id>/", views.update_status, name="update_status"),
]