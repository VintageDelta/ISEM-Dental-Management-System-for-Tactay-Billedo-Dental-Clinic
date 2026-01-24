"""
URL configuration for isem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from landingpage import views as landing_views
from django.conf import settings
from django.conf.urls.static import static

from core.views import index
urlpatterns = [
    path('', landing_views.landing, name='landing'),
    path("", index, name="index"),
    path("dashboard/", include('dashboard.urls')),
    path("dashboard/patient/", include('patient.urls')),
    path("dashboard/appointment/", include('appointment.urls')),
    path("dashboard/inventory/", include('inventory.urls')),
    path("dashboard/billing/", include('billing.urls')),
    path("user/",include('userprofile.urls')),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)