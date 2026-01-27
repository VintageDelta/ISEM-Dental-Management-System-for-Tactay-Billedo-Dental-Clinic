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
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='userprofile/password_reset.html',
                                                                 email_template_name='userprofile/password_reset_email.html',
                                                                 subject_template_name='userprofile/password_reset_subject.txt',
                                                                 success_url= reverse_lazy('userprofile:password_reset_done')), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='userprofile/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='userprofile/password_reset_confirm.html',
                                                                                                 success_url=reverse_lazy('userprofile:password_reset_complete')), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='userprofile/password_reset_complete.html'), name='password_reset_complete'), 

    
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('homepage/', views.homepage, name='homepage'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('delete-avatar/', views.delete_avatar, name='delete_avatar'),
    path('add-staff/', views.add_staff, name='add_staff'),
    path('add-user/', views.add_user, name='add_user'),


]