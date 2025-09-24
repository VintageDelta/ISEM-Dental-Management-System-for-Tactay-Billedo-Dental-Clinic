from django.urls import path

from . import views

app_name = 'userprofile'

urlpatterns = [
    path('sign-in/', views.RoleBasedLoginView.as_view(), name='signin'),
    path('sign-up/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('homepage/', views.homepage, name='homepage'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-staff/<int:user_id>/', views.approve_staff, name='approve_staff'),
    path('decline-staff/<int:user_id>/', views.decline_staff, name='decline_staff'), 
]