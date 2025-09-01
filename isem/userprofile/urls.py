from django.urls import path

from . import views

app_name = 'userprofile'

urlpatterns = [
    path('sign-in/', views.signin, name='signin'),
    path('sign-up/', views.signup, name='signup'),
]