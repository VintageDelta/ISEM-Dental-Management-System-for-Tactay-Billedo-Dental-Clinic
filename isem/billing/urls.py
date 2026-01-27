from django.urls import path

from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.billing, name='list'),
    path('', views.billing, name='billing_view'),
    path('add/', views.billing_add, name='billing_add'),
    path('<int:pk>/', views.billing_detail, name='billing_detail'),
    path('<int:pk>/edit/', views.billing_edit, name='billing_edit'),
    path('<int:pk>/delete/', views.billing_delete, name='billing_delete'),
    path('search/', views.search_billing, name='search_billing'),

]