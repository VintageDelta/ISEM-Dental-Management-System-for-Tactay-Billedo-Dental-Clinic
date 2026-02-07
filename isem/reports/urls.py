from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_dashboard, name="index"),
    path("export_reports_dashboard", views.export_reports_dashboard, name="export")
]