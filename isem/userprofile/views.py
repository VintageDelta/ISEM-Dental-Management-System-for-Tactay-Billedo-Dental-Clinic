from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.views import LoginView as Loginview
from django.db import models
from patient.models import Patient
from appointment.models import Appointment
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views


class RoleBasedLoginView(Loginview):
    template_name = 'userprofile/sign-in.html'
    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return '/user/admin/dashboard/'
        elif user.is_staff:
            return '/dashboard/'
        else:
            return '/user/homepage/' 

@login_required
def patient_dashboard(request):
    user = request.user

    # Get patient profile
    patient = Patient.objects.filter(user=user).first()

    today = timezone.now().date()
    next_week = today + timedelta(days=7)

    # All appointments of this user
    appointments = Appointment.objects.filter(user=user)

    total_appointments = appointments.count()

    upcoming_appointments = appointments.filter(
        date__gte=today,
        status__in=["not_arrived", "arrived", "ongoing"]
    ).count()

    cancelled_appointments = appointments.filter(
        status="cancelled",
        date__gte=today - timedelta(days=7)
    ).count()

    # Next appointment
    next_appointment = appointments.filter(
        date__gte=today,
        status__in=["not_arrived", "arrived"]
    ).order_by("date", "time").first()

    context = {
        "patient": patient,
        "total_appointments": total_appointments,
        "upcoming_appointments": upcoming_appointments,
        "cancelled_appointments": cancelled_appointments,
        "next_appointment": next_appointment,
    }

    return render(request, "userprofile/homepage.html", context)

def signin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print("DEBUG - Username:", username)
        print("DEBUG - Password:", password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("dashboard:index")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'userprofile/sign-in.html')

def signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        terms = request.POST.get("terms")
        role = request.POST.get("role")

        if not terms:
            messages.error(request, "You must agree to the terms and conditions.") 
            return redirect("userprofile:signup")
        
        #password matching
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("userprofile:signup")
       
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("userprofile:signup")
    
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("userprofile:signup")
        
        #user creation role based
        if role == "patient":
            print("DEBUG: Creating patient user")
            user = User.objects.create_user(
                username=username, email=email, password=password1,
                first_name=first_name, last_name=last_name
            )
            patient_group, created = Group.objects.get_or_create(name='Patient')
            user.groups.add(patient_group)
            print("DEBUG: Creating Patient object")
            Patient.objects.create(
                user=user,
                name=f"{first_name} {last_name}",
                email=email,
                address="",
                telephone="",
                age=0,
                occupation="",
                is_guest=False,

                gender="",
                particular_condition="",
                allergy="",
                pregnancy_status="",
                medications="",
                abnormal_bleeding_history=""
            )
            print("DEBUG: Logging in user")
            login(request, user)
            print("DEBUG: About to redirect")
            messages.success(request, "Account created successfully. Please complete your patient data.")
            return redirect("userprofile:patient_data")

        elif role == "staff":
            user = User.objects.create_user(
                username=username, email=email, password=password1,
                first_name=first_name, last_name=last_name,
                is_active=False,   
                is_staff=False     
            )
            staff_group, created = Group.objects.get_or_create(name='Staff')
            user.groups.add(staff_group)
            messages.success(request,
                "Staff request submitted. An admin must approve your account before you can log in."
            )

        return redirect("userprofile:signin")

    return render(request, 'userprofile/sign-up.html')

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    pending_staff = User.objects.filter(is_staff=False, is_active=False)
    decline_staff = User.objects.filter(is_staff=False, is_active=False)
    return render(request, 'userprofile/admin/admin-dashboard.html',
                   {'pending_staff': pending_staff,
                    'all_users': User.objects.all(),})

def approve_staff(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = True
    user.is_staff = True
    user.save()
    messages.success(request, f"{user.username} has been approved as staff.")
    return redirect('userprofile:admin_dashboard')  

def decline_staff(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = False
    user.is_staff = False
    user.save()
    messages.success(request, f"{user.username} has been declined as staff.")
    return redirect('userprofile:admin_dashboard')



def profile(request):
    if not request.user.is_authenticated:
        return redirect("userprofile:signin")
    
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        user = request.user
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if user.username:
                user.username = user.username
        if email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, "Email already exists.")
                return redirect("userprofile:profile")
            user.email = email
        else:
                
                return redirect("userprofile:profile")
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("userprofile:profile")
    return render(request, 'userprofile/profile.html')

def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("userprofile:signin")

def is_patient(user):
    
    return hasattr(user, 'patient') or not user.is_staff

@login_required
def patient_data(request):
    patient = getattr(request.user, 'patient_patient', None)
 
    if not patient:
        print("DEBUG: No patient found, redirecting to homepage")
        return redirect('userprofile:homepage')
    
    if request.method == "POST":

        age = request.POST.get("age")
        if age:
            try:
                patient.age = int(age)
            except ValueError:
                    pass
        
        patient.gender = request.POST.get("gender") or getattr(patient, "gender", "")
        patient.occupation = request.POST.get("occupation") or patient.occupation
        patient.telephone = request.POST.get("telephone") or patient.telephone
        patient.address = request.POST.get("address") or patient.address

        patient.particular_condition = request.POST.get("particular_condition") or getattr(patient, "particular_condition", "")
        patient.allergy = request.POST.get("allergy") or getattr(patient, "allergy", "")
        patient.pregnancy_status = request.POST.get("pregnancy_status") or getattr(patient, "pregnancy_status", "")
        patient.medications = request.POST.get("medications") or getattr(patient, "medications", "")
        patient.abnormal_bleeding_history = request.POST.get("abnormal_bleeding_history") or getattr(patient, "abnormal_bleeding_history", "")

        patient.save()
        return redirect("userprofile:homepage")

    return render(request, 'userprofile/patient_data.html', {'patient': patient})

@login_required
def homepage(request):
    if request.user.is_superuser:
        return redirect('userprofile:admin_dashboard')
    elif request.user.is_staff:
        return redirect('dashboard:index')
    else:
        return patient_dashboard(request)
