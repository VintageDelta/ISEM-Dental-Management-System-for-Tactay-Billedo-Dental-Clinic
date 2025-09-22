import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.views import LoginView as Loginview

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
        
def admin_dashboard(request):
    return render(request, 'userprofile/admin/admin-dashboard.html')

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
        
        #user_creation
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        messages.success(request, "Account created successfully. Please sign in.")
        return redirect("userprofile:signin")
    
    return render(request, 'userprofile/sign-up.html')

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