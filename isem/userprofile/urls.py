from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse_lazy

app_name = 'userprofile'

urlpatterns = [
    path('sign-in/', views.RoleBasedLoginView.as_view(), name='signin'),
    path('sign-up/', views.signup, name='signup'),
    path('patient_data/', views.patient_data, name='patient_data'),

    #Password Reset URLs
    #OTP-Based Password Reset URLs
    path('password-reset/', 
         views.ForgotPasswordView.as_view(), 
         name='password_reset'),
    
    path('password-reset/done/', 
         views.PasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    
    path('password-reset-confirm/', 
         views.PasswordResetConfirmOTPView.as_view(), 
         name='password_reset_confirm_otp'),
    
    path('password-reset/complete/', 
         views.PasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
    
    path('resend-otp/', 
         views.ResendOTPView.as_view(), 
         name='resend_otp'),

    
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('homepage/', views.homepage, name='homepage'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('delete-avatar/', views.delete_avatar, name='delete_avatar'),
    path('add-staff/', views.add_staff, name='add_staff'),
    path('add-user/', views.add_user, name='add_user'),
    path('admin/edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path("admin/dentist/create/", views.dentist_create, name="dentist_create"),
    path("admin/service/create/", views.service_create, name="service_create"),
    path("admin/service/search", views.search_services, name='search_services'),
    path("admin/dentist/delete/<int:pk>/", views.dentist_delete, name="dentist_delete"),
    path("admin/service/delete/<int:pk>/", views.service_delete, name="service_delete"),
    path("admin/dentist/edit/<int:pk>/", views.dentist_update, name="dentist_update"),
    path("admin/service/edit/<int:pk>/", views.service_update, name="service_update"),
    path("admin/branch/edit/<int:pk>/", views.branch_update, name="branch_update"),
]