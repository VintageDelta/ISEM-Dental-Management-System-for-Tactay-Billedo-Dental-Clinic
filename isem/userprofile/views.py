from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.views import LoginView as Loginview
from django.db import models

# Create your views here.
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
            user = User.objects.create_user(
                username=username, email=email, password=password1,
                first_name=first_name, last_name=last_name
            )
            patient_group = Group.objects.get(name='Patient')
            user.groups.add(patient_group)
            messages.success(request, "Account created successfully. Please sign in.")

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
                   {'pending_staff': pending_staff})

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
    return render(request, 'userprofile/profile.html')

def logout(request):
    messages.success(request, "You have been logged out.")
    return redirect("userprofile:signin")

def is_patient(user):
    
    return hasattr(user, 'patient') or not user.is_staff

# @login_required
# @user_passes_test(is_patient)
def homepage(request):
    if request.user.is_superuser:
        return redirect('userprofile:admin_dashboard')
    elif request.user.is_staff:
        return redirect('dashboard:index')
    else:
        return render(request, 'userprofile/homepage.html')
    

            